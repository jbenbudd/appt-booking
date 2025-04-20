# Appointment Booking API

A serverless appointment booking API built with Google Cloud Functions and Firestore.

## API Endpoints

### Appointment Types
- `GET /appointment-types`: List all appointment types
- `POST /appointment-types`: Create a new appointment type
  ```json
  {
    "name": "Regular Checkup",
    "description": "Standard appointment",
    "duration_minutes": 30,
    "price": 50.0,
    "color": "#4CAF50"
  }
  ```
- `GET /appointment-types/{id}`: Get a specific appointment type
- `PUT /appointment-types/{id}`: Update an appointment type
- `DELETE /appointment-types/{id}`: Delete an appointment type

### Providers
- `GET /providers`: List all providers
- `POST /providers`: Create a new provider
  ```json
  {
    "name": "Dr. Jane Smith",
    "email": "jane@example.com",
    "phone": "555-123-4567",
    "specialization": "General",
    "appointment_types": ["appointment-type-id-here"]
  }
  ```
- `GET /providers/{id}`: Get a specific provider
- `PUT /providers/{id}`: Update a provider
- `GET /providers/{id}/availability`: Get a provider's availability
- `PUT /providers/{id}/availability`: Update a provider's availability

### Customers
- `GET /customers`: List all customers
- `POST /customers`: Create a new customer
  ```json
  {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "555-987-6543",
    "address": "123 Main St"
  }
  ```
- `GET /customers/{id}`: Get a specific customer
- `PUT /customers/{id}`: Update a customer
- `DELETE /customers/{id}`: Delete a customer

### Appointments
- `GET /appointments`: List appointments with optional filtering
- `POST /appointments`: Create a new appointment
  ```json
  {
    "provider_id": "provider-id-here",
    "customer_id": "customer-id-here",
    "appointment_type_id": "appointment-type-id-here",
    "start_time": "2023-05-01T10:00:00Z",
    "notes": "Optional notes"
  }
  ```
- `GET /appointments/{id}`: Get a specific appointment
- `PUT /appointments/{id}`: Update an appointment
- `DELETE /appointments/{id}`: Cancel an appointment
- `GET /available-slots`: Find available appointment slots
  ```
  ?provider_id=provider-id-here
  &appointment_type_id=appointment-type-id-here
  &start_date=2023-05-01T00:00:00Z
  &end_date=2023-05-07T23:59:59Z
  ```

## API URLs

The base URLs for each service are:
- Appointment Types: `https://DOMAIN/appointment-types-service`
- Providers: `https://DOMAIN/providers-service`
- Customers: `https://DOMAIN/customers-service`
- Appointments: `https://DOMAIN/appointments-service`

## Testing the API

Use the `test_api.py` script to test all endpoints:

```bash
# Set the API URLs
export APPT_TYPES_URL="https://DOMAIN/appointment-types-service"
export PROVIDERS_URL="https://DOMAIN/providers-service"
export CUSTOMERS_URL="https://DOMAIN/customers-service"
export APPOINTMENTS_URL="https://DOMAIN/appointments-service"

# Run the test script
python test_api.py
```

## API Example (JavaScript)

```javascript
// Sample code to call the APIs
async function getAppointmentTypes() {
  const response = await fetch('https://DOMAIN/appointment-types-service/appointment-types');
  return response.json();
}

async function createAppointment(data) {
  const response = await fetch('https://DOMAIN/appointments-service/appointments', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return response.json();
}
```

## Data Flow

1. Create appointment types
2. Create providers and assign appointment types they can offer
3. Set providers' availability
4. Create customers
5. Find available slots for booking
6. Create appointments
