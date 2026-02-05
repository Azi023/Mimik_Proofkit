"""Report and narrative models."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from .finding import Finding, Category
from .business import BusinessType


class ReportMeta(BaseModel):
    """Metadata about the audit report."""
    audit_id: str
    url: str
    business_type: Optional[BusinessType] = None
    conversion_goal: Optional[str] = None
    generated_at: datetime
    proofkit_version: str
    mode: str  # "fast" or "full"
    pages_analyzed: int = 1

    model_config = {"use_enum_values": True}


class ReportNarrative(BaseModel):
    """AI-generated narrative sections."""
    executive_summary: str = ""
    quick_wins: List[str] = []
    strategic_priorities: List[str] = []
    category_insights: Dict[str, str] = {}
    lovable_concept: Optional[str] = None  # Lovable redesign prompt


class ScoreBreakdown(BaseModel):
    """Score breakdown by category."""
    category: Category
    score: int = Field(..., ge=0, le=100)
    finding_count: int
    critical_count: int = 0
    weight: float = 0.0
    weighted_score: float = 0.0

    model_config = {"use_enum_values": True}


class Report(BaseModel):
    """Complete audit report."""
    meta: ReportMeta
    overall_score: int = Field(..., ge=0, le=100)
    scorecard: Dict[str, int] = {}  # Category -> score
    score_breakdown: List[ScoreBreakdown] = []
    findings: List[Finding] = []
    narrative: ReportNarrative = ReportNarrative()
    raw_data_paths: Dict[str, str] = {}  # collector -> file path

    def get_findings_by_category(self, category: Category) -> List[Finding]:
        """Get all findings for a specific category."""
        return [f for f in self.findings if f.category == category]

    def get_findings_by_severity(self, severity: str) -> List[Finding]:
        """Get all findings for a specific severity."""
        return [f for f in self.findings if f.severity == severity]

    def get_critical_findings(self) -> List[Finding]:
        """Get all P0 (critical) findings."""
        return self.get_findings_by_severity("P0")

    def get_quick_wins(self) -> List[Finding]:
        """Get high-impact, low-effort findings (P0/P1 with effort S)."""
        return [
            f for f in self.findings
            if f.severity in ("P0", "P1") and f.effort == "S"
        ]
