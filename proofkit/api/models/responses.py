"""API response models."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class AuditResponse(BaseModel):
    """Response model for audit status and summary."""
    audit_id: str = Field(..., description="Unique audit identifier")
    status: str = Field(
        ...,
        description="Audit status: queued, processing, complete, failed",
    )
    url: Optional[str] = Field(None, description="Audited URL")
    estimated_time_seconds: Optional[int] = Field(
        None,
        description="Estimated time to completion (for queued audits)",
    )
    created_at: datetime = Field(..., description="Audit creation timestamp")
    completed_at: Optional[datetime] = Field(
        None,
        description="Audit completion timestamp",
    )
    scorecard: Optional[Dict[str, int]] = Field(
        None,
        description="Category scores (0-100)",
    )
    finding_count: Optional[int] = Field(
        None,
        description="Total number of findings",
    )
    report_url: Optional[str] = Field(
        None,
        description="URL to retrieve full report",
    )
    error: Optional[str] = Field(
        None,
        description="Error message if audit failed",
    )

    model_config = {"from_attributes": True}


class AuditListResponse(BaseModel):
    """Response model for listing audits."""
    audits: List[AuditResponse] = Field(..., description="List of audits")
    total: int = Field(..., description="Total number of audits")
    limit: int = Field(..., description="Number of results returned")
    offset: int = Field(..., description="Number of results skipped")


class FindingResponse(BaseModel):
    """Response model for a single finding."""
    id: str = Field(..., description="Finding identifier")
    category: str = Field(
        ...,
        description="Category: PERFORMANCE, SEO, CONVERSION, UX, SECURITY, etc.",
    )
    severity: str = Field(
        ...,
        description="Severity: P0 (critical), P1 (high), P2 (medium), P3 (low)",
    )
    title: str = Field(..., description="Finding title")
    summary: str = Field(..., description="Brief description")
    impact: str = Field(..., description="Business impact explanation")
    recommendation: str = Field(..., description="How to fix")
    effort: str = Field(
        ...,
        description="Effort to fix: S (small), M (medium), L (large)",
    )


class NarrativeResponse(BaseModel):
    """Response model for AI-generated narrative."""
    executive_summary: str = Field(
        ...,
        description="Business-focused summary",
    )
    quick_wins: List[str] = Field(
        default=[],
        description="High-impact, low-effort fixes",
    )
    strategic_priorities: List[str] = Field(
        default=[],
        description="Strategic improvement recommendations",
    )
    category_insights: Dict[str, str] = Field(
        default={},
        description="Brief insights by category",
    )


class ReportResponse(BaseModel):
    """Response model for full audit report."""
    audit_id: str = Field(..., description="Audit identifier")
    url: str = Field(..., description="Audited URL")
    scorecard: Dict[str, int] = Field(
        ...,
        description="Category scores (0-100)",
    )
    findings: List[FindingResponse] = Field(
        ...,
        description="All findings",
    )
    narrative: NarrativeResponse = Field(
        ...,
        description="AI-generated narrative",
    )
    lovable_prompt: Optional[str] = Field(
        None,
        description="Lovable.dev redesign prompt (if generate_concept was true)",
    )


class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")
