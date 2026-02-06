"""API key authentication."""

from fastapi import HTTPException, Security, Request
from fastapi.security import APIKeyHeader, APIKeyQuery
from typing import Optional
import secrets

from proofkit.utils.logger import logger


# API key can be provided in multiple ways
api_key_header = APIKeyHeader(
    name="Authorization",
    auto_error=False,
    description="API key in format: Bearer pk_live_xxxxx",
)
api_key_header_alt = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
    description="API key directly in X-API-Key header",
)
api_key_query = APIKeyQuery(
    name="api_key",
    auto_error=False,
    description="API key as query parameter (not recommended)",
)


async def get_api_key(
    auth_header: Optional[str] = Security(api_key_header),
    x_api_key: Optional[str] = Security(api_key_header_alt),
    query_key: Optional[str] = Security(api_key_query),
) -> str:
    """
    Extract API key from various sources.

    Checks in order:
    1. Authorization header (Bearer token)
    2. X-API-Key header
    3. api_key query parameter
    """
    # Try Authorization header (Bearer token)
    if auth_header:
        if auth_header.startswith("Bearer "):
            return auth_header[7:]
        return auth_header

    # Try X-API-Key header
    if x_api_key:
        return x_api_key

    # Try query parameter
    if query_key:
        return query_key

    raise HTTPException(
        status_code=401,
        detail="Missing API key. Provide via Authorization header (Bearer token), X-API-Key header, or api_key query parameter.",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def verify_api_key(
    api_key: str = Security(get_api_key),
):
    """
    Verify API key and return user.

    Raises HTTPException 401 if key is missing or invalid.
    """
    # Import here to avoid circular imports
    from ..database.crud import get_user_by_api_key

    user = await get_user_by_api_key(api_key)

    if not user:
        logger.warning(f"Invalid API key attempt: {api_key[:10]}...")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_user(
    api_key: str = Security(get_api_key),
):
    """
    Get current user from API key.

    This is an alias for verify_api_key that returns the user.
    """
    return await verify_api_key(api_key)


def generate_api_key(prefix: str = "pk_live") -> str:
    """
    Generate a new API key.

    Args:
        prefix: Key prefix (pk_live for production, pk_test for testing)

    Returns:
        Generated API key string
    """
    random_part = secrets.token_urlsafe(24)
    return f"{prefix}_{random_part}"


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key for storage.

    Note: For simplicity, we store keys directly in this implementation.
    In production, you should hash them.
    """
    # In production, use proper hashing:
    # import hashlib
    # return hashlib.sha256(api_key.encode()).hexdigest()
    return api_key
