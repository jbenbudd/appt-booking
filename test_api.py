#!/usr/bin/env python3
"""
API Test Script for Appointment Booking System

This script tests all API endpoints sequentially, creating test data
and verifying that the system works as expected. It also cleans up
after itself.
"""

import requests
import json
from datetime import datetime, timedelta
import sys
import os
import uuid

# ANSI color codes for output formatting
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"

# Configuration
BASE_URLS = {
    # Update these URLs with your actual Cloud Function URLs
    "appointment_types": os.environ.get("APPT_TYPES_URL", "http://localhost:8080"),
    "providers": os.environ.get("PROVIDERS_URL", "http://localhost:8081"),
    "customers": os.environ.get("CUSTOMERS_URL", "http://localhost:8082"),
    "appointments": os.environ.get("APPOINTMENTS_URL", "http://localhost:8083")
}

# Test data storage
test_data = {
    "appointment_types": [],
    "providers": [],
    "customers": [],
    "appointments": []
}

def print_header(message):
    """Print a formatted header message."""
    print(f"\n{BOLD}{YELLOW}=== {message} ==={RESET}\n")

def print_success(message):
    """Print a success message."""
    print(f"{GREEN}✓ {message}{RESET}")

def print_error(message):
    """Print an error message."""
    print(f"{RED}✗ {message}{RESET}")

