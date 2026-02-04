from fastapi import Depends, HTTPException, Header
from sqlmodel import Session
from typing import Optional, Set
import os
from src.models.database import get_session


def _allowed_api_keys() -> Set[str]:
    """Collect allowed API keys from environment for compatibility.

    Supports multiple env vars to match docs, clients and tests:
    - API_KEY_HEADLESS_PM (preferred)
    - API_KEY (legacy/server)
    - HEADLESS_PM_API_KEY (fallback)
    Defaults to {'development-key'} if none provided.
    """
    candidates = (
        os.getenv("API_KEY_HEADLESS_PM"),
        os.getenv("API_KEY"),
        os.getenv("HEADLESS_PM_API_KEY"),
    )
    keys = {k for k in candidates if k}
    # In non-production, accept common dev/test keys
    environment = os.getenv("ENVIRONMENT", "development").lower()
    if environment != "production":
        keys.update({"development-key", "XXXXXX"})
    return keys


def verify_api_key(x_api_key: Optional[str] = Header(None)):
    if not x_api_key or x_api_key not in _allowed_api_keys():
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


def get_db(api_key: str = Depends(verify_api_key)) -> Session:
    return next(get_session())
