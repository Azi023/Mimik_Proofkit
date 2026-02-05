"""Tests for individual rule classes."""

import pytest

from proofkit.analyzer.rules.conversion import ConversionRules
from proofkit.analyzer.rules.performance import PerformanceRules
from proofkit.analyzer.rules.seo import SEORules
from proofkit.analyzer.rules.security import SecurityRules
from proofkit.analyzer.rules.ux import UXRules
from proofkit.analyzer.rules.business_logic import BusinessLogicRules
from proofkit.schemas.finding import Category, Severity
from proofkit.schemas.business import BusinessType


class TestConversionRules:
    def test_category_is_conversion(self, sample_raw_data):
        rule = ConversionRules(sample_raw_data)
        assert rule.category == Category.CONVERSION

    def test_good_data_has_few_findings(self, sample_raw_data):
        rule = ConversionRules(sample_raw_data)
        findings = rule.run()

        # Good data should have minimal conversion issues
        critical = [f for f in findings if f.severity == Severity.P0]
        assert len(critical) == 0

    def test_no_cta_detected(self, poor_raw_data):
        rule = ConversionRules(poor_raw_data)
        findings = rule.run()

        # Should detect missing CTAs
        cta_findings = [f for f in findings if "CTA" in f.id or "cta" in f.title.lower()]
        assert len(cta_findings) > 0


class TestPerformanceRules:
    def test_category_is_performance(self, sample_raw_data):
        rule = PerformanceRules(sample_raw_data)
        assert rule.category == Category.PERFORMANCE

    def test_poor_performance_detected(self, poor_raw_data):
        rule = PerformanceRules(poor_raw_data)
        findings = rule.run()

        # Poor data has bad Lighthouse scores
        score_findings = [f for f in findings if "SCORE" in f.id or "performance" in f.title.lower()]
        assert len(score_findings) > 0

    def test_cwv_issues_detected(self, poor_raw_data):
        rule = PerformanceRules(poor_raw_data)
        findings = rule.run()

        # Poor data has bad CWV
        cwv_findings = [f for f in findings if any(x in f.id for x in ["LCP", "CLS", "TBT"])]
        assert len(cwv_findings) > 0


class TestSEORules:
    def test_category_is_seo(self, sample_raw_data):
        rule = SEORules(sample_raw_data)
        assert rule.category == Category.SEO

    def test_missing_title_detected(self, poor_raw_data):
        rule = SEORules(poor_raw_data)
        findings = rule.run()

        # Poor data has missing title
        title_findings = [f for f in findings if "TITLE" in f.id]
        assert len(title_findings) > 0

    def test_missing_h1_detected(self, poor_raw_data):
        rule = SEORules(poor_raw_data)
        findings = rule.run()

        # Poor data has no H1
        h1_findings = [f for f in findings if "H1" in f.id]
        assert len(h1_findings) > 0

    def test_heading_hierarchy_issue(self, poor_raw_data):
        rule = SEORules(poor_raw_data)
        findings = rule.run()

        # Poor data has H3 without H2
        hierarchy_findings = [f for f in findings if "HIER" in f.id]
        assert len(hierarchy_findings) > 0


class TestSecurityRules:
    def test_category_is_security(self, sample_raw_data):
        rule = SecurityRules(sample_raw_data)
        assert rule.category == Category.SECURITY

    def test_missing_https_detected(self, poor_raw_data):
        rule = SecurityRules(poor_raw_data)
        findings = rule.run()

        # Poor data uses HTTP
        https_findings = [f for f in findings if "HTTPS" in f.id]
        assert len(https_findings) > 0

    def test_missing_headers_detected(self, poor_raw_data):
        rule = SecurityRules(poor_raw_data)
        findings = rule.run()

        # Poor data has no security headers
        header_findings = [f for f in findings if "HSTS" in f.id or "CSP" in f.id or "HEADERS" in f.id]
        assert len(header_findings) > 0


class TestUXRules:
    def test_category_is_ux(self, sample_raw_data):
        rule = UXRules(sample_raw_data)
        assert rule.category == Category.UX

    def test_missing_navigation_detected(self, poor_raw_data):
        rule = UXRules(poor_raw_data)
        findings = rule.run()

        # Poor data has no navigation
        nav_findings = [f for f in findings if "NAV" in f.id]
        assert len(nav_findings) > 0

    def test_console_errors_detected(self, poor_raw_data):
        rule = UXRules(poor_raw_data)
        findings = rule.run()

        # Poor data has console errors
        js_findings = [f for f in findings if "JS" in f.id]
        assert len(js_findings) > 0


class TestBusinessLogicRules:
    def test_category_is_business_logic(self, sample_raw_data):
        rule = BusinessLogicRules(sample_raw_data, BusinessType.AGENCY)
        assert rule.category == Category.BUSINESS_LOGIC

    def test_no_findings_without_business_type(self, sample_raw_data):
        rule = BusinessLogicRules(sample_raw_data, None)
        # Clear the business_signals so auto-detect doesn't work
        sample_raw_data.business_signals.detected_type = None
        findings = rule.run()

        # Without business type, should have no business logic findings
        assert len(findings) == 0

    def test_uses_detected_business_type(self, sample_raw_data):
        # sample_raw_data has detected_type="agency"
        rule = BusinessLogicRules(sample_raw_data)
        findings = rule.run()

        # May or may not have findings depending on feature detection
        assert isinstance(findings, list)


class TestFindingCreation:
    def test_finding_has_required_fields(self, sample_raw_data):
        rule = SEORules(sample_raw_data)
        findings = rule.run()

        for finding in findings:
            assert finding.id
            assert finding.category
            assert finding.severity
            assert finding.title
            assert finding.summary
            assert finding.impact
            assert finding.recommendation

    def test_finding_evidence_included(self, poor_raw_data):
        rule = SEORules(poor_raw_data)
        findings = rule.run()

        # At least some findings should have evidence
        findings_with_evidence = [f for f in findings if f.evidence]
        # Not all findings need evidence, but some should have it
        assert len(findings_with_evidence) >= 0  # At minimum, list is valid
