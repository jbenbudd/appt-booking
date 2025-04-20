"""
Utility functions for the appointment booking system
"""

import asyncio
import logging
from flask import Response
from fastapi import FastAPI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fastapi_cloud_function_handler(app: FastAPI, request, function_name: str):
    """
    Handle a Cloud Function request using a FastAPI app.
    
    Args:
        app: The FastAPI app
        request: The Cloud Function request object
        function_name: The name of the function (for path prefix removal)
        
    Returns:
        A Flask Response object
    """
    try:
        logger.info(f"{function_name} Service: Received request")
        
        # Extract request path and method
        path = request.path
        function_prefix = f'/{function_name}'
        if path.startswith(function_prefix):
            # Remove the Cloud Function prefix from the path
            path = path[len(function_prefix):]
        
        # Ensure path starts with /
        if not path.startswith('/'):
            path = '/' + path
        
        # Create scope for ASGI request
        scope = {
            'type': 'http',
            'asgi': {'version': '3.0'},
            'http_version': '1.1',
            'method': request.method,
            'scheme': 'https',
            'path': path,
            'query_string': request.query_string,
            'headers': [(k.lower().encode(), v.encode()) for k, v in request.headers.items()],
            'raw_path': path.encode(),
        }
        
        # Process request through FastAPI
        body = request.get_data()
        
        async def receive():
            return {'type': 'http.request', 'body': body, 'more_body': False}
        
        response_body = []
        response_headers = []
        response_status = [200]
        
        async def send(message):
            if message['type'] == 'http.response.start':
                response_status[0] = message['status']
                response_headers.extend(message.get('headers', []))
            elif message['type'] == 'http.response.body':
                response_body.append(message.get('body', b''))
        
        # Run the ASGI app
        async def run_app():
            await app(scope, receive, send)
        
        asyncio.run(run_app())
        
        # Format response for Cloud Functions
        body_content = b''.join(response_body)
        headers = {k.decode(): v.decode() for k, v in response_headers}
        
        logger.info(f"{function_name} Service: Processed successfully with status {response_status[0]}")
        return Response(
            response=body_content,
            status=response_status[0],
            headers=headers
        )
    
    except Exception as e:
        logger.error(f"{function_name} Service ERROR: {str(e)}", exc_info=True)
        # Return a formatted error response
        import traceback
        error_details = {
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        import json
        return Response(
            response=json.dumps(error_details),
            status=500,
            mimetype="application/json"
        ) 