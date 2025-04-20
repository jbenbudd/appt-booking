import functions_framework
from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel, EmailStr
import uvicorn
import uuid
from typing import List, Optional
import logging

from src.models import Provider, Availability, WeeklySchedule
from src.db import FirestoreDB

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
db = FirestoreDB()

PROVIDER_COLLECTION = "providers"
AVAILABILITY_COLLECTION = "availability"

class ProviderCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    specialization: Optional[str] = None
    appointment_types: List[str]  # List of appointment type IDs

class ProviderUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    specialization: Optional[str] = None
    appointment_types: Optional[List[str]] = None
    active: Optional[bool] = None

@app.post("/providers", response_model=Provider)
async def create_provider(provider: ProviderCreate):
    """Create a new service provider."""
    provider_id = str(uuid.uuid4())
    new_provider = Provider(
        id=provider_id,
        **provider.model_dump(),
        active=True
    )
    
    await db.create(PROVIDER_COLLECTION, provider_id, new_provider)
    
    # Create default empty availability
    default_availability = Availability(
        provider_id=provider_id,
        weekly_schedule=WeeklySchedule()
    )
    await db.create(AVAILABILITY_COLLECTION, provider_id, default_availability)
    
    return new_provider

@app.get("/providers", response_model=List[Provider])
async def list_providers(active_only: bool = Query(False)):
    """List all service providers, optionally filtering by active status."""
    filters = None
    if active_only:
        filters = [("active", "==", True)]
    
    return await db.list(PROVIDER_COLLECTION, Provider, filters=filters)

@app.get("/providers/{provider_id}", response_model=Provider)
async def get_provider(provider_id: str):
    """Get a service provider by ID."""
    provider = await db.get(PROVIDER_COLLECTION, provider_id, Provider)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider

@app.put("/providers/{provider_id}", response_model=Provider)
async def update_provider(provider_id: str, update_data: ProviderUpdate):
    """Update an existing service provider."""
    # First get the existing provider
    provider = await db.get(PROVIDER_COLLECTION, provider_id, Provider)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    # Update with non-None values
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    
    # Update in database
    await db.update(PROVIDER_COLLECTION, provider_id, update_dict)
    
    # Return updated object
    return await db.get(PROVIDER_COLLECTION, provider_id, Provider)

@app.delete("/providers/{provider_id}", status_code=204)
async def delete_provider(provider_id: str):
    """Delete a service provider (soft delete by setting active=False)."""
    provider = await db.get(PROVIDER_COLLECTION, provider_id, Provider)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    # Soft delete by setting active=False
    await db.update(PROVIDER_COLLECTION, provider_id, {"active": False})
    return {"message": "Provider deactivated"}

@app.get("/providers/{provider_id}/availability", response_model=Availability)
async def get_provider_availability(provider_id: str):
    """Get a provider's availability schedule."""
    # First check if provider exists
    provider = await db.get(PROVIDER_COLLECTION, provider_id, Provider)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    # Get availability
    availability = await db.get(AVAILABILITY_COLLECTION, provider_id, Availability)
    if not availability:
        raise HTTPException(status_code=404, detail="Availability not found")
    
    return availability

@app.put("/providers/{provider_id}/availability", response_model=Availability)
async def update_provider_availability(provider_id: str, availability: Availability):
    """Update a provider's availability schedule."""
    # First check if provider exists
    provider = await db.get(PROVIDER_COLLECTION, provider_id, Provider)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    # Ensure provider_id in availability matches path parameter
    if availability.provider_id != provider_id:
        availability.provider_id = provider_id
    
    # Update availability
    await db.update(AVAILABILITY_COLLECTION, provider_id, availability.model_dump())
    
    # Return updated availability
    return await db.get(AVAILABILITY_COLLECTION, provider_id, Availability)

@functions_framework.http
def providers_service(request):
    """Cloud Function entry point."""
    try:
        logger.info("Providers Service: Received request")
        # For Cloud Functions Gen 2, the Flask request object is passed directly
        # We need to convert it to WSGI environ format for FastAPI
        asgi_app = app 
        response = functions_framework.flask_to_function(asgi_app)(request)
        logger.info(f"Providers Service: Processed successfully with status {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Providers Service ERROR: {str(e)}", exc_info=True)
        # Return a formatted error response
        import traceback
        error_details = {
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        import json
        from flask import Response
        return Response(
            response=json.dumps(error_details),
            status=500,
            mimetype="application/json"
        ) 