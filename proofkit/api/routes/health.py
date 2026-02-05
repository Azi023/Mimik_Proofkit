"""Health check endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel

from proofkit import __version__


router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str


class DetailedHealthResponse(BaseModel):
    """Detailed health check response."""
    status: str
    version: str
    database: str
    api_ready: bool


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Basic health check endpoint.

    Returns service status and version.
    """
    return HealthResponse(
        status="healthy",
        version=__version__,
    )


@router.get("/v1/health", response_model=DetailedHealthResponse)
async def detailed_health_check():
    """
    Detailed health check with component status.

    Returns status of all service components.
    """
    # Check database connectivity
    db_status = "healthy"
    try:
        from ..database import get_db
        async for db in get_db():
            await db.execute("SELECT 1")
    except Exception:
        db_status = "unhealthy"

    return DetailedHealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        version=__version__,
        database=db_status,
        api_ready=True,
    )
