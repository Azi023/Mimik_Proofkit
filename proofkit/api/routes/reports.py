"""Report retrieval endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
import json

from ..models.responses import ReportResponse, FindingResponse, NarrativeResponse
from ..database.crud import get_audit
from ..auth.api_keys import get_current_user
from ..database.models import User


router = APIRouter()


@router.get("/audits/{audit_id}/report", response_model=ReportResponse)
async def get_audit_report(
    audit_id: str,
    user: User = Depends(get_current_user),
):
    """
    Get full audit report with findings and narrative.

    Only available for completed audits.
    """
    audit = await get_audit(audit_id, user.id)

    if not audit:
        raise HTTPException(
            status_code=404,
            detail=f"Audit {audit_id} not found",
        )

    if audit.status != "complete":
        raise HTTPException(
            status_code=400,
            detail=f"Audit is not complete. Current status: {audit.status}",
        )

    if not audit.report_data:
        raise HTTPException(
            status_code=404,
            detail="Report data not found",
        )

    report_data = audit.report_data

    # Build response from stored report data
    findings = [
        FindingResponse(
            id=f.get("id", ""),
            category=f.get("category", ""),
            severity=f.get("severity", ""),
            title=f.get("title", ""),
            summary=f.get("summary", ""),
            impact=f.get("impact", ""),
            recommendation=f.get("recommendation", ""),
            effort=f.get("effort", "M"),
        )
        for f in report_data.get("findings", [])
    ]

    narrative_data = report_data.get("narrative", {})
    narrative = NarrativeResponse(
        executive_summary=narrative_data.get("executive_summary", ""),
        quick_wins=narrative_data.get("quick_wins", []),
        strategic_priorities=narrative_data.get("strategic_priorities", []),
        category_insights=narrative_data.get("category_insights", {}),
    )

    return ReportResponse(
        audit_id=audit.id,
        url=audit.url,
        scorecard=audit.scorecard or {},
        findings=findings,
        narrative=narrative,
        lovable_prompt=narrative_data.get("lovable_concept"),
    )


@router.get("/audits/{audit_id}/report/json")
async def download_report_json(
    audit_id: str,
    user: User = Depends(get_current_user),
):
    """
    Download full report as JSON file.
    """
    audit = await get_audit(audit_id, user.id)

    if not audit:
        raise HTTPException(
            status_code=404,
            detail=f"Audit {audit_id} not found",
        )

    if audit.status != "complete":
        raise HTTPException(
            status_code=400,
            detail=f"Audit is not complete. Current status: {audit.status}",
        )

    if not audit.report_data:
        raise HTTPException(
            status_code=404,
            detail="Report data not found",
        )

    return JSONResponse(
        content=audit.report_data,
        headers={
            "Content-Disposition": f'attachment; filename="report_{audit_id}.json"'
        },
    )


@router.get("/audits/{audit_id}/report/pdf")
async def download_report_pdf(
    audit_id: str,
    user: User = Depends(get_current_user),
):
    """
    Download report as PDF.

    Note: PDF generation requires additional setup.
    """
    audit = await get_audit(audit_id, user.id)

    if not audit:
        raise HTTPException(
            status_code=404,
            detail=f"Audit {audit_id} not found",
        )

    if audit.status != "complete":
        raise HTTPException(
            status_code=400,
            detail=f"Audit is not complete. Current status: {audit.status}",
        )

    # Check if PDF exists
    if audit.raw_data_path:
        output_dir = Path(audit.raw_data_path).parent.parent / "out"
        pdf_path = output_dir / "report.pdf"

        if pdf_path.exists():
            return FileResponse(
                path=str(pdf_path),
                filename=f"report_{audit_id}.pdf",
                media_type="application/pdf",
            )

    raise HTTPException(
        status_code=404,
        detail="PDF report not available. Use /report/json for JSON format.",
    )


@router.get("/audits/{audit_id}/findings")
async def get_audit_findings(
    audit_id: str,
    category: str = None,
    severity: str = None,
    user: User = Depends(get_current_user),
):
    """
    Get audit findings with optional filtering.

    - **category**: Filter by category (PERFORMANCE, SEO, etc.)
    - **severity**: Filter by severity (P0, P1, P2, P3)
    """
    audit = await get_audit(audit_id, user.id)

    if not audit:
        raise HTTPException(
            status_code=404,
            detail=f"Audit {audit_id} not found",
        )

    if audit.status != "complete":
        raise HTTPException(
            status_code=400,
            detail=f"Audit is not complete. Current status: {audit.status}",
        )

    if not audit.report_data:
        raise HTTPException(
            status_code=404,
            detail="Report data not found",
        )

    findings = audit.report_data.get("findings", [])

    # Apply filters
    if category:
        findings = [f for f in findings if f.get("category", "").upper() == category.upper()]

    if severity:
        findings = [f for f in findings if f.get("severity", "").upper() == severity.upper()]

    return {
        "audit_id": audit_id,
        "total": len(findings),
        "findings": [
            FindingResponse(
                id=f.get("id", ""),
                category=f.get("category", ""),
                severity=f.get("severity", ""),
                title=f.get("title", ""),
                summary=f.get("summary", ""),
                impact=f.get("impact", ""),
                recommendation=f.get("recommendation", ""),
                effort=f.get("effort", "M"),
            )
            for f in findings
        ],
    }
