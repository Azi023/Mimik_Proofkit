"""Tests for score calculation."""

import pytest

from proofkit.analyzer.scoring import ScoreCalculator
from proofkit.schemas.finding import Finding, Severity, Category, Effort


@pytest.fixture
def calculator():
    return ScoreCalculator()


class TestScoreCalculator:
    def test_empty_findings(self, calculator):
        """Test scoring with no findings."""
        scores = calculator.calculate([])

        # All categories should have perfect score
        assert scores.get("PERFORMANCE") == 100
        assert scores.get("SEO") == 100
        assert scores.get("CONVERSION") == 100
        assert scores.get("OVERALL") == 100

    def test_single_p0_finding(self, calculator):
        """Test impact of a single P0 finding."""
        findings = [
            Finding(
                id="TEST-001",
                category=Category.PERFORMANCE,
                severity=Severity.P0,
                title="Test",
                summary="Test",
                impact="Test",
                recommendation="Test",
            )
        ]
        scores = calculator.calculate(findings)

        # P0 deducts 25 points
        assert scores["PERFORMANCE"] == 75
        # Other categories unaffected
        assert scores["SEO"] == 100

    def test_multiple_findings_same_category(self, calculator):
        """Test multiple findings in same category."""
        findings = [
            Finding(
                id="TEST-001",
                category=Category.SEO,
                severity=Severity.P1,
                title="Test 1",
                summary="Test",
                impact="Test",
                recommendation="Test",
            ),
            Finding(
                id="TEST-002",
                category=Category.SEO,
                severity=Severity.P2,
                title="Test 2",
                summary="Test",
                impact="Test",
                recommendation="Test",
            ),
        ]
        scores = calculator.calculate(findings)

        # P1 = 15, P2 = 8, total = 23 deducted
        assert scores["SEO"] == 77

    def test_severity_impact(self, calculator):
        """Test different severity levels have correct impact."""
        for severity, expected_impact in [
            (Severity.P0, 75),   # 100 - 25
            (Severity.P1, 85),   # 100 - 15
            (Severity.P2, 92),   # 100 - 8
            (Severity.P3, 97),   # 100 - 3
        ]:
            findings = [
                Finding(
                    id=f"TEST-{severity.value}",
                    category=Category.UX,
                    severity=severity,
                    title="Test",
                    summary="Test",
                    impact="Test",
                    recommendation="Test",
                )
            ]
            scores = calculator.calculate(findings)
            assert scores["UX"] == expected_impact

    def test_confidence_affects_score(self, calculator):
        """Test that confidence factor affects score impact."""
        # Full confidence
        findings_full = [
            Finding(
                id="TEST-001",
                category=Category.CONVERSION,
                severity=Severity.P1,
                title="Test",
                summary="Test",
                impact="Test",
                recommendation="Test",
                confidence=1.0,
            )
        ]
        scores_full = calculator.calculate(findings_full)

        # Half confidence
        findings_half = [
            Finding(
                id="TEST-001",
                category=Category.CONVERSION,
                severity=Severity.P1,
                title="Test",
                summary="Test",
                impact="Test",
                recommendation="Test",
                confidence=0.5,
            )
        ]
        scores_half = calculator.calculate(findings_half)

        # Half confidence should have less impact
        assert scores_half["CONVERSION"] > scores_full["CONVERSION"]

    def test_score_floor_at_zero(self, calculator):
        """Test that scores don't go below zero."""
        # Create many severe findings
        findings = [
            Finding(
                id=f"TEST-{i}",
                category=Category.SECURITY,
                severity=Severity.P0,
                title=f"Test {i}",
                summary="Test",
                impact="Test",
                recommendation="Test",
            )
            for i in range(10)  # 10 P0s = 250 points deducted
        ]
        scores = calculator.calculate(findings)

        assert scores["SECURITY"] == 0  # Capped at 0

    def test_overall_score_weighted(self, calculator):
        """Test that overall score uses weights."""
        findings = [
            Finding(
                id="TEST-001",
                category=Category.PERFORMANCE,
                severity=Severity.P0,
                title="Test",
                summary="Test",
                impact="Test",
                recommendation="Test",
            )
        ]
        scores = calculator.calculate(findings)

        # Overall should be weighted average, not simple average
        # Performance weight is 0.25
        overall = scores["OVERALL"]
        assert overall > 50  # Because only one category affected


class TestGrade:
    def test_grades(self, calculator):
        assert calculator.get_grade(95) == "A"
        assert calculator.get_grade(90) == "A"
        assert calculator.get_grade(85) == "B"
        assert calculator.get_grade(80) == "B"
        assert calculator.get_grade(75) == "C"
        assert calculator.get_grade(70) == "C"
        assert calculator.get_grade(65) == "D"
        assert calculator.get_grade(60) == "D"
        assert calculator.get_grade(55) == "F"
        assert calculator.get_grade(0) == "F"


class TestSummary:
    def test_summary(self, calculator):
        findings = [
            Finding(
                id="TEST-001",
                category=Category.SEO,
                severity=Severity.P0,
                title="Critical",
                summary="Test",
                impact="Test",
                recommendation="Test",
            ),
            Finding(
                id="TEST-002",
                category=Category.SEO,
                severity=Severity.P1,
                title="High",
                summary="Test",
                impact="Test",
                recommendation="Test",
            ),
            Finding(
                id="TEST-003",
                category=Category.PERFORMANCE,
                severity=Severity.P2,
                title="Medium",
                summary="Test",
                impact="Test",
                recommendation="Test",
            ),
        ]

        summary = calculator.get_summary(findings)

        assert summary["total"] == 3
        assert summary["critical"] == 1
        assert summary["high"] == 1
        assert summary["medium"] == 1
        assert summary["low"] == 0
        assert summary["by_category"]["SEO"] == 2
        assert summary["by_category"]["PERFORMANCE"] == 1
