from firebase_admin import credentials, firestore, initialize_app, get_app
from typing import List, Optional, Dict, Any, Type, TypeVar, Generic
from pydantic import BaseModel
import os
import json
from datetime import datetime
from google.cloud.firestore_v1.base_query import FieldFilter
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type variable for generic database operations
T = TypeVar('T', bound=BaseModel)

class FirestoreDB:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirestoreDB, cls).__new__(cls)
            
            # Different initialization methods based on environment
            try:
                # First try to get existing app
                app = get_app()
                logger.info("Firebase app already initialized")
            except ValueError:
                # App doesn't exist, need to initialize
                project_id = os.environ.get('FIREBASE_PROJECT_ID')
                logger.info(f"Initializing Firebase with project ID: {project_id}")
                
                try:
                    if os.environ.get('FIREBASE_CONFIG'):
                        # Running in Cloud Functions older method
                        firebase_config = json.loads(os.environ.get('FIREBASE_CONFIG'))
                        logger.info(f"Initializing with FIREBASE_CONFIG: {firebase_config}")
                        initialize_app(options=firebase_config)
                    elif project_id:
                        # Initialize with project ID
                        logger.info(f"Initializing with project ID only: {project_id}")
                        initialize_app(options={'projectId': project_id})
                    else:
                        # Local development - use credentials file
                        cred_path = os.environ.get('GOOGLE_CREDENTIALS')
                        if cred_path:
                            logger.info(f"Initializing with credentials file: {cred_path}")
                            cred = credentials.Certificate(cred_path)
                            initialize_app(cred)
                        else:
                            # Try default initialization 
                            logger.info("Attempting default initialization with no params")
                            initialize_app()
                    logger.info("Firebase initialization successful")
                except Exception as e:
                    logger.error(f"Firebase initialization error: {str(e)}")
                    raise
            
            # Create Firestore client
            try:
                cls._instance.db = firestore.client()
                logger.info("Firestore client created successfully")
            except Exception as e:
                logger.error(f"Error creating Firestore client: {str(e)}")
                raise
            
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
    
    async def create_indexes(self):
        """Create necessary indexes for the application."""
        try:
            logger.info("Creating Firestore indexes for appointments...")
            
            # Create a composite index for appointments by provider, status, and start_time
            collection_ref = self.db.collection("appointments")
            
            # Unfortunately, we can't directly create indexes via API in client mode
            # We need to use the Firestore Admin API which requires additional permissions
            # For now, log the indexes needed so they can be created manually
            
            logger.info("Firestore indexes needed:")
            logger.info("1. Collection: appointments, Fields: provider_id (ASC), status (ASC), start_time (ASC)")
            logger.info("2. Collection: appointments, Fields: customer_id (ASC), status (ASC), start_time (ASC)")
            
            # An alternative is to simply attempt a few queries that would create these indexes
            # This works because Firestore automatically suggests index creation
            try:
                # This will trigger index creation suggestions if indexes don't exist
                # Provider + status + start_time index
                collection_ref.where(filter=FieldFilter("provider_id", "==", "dummy"))\
                              .where(filter=FieldFilter("status", "==", "scheduled"))\
                              .order_by("start_time").limit(1).get()
                
                # Customer + status + start_time index
                collection_ref.where(filter=FieldFilter("customer_id", "==", "dummy"))\
                              .where(filter=FieldFilter("status", "==", "scheduled"))\
                              .order_by("start_time").limit(1).get()
                
                logger.info("Index creation triggered successfully")
            except Exception as e:
                logger.warning(f"Index creation attempt resulted in: {str(e)}")
                logger.info("Use the Firestore console to create these indexes manually")
                
        except Exception as e:
            logger.error(f"Error setting up indexes: {str(e)}") 