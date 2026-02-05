"""Database CRUD operations."""

from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User, Audit, WebhookLog, generate_id


# We need direct session access, so we'll use the factory directly
_session_factory = None


async def _get_session():
    """Get a database session."""
    global _session_factory
    if _session_factory is None:
        from . import _async_session_factory
        _session_factory = _async_session_factory
    return _session_factory()


# ============================================================================
# User operations
# ============================================================================

async def get_user_by_api_key(api_key: str) -> Optional[User]:
    """Get user by API key."""
    from . import _async_session_factory
    if _async_session_factory is None:
        return None

    async with _async_session_factory() as session:
        result = await session.execute(
            select(User).where(
                User.api_key == api_key,
                User.is_active == True,
            )
        )
        return result.scalar_one_or_none()


async def get_user_by_email(email: str) -> Optional[User]:
    """Get user by email."""
    from . import _async_session_factory
    if _async_session_factory is None:
        return None

    async with _async_session_factory() as session:
        result = await session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()


async def get_user_by_id(user_id: str) -> Optional[User]:
    """Get user by ID."""
    from . import _async_session_factory
    if _async_session_factory is None:
        return None

    async with _async_session_factory() as session:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()


async def create_user(
    email: str,
    api_key: str,
    name: Optional[str] = None,
) -> User:
    """Create a new user."""
    from . import _async_session_factory

    async with _async_session_factory() as session:
        user = User(
            id=generate_id("usr"),
            email=email,
            api_key=api_key,
            name=name,
        )
        session.add(user)
        await session.commit()

        # Re-fetch the user to get all fields
        result = await session.execute(
            select(User).where(User.id == user.id)
        )
        return result.scalar_one()


async def update_user_api_key(user_id: str, new_api_key: str) -> Optional[User]:
    """Update user's API key."""
    from . import _async_session_factory

    async with _async_session_factory() as session:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.api_key = new_api_key
            await session.commit()
        return user


# ============================================================================
# Audit operations
# ============================================================================

async def create_audit_record(
    url: str,
    mode: str,
    user_id: str,
    business_type: Optional[str] = None,
    conversion_goal: Optional[str] = None,
    generate_concept: bool = False,
) -> Audit:
    """Create a new audit record."""
    from . import _async_session_factory

    async with _async_session_factory() as session:
        audit = Audit(
            id=generate_id("aud"),
            url=url,
            mode=mode,
            user_id=user_id,
            business_type=business_type,
            conversion_goal=conversion_goal,
            generate_concept=generate_concept,
            status="queued",
        )
        session.add(audit)
        await session.commit()

        # Re-fetch the audit
        result = await session.execute(
            select(Audit).where(Audit.id == audit.id)
        )
        return result.scalar_one()


async def get_audit(audit_id: str, user_id: Optional[str] = None) -> Optional[Audit]:
    """
    Get audit by ID.

    Args:
        audit_id: Audit identifier
        user_id: Optional user ID to verify ownership

    Returns:
        Audit or None
    """
    from . import _async_session_factory
    if _async_session_factory is None:
        return None

    async with _async_session_factory() as session:
        query = select(Audit).where(Audit.id == audit_id)
        if user_id:
            query = query.where(Audit.user_id == user_id)

        result = await session.execute(query)
        return result.scalar_one_or_none()


async def list_audits(
    user_id: str,
    limit: int = 20,
    offset: int = 0,
    status: Optional[str] = None,
) -> Tuple[List[Audit], int]:
    """
    List audits for a user with pagination.

    Returns:
        Tuple of (audits list, total count)
    """
    from . import _async_session_factory

    async with _async_session_factory() as session:
        # Base query
        query = select(Audit).where(Audit.user_id == user_id)

        # Apply status filter
        if status:
            query = query.where(Audit.status == status)

        # Get total count
        count_query = select(func.count()).select_from(
            query.subquery()
        )
        total_result = await session.execute(count_query)
        total = total_result.scalar()

        # Apply pagination and ordering
        query = query.order_by(Audit.created_at.desc())
        query = query.limit(limit).offset(offset)

        result = await session.execute(query)
        audits = result.scalars().all()

        return list(audits), total


async def update_audit_status(
    audit_id: str,
    status: str,
    error: Optional[str] = None,
) -> Optional[Audit]:
    """Update audit status."""
    from . import _async_session_factory

    async with _async_session_factory() as session:
        result = await session.execute(
            select(Audit).where(Audit.id == audit_id)
        )
        audit = result.scalar_one_or_none()

        if audit:
            audit.status = status
            if error:
                audit.error = error
            if status == "complete":
                audit.completed_at = datetime.utcnow()

            await session.commit()

        return audit


async def save_audit_results(
    audit_id: str,
    results: dict,
) -> Optional[Audit]:
    """Save audit results."""
    from . import _async_session_factory

    async with _async_session_factory() as session:
        result = await session.execute(
            select(Audit).where(Audit.id == audit_id)
        )
        audit = result.scalar_one_or_none()

        if audit:
            audit.scorecard = results.get("scorecard")
            audit.finding_count = results.get("finding_count", 0)
            audit.raw_data_path = results.get("output_dir")

            # Load full report data if available
            if results.get("output_dir"):
                report_path = f"{results['output_dir']}/out/report.json"
                try:
                    import json
                    with open(report_path) as f:
                        audit.report_data = json.load(f)
                except Exception:
                    pass

            await session.commit()

        return audit


async def delete_audit(audit_id: str) -> bool:
    """Delete an audit and its data."""
    from . import _async_session_factory

    async with _async_session_factory() as session:
        result = await session.execute(
            delete(Audit).where(Audit.id == audit_id)
        )
        await session.commit()
        return result.rowcount > 0


# ============================================================================
# Webhook operations
# ============================================================================

async def log_webhook(
    audit_id: str,
    url: str,
    status_code: Optional[int] = None,
    success: bool = False,
    error: Optional[str] = None,
) -> WebhookLog:
    """Log a webhook delivery attempt."""
    from . import _async_session_factory

    async with _async_session_factory() as session:
        log = WebhookLog(
            id=generate_id("whk"),
            audit_id=audit_id,
            url=url,
            status_code=status_code,
            success=success,
            error=error,
        )
        session.add(log)
        await session.commit()

        # Re-fetch
        result = await session.execute(
            select(WebhookLog).where(WebhookLog.id == log.id)
        )
        return result.scalar_one()
