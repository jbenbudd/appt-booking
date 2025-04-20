import functions_framework
from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel
import uvicorn
import uuid
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import logging

from src.models import Appointment, AppointmentStatus, AppointmentType, Provider, Availability, Customer
from src.db import FirestoreDB

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
db = FirestoreDB()

APPOINTMENT_COLLECTION = "appointments"
PROVIDER_COLLECTION = "providers"
APPOINTMENT_TYPE_COLLECTION = "appointment_types"
AVAILABILITY_COLLECTION = "availability"
CUSTOMER_COLLECTION = "customers"

class AppointmentCreate(BaseModel):
    provider_id: str
    customer_id: str
    appointment_type_id: str
    start_time: datetime
    notes: Optional[str] = None

class AppointmentUpdate(BaseModel):
    start_time: Optional[datetime] = None
    status: Optional[AppointmentStatus] = None
    notes: Optional[str] = None

class AvailableSlot(BaseModel):
    provider_id: str
    provider_name: str
    start_time: datetime
    end_time: datetime

@app.post("/appointments", response_model=Appointment)
async def create_appointment(appointment: AppointmentCreate):
    """Create a new appointment."""
    # Check if provider exists
    provider = await db.get(PROVIDER_COLLECTION, appointment.provider_id, Provider)
    if not provider or not provider.active:
        raise HTTPException(status_code=404, detail="Provider not found or inactive")
    
    # Check if appointment type exists
    appt_type = await db.get(APPOINTMENT_TYPE_COLLECTION, appointment.appointment_type_id, AppointmentType)
    if not appt_type:
        raise HTTPException(status_code=404, detail="Appointment type not found")
    
    # Check if customer exists
    customer = await db.get(CUSTOMER_COLLECTION, appointment.customer_id, Customer)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Check if provider supports this appointment type
    if appointment.appointment_type_id not in provider.appointment_types:
        raise HTTPException(
            status_code=400, 
            detail="This provider does not offer this appointment type"
        )
    
    # Calculate end time based on appointment type duration
    end_time = appointment.start_time + timedelta(minutes=appt_type.duration_minutes)
    
    # Check if provider is available at this time
    is_available = await check_provider_availability(
        appointment.provider_id, 
        appointment.start_time, 
        end_time
    )
    
    if not is_available:
        raise HTTPException(
            status_code=400,
            detail="Provider is not available at this time"
        )
    
    # Create appointment
    appointment_id = str(uuid.uuid4())
    new_appointment = Appointment(
        id=appointment_id,
        provider_id=appointment.provider_id,
        customer_id=appointment.customer_id,
        appointment_type_id=appointment.appointment_type_id,
        start_time=appointment.start_time,
        end_time=end_time,
        status=AppointmentStatus.SCHEDULED,
        notes=appointment.notes,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    await db.create(APPOINTMENT_COLLECTION, appointment_id, new_appointment)
    return new_appointment

@app.get("/appointments", response_model=List[Appointment])
async def list_appointments(
    provider_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    status: Optional[AppointmentStatus] = None
):
    """List appointments with optional filtering."""
    filters = []
    
    if provider_id:
        filters.append(("provider_id", "==", provider_id))
    
    if customer_id:
        filters.append(("customer_id", "==", customer_id))
    
    if start_date:
        filters.append(("start_time", ">=", start_date.isoformat()))
    
    if end_date:
        filters.append(("start_time", "<=", end_date.isoformat()))
    
    if status:
        filters.append(("status", "==", status.value))
    
    filters = filters if filters else None
    return await db.list(APPOINTMENT_COLLECTION, Appointment, filters=filters, order_by="start_time")

@app.get("/appointments/{appointment_id}", response_model=Appointment)
async def get_appointment(appointment_id: str):
    """Get an appointment by ID."""
    appointment = await db.get(APPOINTMENT_COLLECTION, appointment_id, Appointment)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment

@app.put("/appointments/{appointment_id}", response_model=Appointment)
async def update_appointment(appointment_id: str, update_data: AppointmentUpdate):
    """Update an existing appointment."""
    # First get the existing appointment
    appointment = await db.get(APPOINTMENT_COLLECTION, appointment_id, Appointment)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Handle start_time update - need to recalculate end_time
    if update_data.start_time is not None:
        appt_type = await db.get(
            APPOINTMENT_TYPE_COLLECTION, 
            appointment.appointment_type_id, 
            AppointmentType
        )
        
        new_end_time = update_data.start_time + timedelta(minutes=appt_type.duration_minutes)
        
        # Check if provider is available at new time
        is_available = await check_provider_availability(
            appointment.provider_id, 
            update_data.start_time, 
            new_end_time,
            exclude_appointment_id=appointment_id
        )
        
        if not is_available:
            raise HTTPException(
                status_code=400,
                detail="Provider is not available at this time"
            )
        
        # Update both start and end time
        update_dict = {
            "start_time": update_data.start_time.isoformat(),
            "end_time": new_end_time.isoformat()
        }
    else:
        update_dict = {}
    
    # Add other fields to update
    update_dict.update({
        k: v.value if isinstance(v, AppointmentStatus) else v 
        for k, v in update_data.model_dump().items() 
        if v is not None and k != "start_time"  # start_time already handled
    })
    
    # Always update the updated_at timestamp
    update_dict["updated_at"] = datetime.now().isoformat()
    
    # Update in database
    await db.update(APPOINTMENT_COLLECTION, appointment_id, update_dict)
    
    # Return updated object
    return await db.get(APPOINTMENT_COLLECTION, appointment_id, Appointment)

@app.delete("/appointments/{appointment_id}", status_code=204)
async def cancel_appointment(appointment_id: str):
    """Cancel an appointment."""
    appointment = await db.get(APPOINTMENT_COLLECTION, appointment_id, Appointment)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Cancel appointment by setting status to CANCELLED
    await db.update(APPOINTMENT_COLLECTION, appointment_id, {
        "status": AppointmentStatus.CANCELLED.value,
        "updated_at": datetime.now().isoformat()
    })
    return {"message": "Appointment cancelled"}

@app.get("/available-slots", response_model=List[AvailableSlot])
async def get_available_slots(
    provider_id: Optional[str] = None,
    appointment_type_id: Optional[str] = None,
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
):
    """Find available appointment slots based on provider and/or appointment type."""
    # If specific appointment type, get its duration
    appointment_duration = 30  # Default 30 minutes
    if appointment_type_id:
        appt_type = await db.get(APPOINTMENT_TYPE_COLLECTION, appointment_type_id, AppointmentType)
        if not appt_type:
            raise HTTPException(status_code=404, detail="Appointment type not found")
        appointment_duration = appt_type.duration_minutes
    
    # Get relevant providers
    providers_filter = []
    if provider_id:
        providers_filter.append(("id", "==", provider_id))
    else:
        providers_filter.append(("active", "==", True))
        
        if appointment_type_id:
            # This is a simplification - Firestore array-contains can only check for one value
            # In a real implementation, you might need to handle this differently
            providers_filter.append(("appointment_types", "array-contains", appointment_type_id))
    
    providers = await db.list(PROVIDER_COLLECTION, Provider, filters=providers_filter)
    
    if not providers:
        return []
    
    available_slots = []
    
    # For each provider, find their available slots
    for provider in providers:
        provider_slots = await find_available_slots_for_provider(
            provider.id,
            provider.name,
            start_date,
            end_date,
            appointment_duration
        )
        available_slots.extend(provider_slots)
    
    # Sort slots by start time
    available_slots.sort(key=lambda slot: slot.start_time)
    
    return available_slots

async def check_provider_availability(
    provider_id: str, 
    start_time: datetime, 
    end_time: datetime,
    exclude_appointment_id: Optional[str] = None
) -> bool:
    """Check if a provider is available for a specific time slot."""
    # 1. Check provider's weekly schedule
    availability = await db.get(AVAILABILITY_COLLECTION, provider_id, Availability)
    
    if not availability:
        return False
    
    # Check day of week
    day_of_week = start_time.strftime("%A").lower()
    day_schedule = getattr(availability.weekly_schedule, day_of_week)
    
    if not day_schedule:
        return False  # Provider doesn't work on this day
    
    # Check if the appointment falls within provider's working hours
    appointment_in_working_hours = False
    start_time_time = start_time.time()
    end_time_time = end_time.time()
    
    for time_slot in day_schedule:
        if (start_time_time >= time_slot.get('start') and 
            end_time_time <= time_slot.get('end')):
            appointment_in_working_hours = True
            break
    
    if not appointment_in_working_hours:
        return False
    
    # 2. Check for unavailable dates
    if availability.unavailable_dates:
        appointment_date = start_time.date()
        for unavailable_date in availability.unavailable_dates:
            if appointment_date == unavailable_date.date():
                return False
    
    # 3. Check for existing appointments
    # Get all appointments for this provider on this day
    appointment_date = start_time.date()
    next_day = appointment_date + timedelta(days=1)
    
    filters = [
        ("provider_id", "==", provider_id),
        ("start_time", ">=", appointment_date.isoformat()),
        ("start_time", "<", next_day.isoformat()),
        ("status", "==", AppointmentStatus.SCHEDULED.value)
    ]
    
    existing_appointments = await db.list(APPOINTMENT_COLLECTION, Appointment, filters=filters)
    
    # Check for overlapping appointments
    for appt in existing_appointments:
        # Skip the appointment we're updating
        if exclude_appointment_id and appt.id == exclude_appointment_id:
            continue
            
        # Check for overlap
        if (start_time < appt.end_time and end_time > appt.start_time):
            return False
    
    return True

async def find_available_slots_for_provider(
    provider_id: str,
    provider_name: str,
    start_date: datetime,
    end_date: datetime,
    appointment_duration: int
) -> List[AvailableSlot]:
    """Find available time slots for a specific provider."""
    # This is a simplified implementation that generates slots
    # In a real implementation, this would need to be more sophisticated
    
    available_slots = []
    current_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Get provider's availability
    availability = await db.get(AVAILABILITY_COLLECTION, provider_id, Availability)
    if not availability:
        return []
    
    # Get all scheduled appointments for this provider in the date range
    filters = [
        ("provider_id", "==", provider_id),
        ("start_time", ">=", start_date.isoformat()),
        ("start_time", "<", end_date.isoformat()),
        ("status", "==", AppointmentStatus.SCHEDULED.value)
    ]
    
    booked_appointments = await db.list(APPOINTMENT_COLLECTION, Appointment, filters=filters)
    
    # Check each day in the range
    while current_date < end_date:
        day_of_week = current_date.strftime("%A").lower()
        day_schedule = getattr(availability.weekly_schedule, day_of_week)
        
        if day_schedule:  # If provider works on this day
            for time_slot in day_schedule:
                # Generate appointment slots within working hours
                slot_start = current_date.replace(
                    hour=time_slot.get('start').hour,
                    minute=time_slot.get('start').minute
                )
                slot_end = current_date.replace(
                    hour=time_slot.get('end').hour, 
                    minute=time_slot.get('end').minute
                )
                
                # Generate slots at 30-minute intervals (or based on appointment duration)
                interval_minutes = min(appointment_duration, 30)  # Use smaller intervals for shorter appointments
                current_slot_start = slot_start
                
                while current_slot_start + timedelta(minutes=appointment_duration) <= slot_end:
                    current_slot_end = current_slot_start + timedelta(minutes=appointment_duration)
                    
                    # Check if this slot overlaps with any booked appointment
                    is_available = True
                    for appt in booked_appointments:
                        if (current_slot_start < appt.end_time and 
                            current_slot_end > appt.start_time):
                            is_available = False
                            break
                    
                    if is_available:
                        available_slots.append(AvailableSlot(
                            provider_id=provider_id,
                            provider_name=provider_name,
                            start_time=current_slot_start,
                            end_time=current_slot_end
                        ))
                    
                    # Move to next interval
                    current_slot_start += timedelta(minutes=interval_minutes)
        
        # Move to next day
        current_date += timedelta(days=1)
    
    return available_slots

@functions_framework.http
def appointments_service(request):
    """Cloud Function entry point."""
    # For Cloud Functions Gen 2, the Flask request object is passed directly
    # We need to convert it to WSGI environ format for FastAPI
    asgi_app = app 
    return functions_framework.flask_to_function(asgi_app)(request) 