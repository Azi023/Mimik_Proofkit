"""Finding and evidence models for audit results."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from enum import Enum


class Severity(str, Enum):
    """Finding severity levels."""
    P0 = "P0"  # Critical - blocks conversion
    P1 = "P1"  # High - significant impact
    P2 = "P2"  # Medium - noticeable issue
    P3 = "P3"  # Low - minor improvement


class Effort(str, Enum):
    """Estimated fix effort."""
    S = "S"   # Small - hours
    M = "M"   # Medium - days
    L = "L"   # Large - weeks


class Category(str, Enum):
    """Finding categories."""
    UX = "UX"
    SEO = "SEO"
    PERFORMANCE = "PERFORMANCE"
    CONVERSION = "CONVERSION"
    SECURITY = "SECURITY"
    MAINTENANCE = "MAINTENANCE"
    BUSINESS_LOGIC = "BUSINESS_LOGIC"
    ACCESSIBILITY = "ACCESSIBILITY"
    CONTENT = "CONTENT"


class Evidence(BaseModel):
    """Evidence supporting a finding."""
    url: str
    selector: Optional[str] = None
    screenshot_path: Optional[str] = None
    metric: Optional[Dict[str, str]] = None
    note: Optional[str] = None
    console_errors: Optional[List[str]] = None


class Finding(BaseModel):
    """A single audit finding."""
    id: str = Field(..., description="Unique ID e.g., UX-CTA-001")
    category: Category
    severity: Severity
    title: str
    summary: str
    impact: str
    recommendation: str
    effort: Effort = Effort.M
    evidence: List[Evidence] = []
    tags: List[str] = []
    confidence: float = Field(1.0, ge=0, le=1, description="Detection confidence 0-1")

    model_config = {"use_enum_values": True}
