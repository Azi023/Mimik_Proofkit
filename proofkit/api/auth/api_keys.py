"""API key authentication."""

from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader, APIKeyQuery
from typing import Optional
import secrets

from proofkit.utils.logger import logger


# API key can be provided in header or query parameter
api_key_header = APIKeyHeader(
    name="Authorization",
    auto_error=False,
    description="API key in format: Bearer pk_live_xxxxx",
)
api_key_query = APIKeyQuery(
    name="api_key",
    auto_error=False,
    description="API key as query parameter (not recommended)",
)


async def verify_api_key(
    header_key: Optional[str] = Security(api_key_header),
    query_key: Optional[str] = Security(api_key_query),
):
    """
    Verify API key from Authorization header or query parameter.

    Raises HTTPException 401 if key is missing or invalid.
    """
    api_key = header_key or query_key

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Provide via Authorization header or api_key query param.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Remove "Bearer " prefix if present
    if api_key.startswith("Bearer "):
        api_key = api_key[7:]

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
    header_key: Optional[str] = Security(api_key_header),
    query_key: Optional[str] = Security(api_key_query),
):
    """
    Get current user from API key.

    This is an alias for verify_api_key that returns the user.
    """
    return await verify_api_key(header_key, query_key)


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
