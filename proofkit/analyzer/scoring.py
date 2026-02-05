"""Score calculation from findings."""

from typing import List, Dict

from proofkit.schemas.finding import Finding, Category, Severity
from proofkit.utils.config import get_config


class ScoreCalculator:
    """
    Calculate category and overall scores from findings.
    """

    # Severity impact on score (points deducted per finding)
    SEVERITY_IMPACT = {
        "P0": 25,
        "P1": 15,
        "P2": 8,
        "P3": 3,
    }

    def __init__(self):
        self.config = get_config()
        self.weights = self.config.score_weights

    def calculate(self, findings: List[Finding]) -> Dict[str, int]:
        """
        Calculate scores for each category.

        Args:
            findings: List of findings from analyzer

        Returns:
            Dict of category -> score (0-100), including "OVERALL"
        """
        # Group findings by category
        by_category: Dict[str, List[Finding]] = {}
        for finding in findings:
            cat = finding.category
            if isinstance(cat, Category):
                cat = cat.value
            elif not isinstance(cat, str):
                cat = str(cat)

            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(finding)

        # Calculate score per category
        scores = {}
        for category in Category:
            cat_name = category.value
            cat_findings = by_category.get(cat_name, [])
            scores[cat_name] = self._category_score(cat_findings)

        # Calculate overall weighted score
        overall = self._overall_score(scores)
        scores["OVERALL"] = overall

        return scores

    def _category_score(self, findings: List[Finding]) -> int:
        """
        Calculate score for a single category.

        Starts at 100 and deducts points based on findings and their severity.
        """
        if not findings:
            return 100  # No findings = perfect score

        score = 100.0

        for finding in findings:
            severity = finding.severity
            if isinstance(severity, Severity):
                severity = severity.value
            elif not isinstance(severity, str):
                severity = str(severity)

            impact = self.SEVERITY_IMPACT.get(severity, 5)

            # Apply confidence factor (lower confidence = less impact)
            impact *= finding.confidence

            score -= impact

        return max(0, min(100, int(score)))

    def _overall_score(self, category_scores: Dict[str, int]) -> int:
        """
        Calculate weighted overall score.

        Uses weights from config to combine category scores.
        """
        total_weight = 0.0
        weighted_sum = 0.0

        for category, weight in self.weights.items():
            if category in category_scores:
                weighted_sum += category_scores[category] * weight
                total_weight += weight

        if total_weight == 0:
            # Fallback: simple average
            valid_scores = [s for s in category_scores.values() if s is not None]
            if valid_scores:
                return int(sum(valid_scores) / len(valid_scores))
            return 0

        return int(weighted_sum / total_weight)

    def get_grade(self, score: int) -> str:
        """
        Convert numeric score to letter grade.

        Args:
            score: Score 0-100

        Returns:
            Letter grade (A, B, C, D, F)
        """
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    def get_summary(self, findings: List[Finding]) -> Dict[str, any]:
        """
        Get summary statistics from findings.

        Args:
            findings: List of findings

        Returns:
            Dict with counts by severity and category
        """
        by_severity = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
        by_category: Dict[str, int] = {}

        for finding in findings:
            # Count by severity
            severity = finding.severity
            if isinstance(severity, Severity):
                severity = severity.value
            if severity in by_severity:
                by_severity[severity] += 1

            # Count by category
            category = finding.category
            if isinstance(category, Category):
                category = category.value
            by_category[category] = by_category.get(category, 0) + 1

        return {
            "total": len(findings),
            "critical": by_severity["P0"],
            "high": by_severity["P1"],
            "medium": by_severity["P2"],
            "low": by_severity["P3"],
            "by_severity": by_severity,
            "by_category": by_category,
        }
