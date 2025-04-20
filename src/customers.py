import functions_framework
from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel, EmailStr
import uvicorn
import uuid
from typing import List, Optional
from datetime import datetime

from src.models import Customer
from src.db import FirestoreDB

app = FastAPI()
db = FirestoreDB()

COLLECTION = "customers"

class CustomerCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

@app.post("/customers", response_model=Customer)
async def create_customer(customer: CustomerCreate):
    """Create a new customer."""
    customer_id = str(uuid.uuid4())
    new_customer = Customer(
        id=customer_id,
        **customer.model_dump(),
        created_at=datetime.now()
    )
    
    await db.create(COLLECTION, customer_id, new_customer)
    return new_customer

@app.get("/customers", response_model=List[Customer])
async def list_customers(email: Optional[str] = None, phone: Optional[str] = None):
    """List all customers, optionally filtered by email or phone."""
    filters = None
    
    if email:
        filters = [("email", "==", email)]
    elif phone:
        filters = [("phone", "==", phone)]
    
    return await db.list(COLLECTION, Customer, filters=filters)

@app.get("/customers/{customer_id}", response_model=Customer)
async def get_customer(customer_id: str):
    """Get a customer by ID."""
    customer = await db.get(COLLECTION, customer_id, Customer)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@app.put("/customers/{customer_id}", response_model=Customer)
async def update_customer(customer_id: str, update_data: CustomerUpdate):
    """Update an existing customer."""
    # First get the existing customer
    customer = await db.get(COLLECTION, customer_id, Customer)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Update with non-None values
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    
    # Update in database
    await db.update(COLLECTION, customer_id, update_dict)
    
    # Return updated object
    return await db.get(COLLECTION, customer_id, Customer)

@app.delete("/customers/{customer_id}", status_code=204)
async def delete_customer(customer_id: str):
    """Delete a customer."""
    customer = await db.get(COLLECTION, customer_id, Customer)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    await db.delete(COLLECTION, customer_id)
    return {"message": "Customer deleted"}

@functions_framework.http
def customers_service(request):
    """Cloud Function entry point."""
    # For Cloud Functions Gen 2, the Flask request object is passed directly
    # We need to convert it to WSGI environ format for FastAPI
    asgi_app = app 
    return functions_framework.flask_to_function(asgi_app)(request) 