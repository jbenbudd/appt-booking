# Appointment Booking API

A serverless appointment booking system built with Google Cloud Functions and Firestore.

## Service URLs

- **Appointment Types**: https://appointment-types-service-ianfiofulq-uc.a.run.app
- **Providers**: https://providers-service-ianfiofulq-uc.a.run.app
- **Customers**: https://customers-service-ianfiofulq-uc.a.run.app
- **Appointments**: https://appointments-service-ianfiofulq-uc.a.run.app

## Documentation

Each service has interactive Swagger documentation available by adding `/docs` to the service URL:

```
https://appointment-types-service-ianfiofulq-uc.a.run.app/docs
```

## Main Features

- Create and manage appointment types (services offered)
- Manage service providers and their availability
- Handle customer information
- Book appointments based on provider availability
- Find available time slots for booking

## Tech Stack

- **Backend**: Python with FastAPI
- **Database**: Firestore
- **Deployment**: Google Cloud Functions
- **CI/CD**: GitHub Actions

## Deployment

The system uses GitHub Actions for continuous deployment. When code is pushed to the main branch, the workflow automatically:
   - Installs dependencies
   - Authenticates with Google Cloud
   - Deploys each service as a separate Cloud Function
   - Runs API tests to verify functionality

This ensures that the latest version is always deployed and functioning correctly.

## Getting Started

1. Explore the API documentation at the `/docs` endpoint
2. Use the endpoints to create appointment types, providers, and customers
3. Set up provider availability
4. Find available slots and create appointments

## Testing

To run the API tests:

```bash
python test_api.py
```

## Data Flow

1. Create appointment types → 2. Create providers → 3. Set availability → 4. Create customers → 5. Book appointments
