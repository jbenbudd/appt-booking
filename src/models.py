from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime, time
from enum import Enum

def time_to_str(t: time) -> str:
    """Convert a time object to string in HH:MM:SS format."""
    return t.strftime("%H:%M:%S") if t else None

def str_to_time(s: str) -> time:
    """Convert a string in HH:MM:SS format to a time object."""
    if not s:
        return None
    if isinstance(s, time):
        return s
    try:
        hour, minute, second = map(int, s.split(':'))
        return time(hour, minute, second)
    except:
        # Try just hour and minute
        try:
            hour, minute = map(int, s.split(':'))
            return time(hour, minute)
        except:
            return None

class TimeSlot(BaseModel):
    start: str
    end: str
    
    def get_start_time(self) -> time:
        return str_to_time(self.start)
    
    def get_end_time(self) -> time:
        return str_to_time(self.end)

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
    monday: Optional[List[TimeSlot]] = None
    tuesday: Optional[List[TimeSlot]] = None
    wednesday: Optional[List[TimeSlot]] = None
    thursday: Optional[List[TimeSlot]] = None
    friday: Optional[List[TimeSlot]] = None
    saturday: Optional[List[TimeSlot]] = None
    sunday: Optional[List[TimeSlot]] = None


class Availability(BaseModel):
    provider_id: str
    weekly_schedule: WeeklySchedule
    exceptions: Optional[Dict[str, List[TimeSlot]]] = None  # Special dates with different hours
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