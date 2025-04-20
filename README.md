# Cloud-Native Appointment Booking Service

A serverless appointment booking service built on Google Cloud Platform using Firebase/Firestore and Cloud Functions.

## Architecture

This appointment booking service is designed as a collection of microservices, each handling specific functionality:

- **Appointment Types Service**: Manages types of appointments that can be booked
- **Providers Service**: Manages service providers and their availability
- **Customers Service**: Manages customer information
- **Appointments Service**: Handles appointment booking, updating, and cancellation

Each service is deployed as a separate Cloud Function with its own API endpoints.

## Tech Stack

- **Backend**: Python 3.11+
- **Database**: Firestore (NoSQL database)
- **API Framework**: FastAPI (wrapped in Cloud Functions)
- **Frontend**: (To be implemented)

## API Endpoints

### Appointment Types

- `GET /appointment-types`: List all appointment types
- `GET /appointment-types/{type_id}`: Get a specific appointment type
- `POST /appointment-types`: Create a new appointment type
- `PUT /appointment-types/{type_id}`: Update an appointment type
- `DELETE /appointment-types/{type_id}`: Delete an appointment type

### Providers

- `GET /providers`: List all providers
- `GET /providers/{provider_id}`: Get a specific provider
- `POST /providers`: Create a new provider
- `PUT /providers/{provider_id}`: Update a provider
- `DELETE /providers/{provider_id}`: Deactivate a provider
- `GET /providers/{provider_id}/availability`: Get a provider's availability
- `PUT /providers/{provider_id}/availability`: Update a provider's availability

### Customers

- `GET /customers`: List all customers
- `GET /customers/{customer_id}`: Get a specific customer
- `POST /customers`: Create a new customer
- `PUT /customers/{customer_id}`: Update a customer
- `DELETE /customers/{customer_id}`: Delete a customer

### Appointments

- `GET /appointments`: List appointments with optional filtering
- `GET /appointments/{appointment_id}`: Get a specific appointment
- `POST /appointments`: Create a new appointment
- `PUT /appointments/{appointment_id}`: Update an appointment
- `DELETE /appointments/{appointment_id}`: Cancel an appointment
- `GET /available-slots`: Find available appointment slots
