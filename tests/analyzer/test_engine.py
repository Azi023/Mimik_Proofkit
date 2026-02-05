"""Tests for the rule engine."""

import pytest

from proofkit.analyzer.engine import RuleEngine
from proofkit.schemas.finding import Finding, Severity
from proofkit.schemas.business import BusinessType


class TestRuleEngine:
    def test_analyze_returns_findings_and_scores(self, sample_raw_data):
        """Test that analyze returns both findings and scores."""
        engine = RuleEngine()
        findings, scores = engine.analyze(sample_raw_data)

        assert isinstance(findings, list)
        assert isinstance(scores, dict)
        assert "OVERALL" in scores

    def test_analyze_with_business_type(self, sample_raw_data):
        """Test analysis with explicit business type."""
        engine = RuleEngine()
        findings, scores = engine.analyze(
            sample_raw_data,
            business_type=BusinessType.AGENCY,
        )

        # Should include business logic findings
        assert isinstance(findings, list)

    def test_analyze_auto_detect(self, sample_raw_data):
        """Test auto-detection of business type."""
        engine = RuleEngine()
        # sample_raw_data has detected_type="agency"
        findings, scores = engine.analyze(sample_raw_data, auto_detect=True)

        assert isinstance(findings, list)

    def test_findings_sorted_by_severity(self, poor_raw_data):
        """Test that findings are sorted by severity (P0 first)."""
        engine = RuleEngine()
        findings, _ = engine.analyze(poor_raw_data)

        if len(findings) > 1:
            severities = [
                f.severity.value if hasattr(f.severity, "value") else f.severity
                for f in findings
            ]
            # Check that P0s come before P1s, P1s before P2s, etc.
            severity_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
            for i in range(len(severities) - 1):
                current = severity_order.get(severities[i], 99)
                next_sev = severity_order.get(severities[i + 1], 99)
                assert current <= next_sev


class TestCategoryAnalysis:
    def test_analyze_single_category(self, sample_raw_data):
        """Test analyzing a single category."""
        engine = RuleEngine()
        findings = engine.analyze_category(sample_raw_data, "seo")

        # All findings should be SEO category
        for finding in findings:
            cat = finding.category
            if hasattr(cat, "value"):
                cat = cat.value
            assert cat == "SEO"

    def test_analyze_unknown_category(self, sample_raw_data):
        """Test analyzing unknown category returns empty list."""
        engine = RuleEngine()
        findings = engine.analyze_category(sample_raw_data, "unknown")

        assert findings == []


class TestQuickWins:
    def test_get_quick_wins(self, sample_raw_data):
        """Test getting quick wins."""
        engine = RuleEngine()
        findings, _ = engine.analyze(sample_raw_data)
        quick_wins = engine.get_quick_wins(findings)

        for finding in quick_wins:
            severity = finding.severity
            if hasattr(severity, "value"):
                severity = severity.value
            effort = finding.effort
            if hasattr(effort, "value"):
                effort = effort.value

            assert severity in ("P0", "P1")
            assert effort == "S"


class TestCriticalFindings:
    def test_get_critical_findings(self, poor_raw_data):
        """Test getting critical findings from poor data."""
        engine = RuleEngine()
        findings, _ = engine.analyze(poor_raw_data)
        critical = engine.get_critical_findings(findings)

        for finding in critical:
            severity = finding.severity
            if hasattr(severity, "value"):
                severity = severity.value
            assert severity == "P0"


class TestGroupByCategory:
    def test_group_by_category(self, sample_raw_data):
        """Test grouping findings by category."""
        engine = RuleEngine()
        findings, _ = engine.analyze(sample_raw_data)
        grouped = engine.group_by_category(findings)

        # Each group should only contain findings of that category
        for category, category_findings in grouped.items():
            for finding in category_findings:
                cat = finding.category
                if hasattr(cat, "value"):
                    cat = cat.value
                assert cat == category


class TestPoorDataAnalysis:
    def test_poor_data_generates_many_findings(self, poor_raw_data):
        """Test that poor data generates many findings."""
        engine = RuleEngine()
        findings, scores = engine.analyze(poor_raw_data)

        # Should have multiple findings
        assert len(findings) > 5

        # Overall score should be low
        assert scores["OVERALL"] < 70

    def test_poor_data_has_critical_findings(self, poor_raw_data):
        """Test that poor data has critical findings."""
        engine = RuleEngine()
        findings, _ = engine.analyze(poor_raw_data)
        critical = engine.get_critical_findings(findings)

        # Should have at least one critical finding (missing HTTPS, title, etc.)
        assert len(critical) > 0
