"""Background job queue for audit processing."""

import asyncio
from typing import Optional
import httpx

from proofkit.core.runner import AuditRunner
from proofkit.schemas.audit import AuditConfig, AuditMode
from proofkit.schemas.business import BusinessType
from proofkit.utils.logger import logger

from ..database.crud import update_audit_status, save_audit_results
from ..models.requests import CreateAuditRequest


async def enqueue_audit(
    audit_id: str,
    config: CreateAuditRequest,
    webhook_url: Optional[str] = None,
):
    """
    Process audit in background.

    This is a simple in-process background task. For production,
    consider using a proper job queue like Celery, ARQ, or Redis Queue.

    Args:
        audit_id: Unique audit identifier
        config: Audit configuration from request
        webhook_url: Optional URL for completion notification
    """
    try:
        # Update status to processing
        await update_audit_status(audit_id, "processing")
        logger.info(f"Starting audit {audit_id} for {config.url}")

        # Build audit config
        business_type = None
        if config.business_type:
            try:
                business_type = BusinessType(config.business_type)
            except ValueError:
                logger.warning(f"Unknown business type: {config.business_type}")

        audit_config = AuditConfig(
            url=str(config.url),
            mode=AuditMode(config.mode.value),
            business_type=business_type,
            conversion_goal=config.conversion_goal,
            generate_concept=config.generate_concept,
        )

        # Run audit synchronously in thread pool
        # (Runner uses sync code like Playwright)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: run_audit_sync(audit_config),
        )

        # Save results
        await save_audit_results(audit_id, result)
        await update_audit_status(audit_id, "complete")

        logger.info(f"Audit {audit_id} complete: {result.get('finding_count', 0)} findings")

        # Send webhook if configured
        if webhook_url:
            await send_webhook(
                webhook_url,
                audit_id,
                "complete",
                scorecard=result.get("scorecard"),
                finding_count=result.get("finding_count"),
            )

    except Exception as e:
        logger.error(f"Audit {audit_id} failed: {e}")
        await update_audit_status(audit_id, "failed", error=str(e))

        if webhook_url:
            await send_webhook(webhook_url, audit_id, "failed", error=str(e))


def run_audit_sync(config: AuditConfig) -> dict:
    """
    Run audit synchronously.

    Args:
        config: Audit configuration

    Returns:
        Dict with audit results
    """
    runner = AuditRunner(config)
    result = runner.run()

    # Convert result to dict for storage
    return {
        "audit_id": result.audit_id,
        "scorecard": result.scorecard,
        "finding_count": result.finding_count,
        "output_dir": str(result.output_dir) if result.output_dir else None,
        "status": result.status.value if hasattr(result.status, "value") else str(result.status),
    }


async def send_webhook(
    url: str,
    audit_id: str,
    status: str,
    scorecard: Optional[dict] = None,
    finding_count: Optional[int] = None,
    error: Optional[str] = None,
):
    """
    Send webhook notification.

    Args:
        url: Webhook URL
        audit_id: Audit identifier
        status: Audit status
        scorecard: Optional scorecard
        finding_count: Optional finding count
        error: Optional error message
    """
    payload = {
        "audit_id": audit_id,
        "status": status,
    }

    if scorecard:
        payload["scorecard"] = scorecard
    if finding_count is not None:
        payload["finding_count"] = finding_count
    if error:
        payload["error"] = error

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                timeout=10,
                headers={"Content-Type": "application/json"},
            )
            logger.info(f"Webhook sent to {url}: {response.status_code}")

    except httpx.TimeoutException:
        logger.warning(f"Webhook timeout for {audit_id}: {url}")
    except Exception as e:
        logger.warning(f"Webhook failed for {audit_id}: {e}")
