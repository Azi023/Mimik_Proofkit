"""Fixtures for API tests."""

import pytest
import asyncio
from typing import AsyncGenerator
from unittest.mock import MagicMock, patch, AsyncMock

import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from proofkit.api.main import create_app
from proofkit.api.database import init_db, close_db, Base, get_db
from proofkit.api.database.models import User, Audit
from proofkit.api.auth.api_keys import generate_api_key


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def app():
    """Create test application."""
    # Use in-memory SQLite for tests
    with patch("proofkit.api.database.get_database_url") as mock_url:
        mock_url.return_value = "sqlite+aiosqlite:///:memory:"

        test_app = create_app()

        # Initialize database
        await init_db()

        yield test_app

        # Cleanup
        await close_db()


@pytest_asyncio.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def test_user(app) -> User:
    """Create a test user with API key."""
    from proofkit.api.database.crud import create_user

    api_key = generate_api_key("pk_test")
    user = await create_user(
        email="test@example.com",
        api_key=api_key,
        name="Test User",
    )
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user) -> dict:
    """Get authentication headers for test user."""
    return {"Authorization": f"Bearer {test_user.api_key}"}


@pytest_asyncio.fixture
async def test_audit(test_user) -> Audit:
    """Create a test audit."""
    from proofkit.api.database.crud import create_audit_record, update_audit_status, save_audit_results

    audit = await create_audit_record(
        url="https://example.com",
        mode="fast",
        user_id=test_user.id,
        business_type="agency",
    )

    # Mark as complete with sample data
    await update_audit_status(audit.id, "complete")
    await save_audit_results(audit.id, {
        "scorecard": {"OVERALL": 75, "SEO": 80, "PERFORMANCE": 70},
        "finding_count": 5,
    })

    # Refresh to get updated data
    from proofkit.api.database.crud import get_audit
    return await get_audit(audit.id)


@pytest.fixture
def mock_audit_runner():
    """Mock the AuditRunner for background jobs."""
    with patch("proofkit.api.jobs.queue.AuditRunner") as MockRunner:
        mock_result = MagicMock()
        mock_result.audit_id = "test_audit"
        mock_result.scorecard = {"OVERALL": 75}
        mock_result.finding_count = 5
        mock_result.output_dir = "/tmp/test"
        mock_result.status = MagicMock(value="complete")

        mock_runner = MagicMock()
        mock_runner.run.return_value = mock_result
        MockRunner.return_value = mock_runner

        yield MockRunner
