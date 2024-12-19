from fastapi import Security, HTTPException, Depends
from fastapi.security import APIKeyHeader
import secrets
from ..config import settings

api_key_header = APIKeyHeader(name="Authorization", auto_error=True)

async def verify_api_key(auth_header: str = Security(api_key_header)) -> str:
    """Verify the API key from the Authorization header."""
    try:
        key = auth_header.replace("Bearer ", "")
        if not secrets.compare_digest(key, settings.API_KEY):
            raise HTTPException(
                status_code=401,
                detail="Invalid API key"
            )
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization credentials"
        )
    return auth_header 