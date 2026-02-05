"""Tests for ProofKit schemas."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from proofkit.schemas.finding import (
    Finding,
    Evidence,
    Severity,
    Category,
    Effort,
)
from proofkit.schemas.audit import (
    AuditConfig,
    AuditResult,
    AuditStatus,
    AuditMode,
)
from proofkit.schemas.business import (
    BusinessType,
    FeatureCheck,
    FeatureStatus,
    ExpectedFeatures,
    BUSINESS_FEATURES,
)
from proofkit.schemas.report import (
    Report,
    ReportMeta,
    ReportNarrative,
    ScoreBreakdown,
)


class TestSeverity:
    def test_severity_values(self):
        assert Severity.P0.value == "P0"
        assert Severity.P1.value == "P1"
        assert Severity.P2.value == "P2"
        assert Severity.P3.value == "P3"

    def test_severity_from_string(self):
        assert Severity("P0") == Severity.P0
        assert Severity("P1") == Severity.P1


class TestCategory:
    def test_all_categories_exist(self):
        expected = [
            "UX", "SEO", "PERFORMANCE", "CONVERSION",
            "SECURITY", "MAINTENANCE", "BUSINESS_LOGIC",
            "ACCESSIBILITY", "CONTENT"
        ]
        for cat in expected:
            assert hasattr(Category, cat)


class TestEvidence:
    def test_minimal_evidence(self):
        evidence = Evidence(url="https://example.com")
        assert evidence.url == "https://example.com"
        assert evidence.selector is None
        assert evidence.screenshot_path is None

    def test_full_evidence(self):
        evidence = Evidence(
            url="https://example.com/page",
            selector=".cta-button",
            screenshot_path="/path/to/screenshot.png",
            metric={"score": "45"},
            note="CTA not visible above fold",
            console_errors=["TypeError: undefined"]
        )
        assert evidence.selector == ".cta-button"
        assert evidence.console_errors == ["TypeError: undefined"]


class TestFinding:
    def test_minimal_finding(self):
        finding = Finding(
            id="UX-CTA-001",
            category=Category.UX,
            severity=Severity.P1,
            title="Missing CTA",
            summary="No clear call-to-action on homepage",
            impact="Users don't know what action to take",
            recommendation="Add prominent CTA above the fold",
        )
        assert finding.id == "UX-CTA-001"
        assert finding.effort == Effort.M  # default
        assert finding.confidence == 1.0  # default
        assert finding.evidence == []
        assert finding.tags == []

    def test_finding_with_evidence(self):
        evidence = Evidence(url="https://example.com")
        finding = Finding(
            id="SEO-H1-001",
            category=Category.SEO,
            severity=Severity.P2,
            title="Missing H1",
            summary="No H1 tag found",
            impact="Poor SEO ranking",
            recommendation="Add H1 tag",
            evidence=[evidence],
            tags=["seo", "heading"],
            confidence=0.95,
        )
        assert len(finding.evidence) == 1
        assert finding.confidence == 0.95

    def test_finding_confidence_validation(self):
        with pytest.raises(ValidationError):
            Finding(
                id="TEST-001",
                category=Category.UX,
                severity=Severity.P1,
                title="Test",
                summary="Test",
                impact="Test",
                recommendation="Test",
                confidence=1.5,  # Invalid: > 1
            )


class TestAuditConfig:
    def test_minimal_config(self):
        config = AuditConfig(url="https://example.com")
        assert config.mode == AuditMode.FAST
        assert config.business_type is None
        assert config.max_pages == 5

    def test_full_config(self):
        config = AuditConfig(
            url="https://example.com",
            mode=AuditMode.FULL,
            business_type=BusinessType.REAL_ESTATE,
            conversion_goal="Generate leads",
            generate_concept=True,
            competitor_urls=["https://competitor.com"],
            auto_detect_business=True,
            max_pages=20,
        )
        assert config.mode == AuditMode.FULL
        assert config.business_type == BusinessType.REAL_ESTATE
        assert config.max_pages == 20


class TestAuditResult:
    def test_audit_result(self):
        config = AuditConfig(url="https://example.com")
        result = AuditResult(
            audit_id="run_20260205_120000",
            config=config,
            status=AuditStatus.PENDING,
            started_at=datetime.utcnow(),
        )
        assert result.status == AuditStatus.PENDING
        assert result.completed_at is None
        assert result.finding_count == 0


class TestBusinessType:
    def test_all_business_types(self):
        expected = [
            "real_estate", "ecommerce", "saas", "hospitality",
            "restaurant", "healthcare", "agency", "other"
        ]
        for bt in expected:
            assert BusinessType(bt) is not None

    def test_business_features_mapping(self):
        assert BusinessType.REAL_ESTATE in BUSINESS_FEATURES
        features = BUSINESS_FEATURES[BusinessType.REAL_ESTATE]
        assert "property_listings" in features.must_have
        assert "whatsapp_cta" in features.should_have


class TestFeatureCheck:
    def test_feature_check(self):
        check = FeatureCheck(
            feature_name="whatsapp_cta",
            expected=True,
            found=True,
            functional=True,
            status=FeatureStatus.FOUND,
            location="header",
            accessibility="above_fold",
        )
        assert check.status == FeatureStatus.FOUND
        assert check.location == "header"


class TestReport:
    def test_report_creation(self):
        meta = ReportMeta(
            audit_id="run_20260205_120000",
            url="https://example.com",
            generated_at=datetime.utcnow(),
            proofkit_version="0.1.0",
            mode="fast",
        )
        report = Report(
            meta=meta,
            overall_score=85,
            scorecard={"UX": 90, "SEO": 80},
        )
        assert report.overall_score == 85
        assert report.scorecard["UX"] == 90

    def test_report_finding_methods(self):
        meta = ReportMeta(
            audit_id="run_20260205_120000",
            url="https://example.com",
            generated_at=datetime.utcnow(),
            proofkit_version="0.1.0",
            mode="fast",
        )
        findings = [
            Finding(
                id="UX-001",
                category=Category.UX,
                severity=Severity.P0,
                title="Critical UX",
                summary="Test",
                impact="Test",
                recommendation="Test",
                effort=Effort.S,
            ),
            Finding(
                id="SEO-001",
                category=Category.SEO,
                severity=Severity.P2,
                title="Medium SEO",
                summary="Test",
                impact="Test",
                recommendation="Test",
            ),
        ]
        report = Report(
            meta=meta,
            overall_score=75,
            findings=findings,
        )

        critical = report.get_critical_findings()
        assert len(critical) == 1
        assert critical[0].id == "UX-001"

        quick_wins = report.get_quick_wins()
        assert len(quick_wins) == 1
        assert quick_wins[0].effort == Effort.S


class TestReportNarrative:
    def test_empty_narrative(self):
        narrative = ReportNarrative()
        assert narrative.executive_summary == ""
        assert narrative.quick_wins == []
        assert narrative.lovable_concept is None

    def test_full_narrative(self):
        narrative = ReportNarrative(
            executive_summary="The website needs improvement.",
            quick_wins=["Fix CTA", "Add H1"],
            strategic_priorities=["Redesign homepage"],
            category_insights={"UX": "Poor mobile experience"},
            lovable_concept="Create a modern, responsive design...",
        )
        assert len(narrative.quick_wins) == 2
        assert "UX" in narrative.category_insights
