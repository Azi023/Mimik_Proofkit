"""Analyzer module for ProofKit - rule-based analysis of collected data."""

from typing import List, Dict, Optional

from proofkit.schemas.finding import Finding
from proofkit.schemas.business import BusinessType
from proofkit.collector.models import RawData
from proofkit.utils.logger import logger

from .engine import RuleEngine
from .scoring import ScoreCalculator
from .deduplication import deduplicate_findings, deduplicate_with_stats, FindingDeduplicator
from .impact_scorer import (
    score_by_business_impact,
    get_top_findings,
    BusinessImpactScorer,
    ScoredFinding,
    ImpactCategory,
)


class Analyzer:
    """
    Main analyzer class that processes raw data and produces findings.

    This is the primary interface for the analyzer module, used by the
    core runner to analyze collected data.
    """

    def __init__(self):
        self.engine = RuleEngine()
        self.scorer = ScoreCalculator()

    def analyze(
        self,
        raw_data: RawData,
        business_type: Optional[BusinessType] = None,
        auto_detect: bool = True,
        deduplicate: bool = True,
    ) -> List[Finding]:
        """
        Analyze raw data and return findings.

        Args:
            raw_data: Raw data from collectors
            business_type: Optional business type for context-aware rules
            auto_detect: Whether to use auto-detected business type
            deduplicate: Whether to deduplicate findings (default True)

        Returns:
            List of Finding objects sorted by severity
        """
        logger.info(f"Starting analysis for {raw_data.url}")

        findings, scores = self.engine.analyze(
            raw_data=raw_data,
            business_type=business_type,
            auto_detect=auto_detect,
        )

        raw_count = len(findings)

        # Apply deduplication if enabled
        if deduplicate:
            findings, stats = deduplicate_with_stats(findings)
            logger.info(
                f"Analysis complete: {raw_count} raw findings → {len(findings)} after deduplication"
            )
        else:
            logger.info(f"Analysis complete: {len(findings)} findings")

        return findings

    def analyze_with_scores(
        self,
        raw_data: RawData,
        business_type: Optional[BusinessType] = None,
        auto_detect: bool = True,
        deduplicate: bool = True,
    ) -> tuple[List[Finding], Dict[str, int]]:
        """
        Analyze raw data and return findings with scores.

        Args:
            raw_data: Raw data from collectors
            business_type: Optional business type for context-aware rules
            auto_detect: Whether to use auto-detected business type
            deduplicate: Whether to deduplicate findings (default True)

        Returns:
            Tuple of (findings list, scores dict)
        """
        findings, scores = self.engine.analyze(
            raw_data=raw_data,
            business_type=business_type,
            auto_detect=auto_detect,
        )

        # Apply deduplication if enabled
        if deduplicate:
            findings = deduplicate_findings(findings)
            # Recalculate scores with deduplicated findings
            scores = self.scorer.calculate(findings)

        return findings, scores

    def analyze_prioritized(
        self,
        raw_data: RawData,
        business_type: Optional[BusinessType] = None,
        auto_detect: bool = True,
        top_n: int = 50,
    ) -> List[ScoredFinding]:
        """
        Analyze and return findings prioritized by business impact.

        This is the recommended method for generating client-ready reports.
        It deduplicates findings and scores them by business impact.

        Args:
            raw_data: Raw data from collectors
            business_type: Optional business type for context-aware rules
            auto_detect: Whether to use auto-detected business type
            top_n: Maximum number of findings to return

        Returns:
            List of ScoredFinding objects sorted by business impact
        """
        # Get deduplicated findings
        findings = self.analyze(
            raw_data=raw_data,
            business_type=business_type,
            auto_detect=auto_detect,
            deduplicate=True,
        )

        # Get business type string for scorer
        bt_str = None
        if business_type:
            bt_str = business_type.value if hasattr(business_type, 'value') else str(business_type)
        elif auto_detect and raw_data.business_signals.detected_type:
            bt_str = raw_data.business_signals.detected_type

        # Score and prioritize
        scored = score_by_business_impact(findings, bt_str)

        logger.info(f"Prioritized {len(scored)} findings by business impact")

        return scored[:top_n]

    def get_scores(self, findings: List[Finding]) -> Dict[str, int]:
        """
        Calculate scores from findings.

        Args:
            findings: List of findings

        Returns:
            Dict mapping category to score (0-100)
        """
        return self.scorer.calculate(findings)

    def get_summary(self, findings: List[Finding]) -> Dict[str, any]:
        """
        Get summary statistics from findings.

        Args:
            findings: List of findings

        Returns:
            Dict with counts by severity and category
        """
        return self.scorer.get_summary(findings)

    def get_quick_wins(self, findings: List[Finding]) -> List[Finding]:
        """
        Get high-impact, low-effort findings.

        Args:
            findings: List of findings

        Returns:
            Filtered list of quick wins
        """
        return self.engine.get_quick_wins(findings)

    def get_critical_findings(self, findings: List[Finding]) -> List[Finding]:
        """
        Get all critical (P0) findings.

        Args:
            findings: List of findings

        Returns:
            Filtered list of critical findings
        """
        return self.engine.get_critical_findings(findings)


# Export main classes
__all__ = [
    "Analyzer",
    "RuleEngine",
    "ScoreCalculator",
    # Deduplication
    "FindingDeduplicator",
    "deduplicate_findings",
    "deduplicate_with_stats",
    # Business Impact Scoring
    "BusinessImpactScorer",
    "ScoredFinding",
    "ImpactCategory",
    "score_by_business_impact",
    "get_top_findings",
]
