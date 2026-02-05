"""Audit configuration and result models."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime
from enum import Enum

from .business import BusinessType


class AuditMode(str, Enum):
    """Audit depth mode."""
    FAST = "fast"    # Homepage + key pages only
    FULL = "full"    # Crawl up to max pages


class AuditStatus(str, Enum):
    """Audit execution status."""
    PENDING = "pending"
    COLLECTING = "collecting"
    ANALYZING = "analyzing"
    NARRATING = "narrating"
    COMPLETE = "complete"
    FAILED = "failed"


class AuditConfig(BaseModel):
    """Configuration for an audit run."""
    url: str
    mode: AuditMode = AuditMode.FAST
    business_type: Optional[BusinessType] = None
    conversion_goal: Optional[str] = None
    output_dir: Optional[Path] = None
    generate_concept: bool = False
    competitor_urls: List[str] = []
    auto_detect_business: bool = False
    max_pages: int = Field(5, description="Max pages for fast mode")
    timeout: int = Field(60000, description="Playwright timeout in ms")

    model_config = {"use_enum_values": True}


class AuditResult(BaseModel):
    """Result of an audit run."""
    audit_id: str
    config: AuditConfig
    status: AuditStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    output_dir: Optional[Path] = None
    scorecard: Dict[str, int] = {}
    finding_count: int = 0
    error: Optional[str] = None

    model_config = {"use_enum_values": True, "arbitrary_types_allowed": True}