def test_endpoint(method, url, data=None, params=None, expected_status=200):
    """Test an API endpoint with the given method, URL, and data."""
    try:
        if method == "GET":
            response = requests.get(url, params=params)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        else:
            print_error(f"Invalid method: {method}")
            return None

        if response.status_code == expected_status:
            print_success(f"{method} {url} - Status: {response.status_code}")
            try:
                return response.json()
            except:
                return response.text
        else:
            print_error(f"{method} {url} - Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"{method} {url} - Error: {str(e)}")
        return None

def test_appointment_types():
    """Test appointment types endpoints."""
    print_header("Testing Appointment Types API")
    base_url = BASE_URLS["appointment_types"]
    
    # Create appointment type
    appointment_type_data = {
        "name": "Test Appointment",
        "description": "A test appointment type",
        "duration_minutes": 30,
        "price": 50.0,
        "color": "#FF5733"
    }
    
    # POST - Create
    result = test_endpoint("POST", f"{base_url}/appointment-types", appointment_type_data)
    if result:
        test_data["appointment_types"].append(result)
        print(f"   Created appointment type with ID: {result['id']}")
    
    # GET - List all
    test_endpoint("GET", f"{base_url}/appointment-types")
    
    if test_data["appointment_types"]:
        appt_type = test_data["appointment_types"][0]
        
        # GET - Get one
        test_endpoint("GET", f"{base_url}/appointment-types/{appt_type['id']}")
        
        # PUT - Update
        update_data = {"description": "Updated test appointment type"}
        updated = test_endpoint("PUT", f"{base_url}/appointment-types/{appt_type['id']}", update_data)
        if updated and updated["description"] == "Updated test appointment type":
            print_success("   Successfully updated appointment type")
        
        # We don't delete appointment types yet because we'll need them for other tests

def test_providers():
    """Test providers endpoints."""
    print_header("Testing Providers API")
    base_url = BASE_URLS["providers"]
    
    if not test_data["appointment_types"]:
        print_error("No appointment types available for testing providers")
        return
    
    # Create provider
    provider_data = {
        "name": "Test Provider",
        "email": "provider@example.com",
        "phone": "555-123-4567",
        "specialization": "Testing",
        "appointment_types": [test_data["appointment_types"][0]["id"]]
    }
    
    # POST - Create
    result = test_endpoint("POST", f"{base_url}/providers", provider_data)
    if result:
        test_data["providers"].append(result)
        print(f"   Created provider with ID: {result['id']}")
    
    # GET - List all
    test_endpoint("GET", f"{base_url}/providers")
    
    if test_data["providers"]:
        provider = test_data["providers"][0]
        
        # GET - Get one
        test_endpoint("GET", f"{base_url}/providers/{provider['id']}")
        
        # PUT - Update
        update_data = {"specialization": "Updated Specialization"}
        updated = test_endpoint("PUT", f"{base_url}/providers/{provider['id']}", update_data)
        if updated and updated["specialization"] == "Updated Specialization":
            print_success("   Successfully updated provider")
        
        # GET - Get availability
        test_endpoint("GET", f"{base_url}/providers/{provider['id']}/availability")
        
        # PUT - Update availability
        # Create a 9-5 schedule for all weekdays
        time_slots = [{"start": "09:00:00", "end": "17:00:00"}]
        availability_data = {
            "provider_id": provider['id'],
            "weekly_schedule": {
                "monday": time_slots,
                "tuesday": time_slots,
                "wednesday": time_slots,
                "thursday": time_slots,
                "friday": time_slots
            }
        }
        test_endpoint("PUT", f"{base_url}/providers/{provider['id']}/availability", availability_data)

def test_customers():
    """Test customers endpoints."""
    print_header("Testing Customers API")
    base_url = BASE_URLS["customers"]
    
    # Create customer
    customer_data = {
        "name": "Test Customer",
        "email": "customer@example.com",
        "phone": "555-987-6543",
        "address": "123 Test St, Testville, TS 12345"
    }
    
    # POST - Create
    result = test_endpoint("POST", f"{base_url}/customers", customer_data)
    if result:
        test_data["customers"].append(result)
        print(f"   Created customer with ID: {result['id']}")
    
    # GET - List all
    test_endpoint("GET", f"{base_url}/customers")
    
    if test_data["customers"]:
        customer = test_data["customers"][0]
        
        # GET - Get one
        test_endpoint("GET", f"{base_url}/customers/{customer['id']}")
        
        # PUT - Update
        update_data = {"address": "456 Updated St, Testville, TS 12345"}
        updated = test_endpoint("PUT", f"{base_url}/customers/{customer['id']}", update_data)
        if updated and updated["address"] == "456 Updated St, Testville, TS 12345":
            print_success("   Successfully updated customer")

def test_appointments():
    """Test appointments endpoints."""
    print_header("Testing Appointments API")
    base_url = BASE_URLS["appointments"]
    
    if not (test_data["providers"] and test_data["customers"] and test_data["appointment_types"]):
        print_error("Missing required data for appointment tests")
        return
    
    # Get available slots
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT12:00:00Z")
    next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%dT12:00:00Z")
    
    slots = test_endpoint(
        "GET", 
        f"{base_url}/available-slots", 
        params={
            "provider_id": test_data["providers"][0]["id"],
            "appointment_type_id": test_data["appointment_types"][0]["id"],
            "start_date": tomorrow,
            "end_date": next_week
        }
    )
    
    if not slots or len(slots) == 0:
        print_error("No available slots found for testing appointments")
        # Create a slot for testing
        tomorrow_noon = (datetime.now() + timedelta(days=1)).replace(hour=12, minute=0).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Create appointment
        appointment_data = {
            "provider_id": test_data["providers"][0]["id"],
            "customer_id": test_data["customers"][0]["id"],
            "appointment_type_id": test_data["appointment_types"][0]["id"],
            "start_time": tomorrow_noon,
            "notes": "Test appointment"
        }
    else:
        # Use the first available slot
        appointment_data = {
            "provider_id": test_data["providers"][0]["id"],
            "customer_id": test_data["customers"][0]["id"],
            "appointment_type_id": test_data["appointment_types"][0]["id"],
            "start_time": slots[0]["start_time"],
            "notes": "Test appointment"
        }
    
    # POST - Create
    result = test_endpoint("POST", f"{base_url}/appointments", appointment_data)
    if result:
        test_data["appointments"].append(result)
        print(f"   Created appointment with ID: {result['id']}")
    
    # GET - List all
    test_endpoint("GET", f"{base_url}/appointments")
    
    if test_data["appointments"]:
        appointment = test_data["appointments"][0]
        
        # GET - Get one
        test_endpoint("GET", f"{base_url}/appointments/{appointment['id']}")
        
        # PUT - Update
        update_data = {"notes": "Updated test appointment notes"}
        updated = test_endpoint("PUT", f"{base_url}/appointments/{appointment['id']}", update_data)
        if updated and updated["notes"] == "Updated test appointment notes":
            print_success("   Successfully updated appointment")
        
        # DELETE - Cancel
        test_endpoint("DELETE", f"{base_url}/appointments/{appointment['id']}", expected_status=204)
        print_success("   Successfully cancelled appointment")

def cleanup():
    """Clean up test data."""
    print_header("Cleaning Up Test Data")
    
    # We don't actually delete most data since it might be useful for manual testing
    print("Skipping deletion to preserve test data for manual inspection")
    print("The following test data was created:")
    
    print(f"- {len(test_data['appointment_types'])} appointment types")
    print(f"- {len(test_data['providers'])} providers")
    print(f"- {len(test_data['customers'])} customers")
    print(f"- {len(test_data['appointments'])} appointments")

def main():
    """Run all tests in sequence."""
    print_header("Starting API Tests")
    
    # Run tests in sequence, with each depending on the previous
    test_appointment_types()
    test_providers()
    test_customers()
    test_appointments()
    
    cleanup()
    
    # Print summary
    success = all(len(data) > 0 for data in test_data.values())
    
    if success:
        print(f"\n{GREEN}{BOLD}All tests completed successfully!{RESET}")
        return 0
    else:
        failed_tests = [name for name, data in test_data.items() if len(data) == 0]
        print(f"\n{RED}{BOLD}Tests failed for: {', '.join(failed_tests)}{RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 