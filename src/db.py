from firebase_admin import credentials, firestore, initialize_app
from typing import List, Optional, Dict, Any, Type, TypeVar, Generic
from pydantic import BaseModel
import os
import json
from datetime import datetime
from google.cloud.firestore_v1.base_query import FieldFilter

# Type variable for generic database operations
T = TypeVar('T', bound=BaseModel)

class FirestoreDB:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirestoreDB, cls).__new__(cls)
            # Initialize app with your Google service credentials
            # For local development, set GOOGLE_CREDENTIALS environment variable
            # or use credentials from environment
            if os.getenv('FIREBASE_CONFIG'):
                # Running in Cloud Functions
                firebase_config = json.loads(os.getenv('FIREBASE_CONFIG'))
                initialize_app(options=firebase_config)
            else:
                # Local development
                cred_path = os.getenv('GOOGLE_CREDENTIALS')
                if cred_path:
                    cred = credentials.Certificate(cred_path)
                    initialize_app(cred)
                else:
                    initialize_app()
            
            cls._instance.db = firestore.client()
        return cls._instance
    
    def _convert_to_dict(self, obj: BaseModel) -> Dict[str, Any]:
        """Convert Pydantic model to dict for Firestore."""
        data = obj.model_dump()
        
        # Convert datetime objects to ISO format strings
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
                
        return data
    
    def _convert_from_dict(self, data: Dict[str, Any], model_class: Type[T]) -> T:
        """Convert Firestore dict to Pydantic model."""
        return model_class.model_validate(data)
    
    async def create(self, collection: str, document_id: str, data: BaseModel) -> str:
        """Create a document in Firestore."""
        doc_ref = self.db.collection(collection).document(document_id)
        doc_ref.set(self._convert_to_dict(data))
        return document_id
    
    async def get(self, collection: str, document_id: str, model_class: Type[T]) -> Optional[T]:
        """Get a document from Firestore."""
        doc_ref = self.db.collection(collection).document(document_id)
        doc = doc_ref.get()
        
        if doc.exists:
            return self._convert_from_dict(doc.to_dict(), model_class)
        return None
    
    async def update(self, collection: str, document_id: str, data: Dict[str, Any]) -> None:
        """Update a document in Firestore."""
        doc_ref = self.db.collection(collection).document(document_id)
        doc_ref.update(data)
    
    async def delete(self, collection: str, document_id: str) -> None:
        """Delete a document from Firestore."""
        doc_ref = self.db.collection(collection).document(document_id)
        doc_ref.delete()
    
    async def list(self, collection: str, model_class: Type[T], 
                  filters: Optional[List[tuple]] = None, 
                  order_by: Optional[str] = None,
                  limit: Optional[int] = None) -> List[T]:
        """
        List documents from a collection with optional filtering.
        
        Args:
            collection: The collection name
            model_class: The Pydantic model class to convert the results to
            filters: List of filters in format (field, operator, value)
            order_by: Field to order results by
            limit: Maximum number of results to return
            
        Returns:
            List of documents as Pydantic models
        """
        query = self.db.collection(collection)
        
        # Apply filters
        if filters:
            for field, op, value in filters:
                query = query.where(filter=FieldFilter(field, op, value))
        
        # Apply ordering
        if order_by:
            query = query.order_by(order_by)
            
        # Apply limit
        if limit:
            query = query.limit(limit)
            
        # Execute query
        docs = query.stream()
        
        # Convert to Pydantic models
        return [self._convert_from_dict(doc.to_dict(), model_class) for doc in docs] 