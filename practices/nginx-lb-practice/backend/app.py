from fastapi import FastAPI, Request
import os

# Create a FastAPI application instance
app = FastAPI()

@app.get("/") # Define a GET request endpoint for the root path
async def read_root(request: Request):
    """
    Responds to root path requests.
    Returns which server processed the request and the client's IP.
    """
    # Retrieve server name and IP from environment variables
    server_name = os.getenv('SERVER_NAME', 'Unknown Server')
    server_ip = os.getenv('SERVER_IP', 'Unknown IP')

    # Get the client's real IP, prioritizing X-Real-IP header from Nginx
    # Fallback to FastAPI's request.client.host if X-Real-IP is not present
    client_ip = request.headers.get('X-Real-IP', request.client.host)

    # Return the response message
    return {"message": f"Hello from {server_name} ({server_ip})! Your IP is {client_ip}"}