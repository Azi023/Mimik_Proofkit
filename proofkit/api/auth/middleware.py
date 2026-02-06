"""Authentication middleware."""

from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from proofkit.utils.logger import logger


# HTTP Bearer security scheme
security = HTTPBearer(auto_error=False)


async def verify_api_key(request: Request):
    """
    Middleware to verify API key for protected routes.

    Can be used as a dependency in route definitions.
    Accepts API key from:
    1. Authorization header (Bearer token)
    2. X-API-Key header
    3. api_key query parameter
    """
    # Get API key from various sources
    auth_header = request.headers.get("Authorization")
    x_api_key_header = request.headers.get("X-API-Key")
    api_key_param = request.query_params.get("api_key")

    api_key = None

    # Try Authorization header (Bearer token)
    if auth_header:
        if auth_header.startswith("Bearer "):
            api_key = auth_header[7:]
        else:
            api_key = auth_header
    # Try X-API-Key header
    elif x_api_key_header:
        api_key = x_api_key_header
    # Try query parameter
    elif api_key_param:
        api_key = api_key_param

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Provide via Authorization header (Bearer token), X-API-Key header, or api_key query parameter.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Import here to avoid circular imports
    from ..database.crud import get_user_by_api_key

    user = await get_user_by_api_key(api_key)

    if not user:
        logger.warning(f"Invalid API key from {request.client.host}: {api_key[:15]}... (length: {len(api_key)})")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Attach user to request state for later use
    request.state.user = user

    return user


class OptionalAPIKeyAuth:
    """
    Optional API key authentication.

    Returns None if no key provided, raises error if key is invalid.
    """

    async def __call__(self, request: Request) -> Optional[object]:
        auth_header = request.headers.get("Authorization")
        api_key_param = request.query_params.get("api_key")

        if not auth_header and not api_key_param:
            return None

        return await verify_api_key(request)
