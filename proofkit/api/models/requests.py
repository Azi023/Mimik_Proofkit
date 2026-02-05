"""API request models."""

from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List
from enum import Enum


class AuditMode(str, Enum):
    """Audit depth mode."""
    FAST = "fast"
    FULL = "full"


class CreateAuditRequest(BaseModel):
    """Request model for creating a new audit."""
    url: HttpUrl = Field(
        ...,
        description="Website URL to audit (must include protocol)",
        examples=["https://example.com"],
    )
    mode: AuditMode = Field(
        default=AuditMode.FAST,
        description="Audit depth: 'fast' (homepage only) or 'full' (crawl site)",
    )
    business_type: Optional[str] = Field(
        default=None,
        description="Business category for tailored analysis",
        examples=["real_estate", "ecommerce", "saas", "hospitality"],
    )
    conversion_goal: Optional[str] = Field(
        default=None,
        description="Primary conversion goal",
        examples=["property inquiries", "online purchases", "demo requests"],
    )
    generate_concept: bool = Field(
        default=False,
        description="Whether to generate Lovable redesign prompts",
    )
    competitor_urls: List[str] = Field(
        default=[],
        description="Competitor URLs for comparison (future feature)",
    )
    webhook_url: Optional[HttpUrl] = Field(
        default=None,
        description="URL to receive completion notification",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "url": "https://example.com",
                "mode": "fast",
                "business_type": "real_estate",
                "conversion_goal": "property inquiries",
                "generate_concept": True,
            }
        }
    }


class WebhookPayload(BaseModel):
    """Webhook notification payload."""
    audit_id: str
    status: str
    url: str
    scorecard: Optional[dict] = None
    finding_count: Optional[int] = None
    error: Optional[str] = None
