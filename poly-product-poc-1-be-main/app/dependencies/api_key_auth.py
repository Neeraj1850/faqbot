from fastapi import Header, HTTPException
import os

API_KEYS = set(k.strip() for k in os.getenv("API_KEYS", "").split(",") if k.strip())

async def require_api_key(x_api_key: str = Header(None)):
    if not x_api_key or x_api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return True
