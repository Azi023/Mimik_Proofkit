"""Database initialization and session management."""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from pathlib import Path
from typing import AsyncGenerator

from proofkit.utils.config import get_config
from proofkit.utils.logger import logger


# SQLAlchemy base for models
Base = declarative_base()

# Global engine and session factory
_engine = None
_async_session_factory = None


def get_database_url() -> str:
    """Get database URL from config or use default SQLite."""
    config = get_config()
    db_path = config.output_dir / "proofkit.db"
    return f"sqlite+aiosqlite:///{db_path}"


async def init_db():
    """Initialize the database connection and create tables."""
    global _engine, _async_session_factory

    database_url = get_database_url()
    logger.info(f"Initializing database: {database_url}")

    # Ensure directory exists
    if "sqlite" in database_url:
        db_path = database_url.replace("sqlite+aiosqlite:///", "")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    # Create async engine
    _engine = create_async_engine(
        database_url,
        echo=False,  # Set to True for SQL debugging
        future=True,
    )

    # Create session factory
    _async_session_factory = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Import models to register them
    from . import models  # noqa: F401

    # Create all tables
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database initialized")

    # Create default user if none exists
    await _ensure_default_user()


async def _ensure_default_user():
    """Create a default user/API key for development."""
    from .crud import get_user_by_email, create_user
    from ..auth.api_keys import generate_api_key

    async for session in get_db():
        # Check if any user exists
        default_email = "admin@proofkit.local"
        user = await get_user_by_email(default_email)

        if not user:
            # Create default user with API key
            api_key = generate_api_key("pk_dev")
            user = await create_user(
                email=default_email,
                api_key=api_key,
            )
            logger.info(f"Created default user with API key: {api_key}")
        break


async def close_db():
    """Close database connection."""
    global _engine
    if _engine:
        await _engine.dispose()
        logger.info("Database connection closed")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session.

    Usage:
        async for session in get_db():
            # Use session
    """
    if _async_session_factory is None:
        await init_db()

    async with _async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
