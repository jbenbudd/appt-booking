from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime, time
from enum import Enum


class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class AppointmentType(BaseModel):
    id: str
    name: str
    description: str
    duration_minutes: int
    price: float
    color: Optional[str] = None
    

class Provider(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    specialization: Optional[str] = None
    appointment_types: List[str]  # List of appointment type IDs
    active: bool = True


class WeeklySchedule(BaseModel):
    monday: Optional[List[Dict[str, time]]] = None  # List of {start: time, end: time}
    tuesday: Optional[List[Dict[str, time]]] = None
    wednesday: Optional[List[Dict[str, time]]] = None
    thursday: Optional[List[Dict[str, time]]] = None
    friday: Optional[List[Dict[str, time]]] = None
    saturday: Optional[List[Dict[str, time]]] = None
    sunday: Optional[List[Dict[str, time]]] = None


class Availability(BaseModel):
    provider_id: str
    weekly_schedule: WeeklySchedule
    exceptions: Optional[Dict[str, List[Dict[str, time]]]] = None  # Special dates with different hours
    unavailable_dates: Optional[List[datetime]] = None  # Dates when provider is not available


class Appointment(BaseModel):
    id: str
    provider_id: str
    customer_id: str
    appointment_type_id: str
    start_time: datetime
    end_time: datetime
    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Customer(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now) 