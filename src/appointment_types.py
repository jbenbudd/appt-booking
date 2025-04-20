import functions_framework
from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel, Field
import uvicorn
import uuid
from typing import List, Optional
import logging

from src.models import AppointmentType
from src.db import FirestoreDB

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
db = FirestoreDB()

COLLECTION = "appointment_types"

class AppointmentTypeCreate(BaseModel):
    name: str
    description: str
    duration_minutes: int
    price: float
    color: Optional[str] = None

class AppointmentTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    price: Optional[float] = None
    color: Optional[str] = None

@app.post("/appointment-types", response_model=AppointmentType)
async def create_appointment_type(appointment_type: AppointmentTypeCreate):
    """Create a new appointment type."""
    type_id = str(uuid.uuid4())
    new_type = AppointmentType(
        id=type_id,
        **appointment_type.model_dump()
    )
    
    await db.create(COLLECTION, type_id, new_type)
    return new_type

@app.get("/appointment-types", response_model=List[AppointmentType])
async def list_appointment_types():
    """List all appointment types."""
    return await db.list(COLLECTION, AppointmentType)

@app.get("/appointment-types/{type_id}", response_model=AppointmentType)
async def get_appointment_type(type_id: str):
    """Get an appointment type by ID."""
    appointment_type = await db.get(COLLECTION, type_id, AppointmentType)
    if not appointment_type:
        raise HTTPException(status_code=404, detail="Appointment type not found")
    return appointment_type

@app.put("/appointment-types/{type_id}", response_model=AppointmentType)
async def update_appointment_type(type_id: str, update_data: AppointmentTypeUpdate):
    """Update an existing appointment type."""
    # First get the existing appointment type
    appointment_type = await db.get(COLLECTION, type_id, AppointmentType)
    if not appointment_type:
        raise HTTPException(status_code=404, detail="Appointment type not found")
    
    # Update with non-None values
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    
    # Update in database
    await db.update(COLLECTION, type_id, update_dict)
    
    # Return updated object
    return await db.get(COLLECTION, type_id, AppointmentType)

@app.delete("/appointment-types/{type_id}", status_code=204)
async def delete_appointment_type(type_id: str):
    """Delete an appointment type."""
    appointment_type = await db.get(COLLECTION, type_id, AppointmentType)
    if not appointment_type:
        raise HTTPException(status_code=404, detail="Appointment type not found")
    
    await db.delete(COLLECTION, type_id)
    return {"message": "Appointment type deleted"}

@functions_framework.http
def appointment_types_service(request):
    """Cloud Function entry point."""
    try:
        logger.info("Appointment Types Service: Received request")
        # For Cloud Functions Gen 2, the Flask request object is passed directly
        # We need to convert it to WSGI environ format for FastAPI
        asgi_app = app 
        response = functions_framework.flask_to_function(asgi_app)(request)
        logger.info(f"Appointment Types Service: Processed successfully with status {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Appointment Types Service ERROR: {str(e)}", exc_info=True)
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