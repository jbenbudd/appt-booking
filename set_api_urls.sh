#!/bin/bash
# Script to set environment variables for API testing

export APPT_TYPES_URL="https://us-central1-appt-booking-e9d9c.cloudfunctions.net/appointment-types-service"
export PROVIDERS_URL="https://us-central1-appt-booking-e9d9c.cloudfunctions.net/providers-service"
export CUSTOMERS_URL="https://us-central1-appt-booking-e9d9c.cloudfunctions.net/customers-service"
export APPOINTMENTS_URL="https://us-central1-appt-booking-e9d9c.cloudfunctions.net/appointments-service"

echo "API URLs set in environment variables:"
echo "APPT_TYPES_URL: $APPT_TYPES_URL"
echo "PROVIDERS_URL: $PROVIDERS_URL"
echo "CUSTOMERS_URL: $CUSTOMERS_URL"
echo "APPOINTMENTS_URL: $APPOINTMENTS_URL"
echo ""
echo "Run the test script with: python test_api.py" 