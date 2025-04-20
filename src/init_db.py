#!/usr/bin/env python3
"""
Initialize the Firestore database with sample data for development/testing purposes.
"""

import asyncio
import uuid
from datetime import datetime, time, timedelta
from firebase_admin import credentials, initialize_app
import os

from src.db import FirestoreDB
from src.models import (
    AppointmentType, 
    Provider, 
    Availability, 
    WeeklySchedule, 
    Customer,
    Appointment,
    AppointmentStatus
)

# Initialize database
db = FirestoreDB()

async def create_appointment_types():
    """Create sample appointment types."""
    appointment_types = [
        AppointmentType(
            id=str(uuid.uuid4()),
            name="Regular Checkup",
            description="Standard medical checkup appointment",
            duration_minutes=30,
            price=50.0,
            color="#4CAF50"  # Green
        ),
        AppointmentType(
            id=str(uuid.uuid4()),
            name="Consultation",
            description="Medical consultation for specific concerns",
            duration_minutes=45,
            price=75.0,
            color="#2196F3"  # Blue
        ),
        AppointmentType(
            id=str(uuid.uuid4()),
            name="Urgent Care",
            description="Immediate care for non-emergency situations",
            duration_minutes=60,
            price=100.0,
            color="#F44336"  # Red
        ),
        AppointmentType(
            id=str(uuid.uuid4()),
            name="Follow-up",
            description="Follow-up appointment after treatment",
            duration_minutes=20,
            price=40.0,
            color="#FF9800"  # Orange
        )
    ]
    
    # Store appointment type IDs for later use
    appointment_type_ids = []
    
    for appt_type in appointment_types:
        await db.create("appointment_types", appt_type.id, appt_type)
        appointment_type_ids.append(appt_type.id)
        print(f"Created appointment type: {appt_type.name}")
    
    return appointment_type_ids

async def create_providers(appointment_type_ids):
    """Create sample providers."""
    providers = [
        Provider(
            id=str(uuid.uuid4()),
            name="Dr. Jane Smith",
            email="jane.smith@example.com",
            phone="555-123-4567",
            specialization="General Practitioner",
            appointment_types=appointment_type_ids,
            active=True
        ),
        Provider(
            id=str(uuid.uuid4()),
            name="Dr. John Doe",
            email="john.doe@example.com",
            phone="555-234-5678",
            specialization="Specialist",
            appointment_types=appointment_type_ids[:2],  # Only first two appointment types
            active=True
        ),
        Provider(
            id=str(uuid.uuid4()),
            name="Dr. Emily Johnson",
            email="emily.johnson@example.com",
            phone="555-345-6789",
            specialization="Pediatrician",
            appointment_types=appointment_type_ids[1:],  # Skip the first appointment type
            active=True
        )
    ]
    
    # Store provider IDs for later use
    provider_ids = []
    
    for provider in providers:
        await db.create("providers", provider.id, provider)
        provider_ids.append(provider.id)
        print(f"Created provider: {provider.name}")
        
        # Create availability for this provider
        await create_provider_availability(provider.id)
    
    return provider_ids

async def create_provider_availability(provider_id):
    """Create sample availability for a provider."""
    # Create a standard 9-5 schedule on weekdays
    weekly_schedule = WeeklySchedule(
        monday=[{"start": time(9, 0), "end": time(17, 0)}],
        tuesday=[{"start": time(9, 0), "end": time(17, 0)}],
        wednesday=[{"start": time(9, 0), "end": time(17, 0)}],
        thursday=[{"start": time(9, 0), "end": time(17, 0)}],
        friday=[{"start": time(9, 0), "end": time(17, 0)}],
        saturday=None,
        sunday=None
    )
    
    availability = Availability(
        provider_id=provider_id,
        weekly_schedule=weekly_schedule,
        exceptions={},
        unavailable_dates=[]
    )
    
    await db.create("availability", provider_id, availability)
    print(f"Created availability for provider ID: {provider_id}")

async def create_customers():
    """Create sample customers."""
    customers = [
        Customer(
            id=str(uuid.uuid4()),
            name="Alice Johnson",
            email="alice.johnson@example.com",
            phone="555-987-6543",
            address="123 Main St, Anytown, USA",
            created_at=datetime.now()
        ),
        Customer(
            id=str(uuid.uuid4()),
            name="Bob Williams",
            email="bob.williams@example.com",
            phone="555-876-5432",
            address="456 Oak Ave, Somewhere, USA",
            created_at=datetime.now()
        ),
        Customer(
            id=str(uuid.uuid4()),
            name="Carol Davis",
            email="carol.davis@example.com",
            phone="555-765-4321",
            address="789 Pine St, Nowhere, USA",
            created_at=datetime.now()
        )
    ]
    
    # Store customer IDs for later use
    customer_ids = []
    
    for customer in customers:
        await db.create("customers", customer.id, customer)
        customer_ids.append(customer.id)
        print(f"Created customer: {customer.name}")
    
    return customer_ids

async def create_appointments(provider_ids, customer_ids, appointment_type_ids):
    """Create sample appointments."""
    # Create a few appointments over the next week
    now = datetime.now()
    
    appointments = [
        # Tomorrow appointment
        Appointment(
            id=str(uuid.uuid4()),
            provider_id=provider_ids[0],
            customer_id=customer_ids[0],
            appointment_type_id=appointment_type_ids[0],
            start_time=now.replace(hour=10, minute=0) + timedelta(days=1),
            end_time=now.replace(hour=10, minute=30) + timedelta(days=1),
            status=AppointmentStatus.SCHEDULED,
            notes="Initial checkup",
            created_at=now,
            updated_at=now
        ),
        # Two days from now
        Appointment(
            id=str(uuid.uuid4()),
            provider_id=provider_ids[1],
            customer_id=customer_ids[1],
            appointment_type_id=appointment_type_ids[1],
            start_time=now.replace(hour=14, minute=0) + timedelta(days=2),
            end_time=now.replace(hour=14, minute=45) + timedelta(days=2),
            status=AppointmentStatus.SCHEDULED,
            notes="Consultation regarding treatment options",
            created_at=now,
            updated_at=now
        ),
        # Next week
        Appointment(
            id=str(uuid.uuid4()),
            provider_id=provider_ids[2],
            customer_id=customer_ids[2],
            appointment_type_id=appointment_type_ids[2],
            start_time=now.replace(hour=11, minute=0) + timedelta(days=7),
            end_time=now.replace(hour=12, minute=0) + timedelta(days=7),
            status=AppointmentStatus.SCHEDULED,
            notes="Urgent care for persistent symptoms",
            created_at=now,
            updated_at=now
        )
    ]
    
    for appointment in appointments:
        await db.create("appointments", appointment.id, appointment)
        print(f"Created appointment: {appointment.id} at {appointment.start_time}")

async def main():
    """Initialize database with sample data."""
    print("Initializing database with sample data...")
    
    # Create sample data
    appointment_type_ids = await create_appointment_types()
    provider_ids = await create_providers(appointment_type_ids)
    customer_ids = await create_customers()
    await create_appointments(provider_ids, customer_ids, appointment_type_ids)
    
    print("Database initialization complete!")

if __name__ == "__main__":
    # Run the async function
    asyncio.run(main()) 