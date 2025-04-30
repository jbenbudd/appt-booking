#!/usr/bin/env python3
"""
Load Testing Script for Appointment Booking API

This script runs a 24-hour load test with:
- One request per hour at random times
- A burst of 1000 requests during hour #3 of the test
"""

import requests
import time
import random
import datetime
import logging
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("load_test.log"),
        logging.StreamHandler()
    ]
)

# API endpoints
API_ENDPOINTS = {
    "appointment_types": "https://appointment-types-service-ianfiofulq-uc.a.run.app/appointment-types",
    "providers": "https://providers-service-ianfiofulq-uc.a.run.app/providers",
    "customers": "https://customers-service-ianfiofulq-uc.a.run.app/customers",
    "appointments": "https://appointments-service-ianfiofulq-uc.a.run.app/appointments",
    "available_slots": "https://appointments-service-ianfiofulq-uc.a.run.app/available-slots"
}

# Specify which hour will have the burst of requests (0-23)
BURST_HOUR = 3

def make_request(endpoint_name=None):
    """Make a single request to a random or specified endpoint and log the result"""
    if endpoint_name is None:
        # Choose a random endpoint if none specified
        endpoint_name = random.choice(list(API_ENDPOINTS.keys()))
    
    url = API_ENDPOINTS[endpoint_name]
    
    start_time = time.time()
    try:
        response = requests.get(url)
        duration = time.time() - start_time
        status = response.status_code
        
        logging.info(f"Request to {endpoint_name}: status={status}, duration={duration:.3f}s")
        return {
            "endpoint": endpoint_name,
            "status": status,
            "duration": duration
        }
    except Exception as e:
        duration = time.time() - start_time
        logging.error(f"Request to {endpoint_name} failed: {str(e)}, duration={duration:.3f}s")
        return {
            "endpoint": endpoint_name,
            "status": "error",
            "duration": duration,
            "error": str(e)
        }

def burst_test():
    """Run 1000 requests in parallel using a thread pool"""
    logging.info(f"Starting burst test with 1000 requests")
    
    results = []
    # Use ThreadPoolExecutor to make requests in parallel
    with ThreadPoolExecutor(max_workers=50) as executor:
        # Submit 1000 tasks to the executor
        futures = [executor.submit(make_request) for _ in range(1000)]
        
        # Collect results as they complete
        for future in futures:
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logging.error(f"Error in thread: {str(e)}")
    
    # Summarize results
    successful = sum(1 for r in results if isinstance(r.get("status"), int) and 200 <= r.get("status") < 300)
    failed = len(results) - successful
    avg_duration = sum(r.get("duration", 0) for r in results) / len(results) if results else 0
    
    logging.info(f"Burst test completed: {successful} successful, {failed} failed, avg duration: {avg_duration:.3f}s")

def run_load_test():
    """Run the full 24-hour load test"""
    logging.info("Starting 24-hour load test")
    
    # Record start time
    start_time = time.time()
    test_end_time = start_time + (24 * 60 * 60)  # 24 hours in seconds
    
    # Keep track of the current hour
    current_hour = 0
    next_hour_time = start_time + (60 * 60)  # 1 hour in seconds
    
    while time.time() < test_end_time:
        current_time = time.time()
        
        # Check if we've moved to a new hour
        if current_time >= next_hour_time:
            current_hour += 1
            next_hour_time = start_time + (current_hour + 1) * 60 * 60
            logging.info(f"Moving to hour {current_hour} of the test")
            
            # If we're in the burst hour, run the burst test
            if current_hour == BURST_HOUR:
                logging.info(f"Reached burst hour ({BURST_HOUR})")
                burst_test()
        
        # Check if we should make the hourly random request
        # Calculate a random time point within this hour
        this_hour_end = next_hour_time
        this_hour_start = this_hour_end - (60 * 60)
        random_request_time = random.uniform(this_hour_start, this_hour_end)
        
        # If we're past the random time point for this hour and haven't made the request yet
        if current_time >= random_request_time and current_time < this_hour_end:
            logging.info(f"Making random request for hour {current_hour}")
            make_request()
            
            # Sleep until the next hour starts
            sleep_time = this_hour_end - current_time
            time.sleep(sleep_time)
        else:
            # Sleep for a short time before checking again
            time.sleep(10)
    
    logging.info("24-hour load test completed")

if __name__ == "__main__":
    logging.info(f"Load test configured with burst during hour {BURST_HOUR}")
    logging.info(f"Testing endpoints: {', '.join(API_ENDPOINTS.keys())}")
    
    try:
        run_load_test()
    except KeyboardInterrupt:
        logging.info("Load test manually interrupted")
    except Exception as e:
        logging.error(f"Load test failed with error: {str(e)}")
        raise 