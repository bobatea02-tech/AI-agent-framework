
import os
from typing import Optional
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from starlette.requests import Request

# Define the header key
API_KEY_HEADER_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)

def verify_api_key(
    request: Request, 
    api_key: Optional[str] = Security(api_key_header)
) -> str:
    """
    Dependency to verify API Key.
    
    In a real app, this might check a DB. 
    Here we check environment variable `API_KEY_SECRET`.
    If valid, returns the key.
    """
    # Allow skipping auth if explicitly disabled in env (e.g. dev/test)
    if os.getenv("AUTH_ENABLED", "true").lower() == "false":
        return "dev-key"

    expected_key = os.getenv("API_KEY_SECRET")
    if not expected_key:
        # If no secret configured, fail safe (reject all)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server Authorization not configured"
        )
        
    if not api_key or api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key"
        )
        
    return api_key
