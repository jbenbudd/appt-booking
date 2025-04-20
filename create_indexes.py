#!/usr/bin/env python3
"""
Create required Firestore indexes for the Appointment Booking System.
"""

import asyncio
import logging
from src.db import FirestoreDB

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Create Firestore indexes."""
    logger.info("Starting index creation...")
    
    # Initialize database connection
    db = FirestoreDB()
    
    # Create indexes
    await db.create_indexes()
    
    logger.info("Index creation process completed.")

if __name__ == "__main__":
    # Run the async function
    asyncio.run(main()) 