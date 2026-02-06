"""FastAPI application factory and main app instance."""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from proofkit.utils.config import get_config
from proofkit.utils.logger import logger
from proofkit import __version__

from .routes import audits, reports, health
from .auth.middleware import verify_api_key
from .database import init_db, close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    # Startup
    logger.info("Starting ProofKit API...")
    await init_db()
    yield
    # Shutdown
    logger.info("Shutting down ProofKit API...")
    await close_db()


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    config = get_config()

    app = FastAPI(
        title="Mimik ProofKit API",
        description="Website Audit QA Engine - Automated website auditing with AI-powered insights",
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # CORS middleware - Allow all origins for development
    # Note: In production, restrict to specific origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    # Health check routes (no auth required)
    app.include_router(
        health.router,
        tags=["Health"],
    )

    # Audit routes (auth required)
    app.include_router(
        audits.router,
        prefix="/v1",
        tags=["Audits"],
        dependencies=[Depends(verify_api_key)],
    )

    # Report routes (auth required)
    app.include_router(
        reports.router,
        prefix="/v1",
        tags=["Reports"],
        dependencies=[Depends(verify_api_key)],
    )

    return app


# Create default app instance
app = create_app()
