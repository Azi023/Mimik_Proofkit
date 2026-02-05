"""Rule engine for orchestrating analyzer rules."""

from typing import List, Dict, Optional, Type

from proofkit.schemas.finding import Finding
from proofkit.schemas.business import BusinessType
from proofkit.collector.models import RawData
from proofkit.utils.logger import logger

from .rules.base import BaseRule
from .rules.conversion import ConversionRules
from .rules.performance import PerformanceRules
from .rules.seo import SEORules
from .rules.security import SecurityRules
from .rules.ux import UXRules
from .rules.business_logic import BusinessLogicRules
from .rules.dom_quality import DOMQualityRules
from .rules.text_quality import TextQualityRules
from .rules.visual_qa import VisualQARules
from .scoring import ScoreCalculator


class RuleEngine:
    """
    Orchestrates execution of all analyzer rules.
    """

    # All available rule classes
    RULE_CLASSES: List[Type[BaseRule]] = [
        ConversionRules,
        PerformanceRules,
        SEORules,
        SecurityRules,
        UXRules,
        BusinessLogicRules,
        # Phase 4 additions
        DOMQualityRules,
        TextQualityRules,
        VisualQARules,  # Optional - requires vision API
    ]

    def __init__(self):
        self.scorer = ScoreCalculator()

    def analyze(
        self,
        raw_data: RawData,
        business_type: Optional[BusinessType] = None,
        auto_detect: bool = True,
    ) -> tuple[List[Finding], Dict[str, int]]:
        """
        Run all rules and return findings with scores.

        Args:
            raw_data: Raw data from collectors
            business_type: Optional business type for context
            auto_detect: Whether to use auto-detected business type

        Returns:
            Tuple of (findings list, scores dict)
        """
        # Determine business type
        if business_type is None and auto_detect:
            detected = raw_data.business_signals.detected_type
            if detected:
                try:
                    business_type = BusinessType(detected)
                    logger.info(f"Using auto-detected business type: {business_type.value}")
                except ValueError:
                    pass

        # Run all rules
        all_findings: List[Finding] = []

        for rule_class in self.RULE_CLASSES:
            try:
                rule = rule_class(raw_data, business_type)
                findings = rule.run()
                all_findings.extend(findings)
                logger.debug(f"{rule_class.__name__}: {len(findings)} findings")
            except Exception as e:
                logger.error(f"Rule {rule_class.__name__} failed: {e}")

        # Sort findings by severity
        severity_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
        all_findings.sort(
            key=lambda f: severity_order.get(
                f.severity.value if hasattr(f.severity, "value") else f.severity,
                99
            )
        )

        # Calculate scores
        scores = self.scorer.calculate(all_findings)

        logger.info(f"Analysis complete: {len(all_findings)} findings, overall score: {scores.get('OVERALL', 0)}")

        return all_findings, scores

    def analyze_category(
        self,
        raw_data: RawData,
        category: str,
        business_type: Optional[BusinessType] = None,
    ) -> List[Finding]:
        """
        Run rules for a specific category only.

        Args:
            raw_data: Raw data from collectors
            category: Category name to analyze
            business_type: Optional business type

        Returns:
            List of findings for that category
        """
        category_lower = category.lower()

        # Map category to rule class
        category_map = {
            "conversion": ConversionRules,
            "performance": PerformanceRules,
            "seo": SEORules,
            "security": SecurityRules,
            "ux": UXRules,
            "business_logic": BusinessLogicRules,
            "dom_quality": DOMQualityRules,
            "text_quality": TextQualityRules,
            "visual_qa": VisualQARules,
            "maintenance": DOMQualityRules,  # Alias
        }

        rule_class = category_map.get(category_lower)
        if not rule_class:
            logger.warning(f"Unknown category: {category}")
            return []

        rule = rule_class(raw_data, business_type)
        return rule.run()

    def get_quick_wins(self, findings: List[Finding]) -> List[Finding]:
        """
        Get high-impact, low-effort findings.

        Args:
            findings: List of all findings

        Returns:
            Filtered list of quick wins (P0/P1 with effort S)
        """
        quick_wins = []

        for finding in findings:
            severity = finding.severity
            if hasattr(severity, "value"):
                severity = severity.value

            effort = finding.effort
            if hasattr(effort, "value"):
                effort = effort.value

            if severity in ("P0", "P1") and effort == "S":
                quick_wins.append(finding)

        return quick_wins

    def get_critical_findings(self, findings: List[Finding]) -> List[Finding]:
        """
        Get all critical (P0) findings.

        Args:
            findings: List of all findings

        Returns:
            Filtered list of critical findings
        """
        critical = []

        for finding in findings:
            severity = finding.severity
            if hasattr(severity, "value"):
                severity = severity.value

            if severity == "P0":
                critical.append(finding)

        return critical

    def group_by_category(self, findings: List[Finding]) -> Dict[str, List[Finding]]:
        """
        Group findings by category.

        Args:
            findings: List of all findings

        Returns:
            Dict mapping category name to findings list
        """
        grouped: Dict[str, List[Finding]] = {}

        for finding in findings:
            category = finding.category
            if hasattr(category, "value"):
                category = category.value

            if category not in grouped:
                grouped[category] = []
            grouped[category].append(finding)

        return grouped
