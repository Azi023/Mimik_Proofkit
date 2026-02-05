"""Audit management endpoints."""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from typing import Optional

from ..models.requests import CreateAuditRequest
from ..models.responses import AuditResponse, AuditListResponse
from ..jobs.queue import enqueue_audit
from ..database.crud import (
    get_audit,
    list_audits,
    create_audit_record,
    delete_audit,
)
from ..auth.api_keys import get_current_user
from ..database.models import User


router = APIRouter()


@router.post("/audits", response_model=AuditResponse, status_code=201)
async def create_audit(
    request: CreateAuditRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
):
    """
    Create a new website audit.

    The audit runs asynchronously in the background. Use the returned
    audit_id to check status and retrieve results.

    - **url**: Website URL to audit (must include protocol)
    - **mode**: Audit depth - "fast" (homepage only) or "full" (crawl site)
    - **business_type**: Optional business category for tailored analysis
    - **conversion_goal**: Primary conversion goal for context
    - **generate_concept**: Whether to generate Lovable redesign prompts
    - **webhook_url**: URL to receive completion notification
    """
    # Create audit record in database
    audit = await create_audit_record(
        url=str(request.url),
        mode=request.mode.value,
        business_type=request.business_type,
        conversion_goal=request.conversion_goal,
        generate_concept=request.generate_concept,
        user_id=user.id,
    )

    # Enqueue for background processing
    background_tasks.add_task(
        enqueue_audit,
        audit_id=audit.id,
        config=request,
        webhook_url=str(request.webhook_url) if request.webhook_url else None,
    )

    # Estimate processing time based on mode
    estimated_time = 180 if request.mode.value == "full" else 60

    return AuditResponse(
        audit_id=audit.id,
        status="queued",
        url=str(request.url),
        estimated_time_seconds=estimated_time,
        created_at=audit.created_at,
    )


@router.get("/audits/{audit_id}", response_model=AuditResponse)
async def get_audit_status(
    audit_id: str,
    user: User = Depends(get_current_user),
):
    """
    Get audit status and summary.

    Returns current status, scorecard (if complete), and finding count.
    """
    audit = await get_audit(audit_id, user.id)

    if not audit:
        raise HTTPException(
            status_code=404,
            detail=f"Audit {audit_id} not found",
        )

    return AuditResponse(
        audit_id=audit.id,
        status=audit.status,
        url=audit.url,
        created_at=audit.created_at,
        completed_at=audit.completed_at,
        scorecard=audit.scorecard,
        finding_count=audit.finding_count,
        report_url=f"/v1/audits/{audit.id}/report" if audit.status == "complete" else None,
        error=audit.error,
    )


@router.get("/audits", response_model=AuditListResponse)
async def list_user_audits(
    limit: int = Query(20, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    status: Optional[str] = Query(None, description="Filter by status"),
    user: User = Depends(get_current_user),
):
    """
    List audits for the current user.

    Supports pagination and filtering by status.
    """
    audits, total = await list_audits(
        user_id=user.id,
        limit=limit,
        offset=offset,
        status=status,
    )

    return AuditListResponse(
        audits=[
            AuditResponse(
                audit_id=a.id,
                status=a.status,
                url=a.url,
                created_at=a.created_at,
                completed_at=a.completed_at,
                scorecard=a.scorecard,
                finding_count=a.finding_count,
                report_url=f"/v1/audits/{a.id}/report" if a.status == "complete" else None,
            )
            for a in audits
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.delete("/audits/{audit_id}", status_code=204)
async def delete_user_audit(
    audit_id: str,
    user: User = Depends(get_current_user),
):
    """
    Delete an audit and its associated data.

    This action cannot be undone.
    """
    audit = await get_audit(audit_id, user.id)

    if not audit:
        raise HTTPException(
            status_code=404,
            detail=f"Audit {audit_id} not found",
        )

    await delete_audit(audit_id)
    return None
