"""
Appointment Booking System - Entry point for Cloud Functions
"""

# Import all the Cloud Function handlers
from src.appointment_types import appointment_types_service
from src.providers import providers_service 
from src.customers import customers_service
from src.appointments import appointments_service

# Expose all the functions for deployment
# These need to be at the top level of the main.py file for Cloud Functions Gen 2 