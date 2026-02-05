"""Tests for collector data models."""

import pytest

from proofkit.collector.models import (
    CTAInfo,
    FormInfo,
    NavigationInfo,
    PageSnapshot,
    SnapshotData,
    CoreWebVitals,
    LighthouseScores,
    LighthouseOpportunity,
    LighthouseData,
    SecurityHeaders,
    SSLInfo,
    HttpProbeData,
    StackInfo,
    BusinessSignals,
    RawData,
)


class TestCTAInfo:
    def test_minimal_cta(self):
        cta = CTAInfo(text="Click Here", type="button")
        assert cta.text == "Click Here"
        assert cta.type == "button"
        assert cta.href is None
        assert cta.is_visible is True
        assert cta.is_above_fold is False

    def test_full_cta(self):
        cta = CTAInfo(
            text="Buy Now",
            type="link",
            href="https://example.com/buy",
            is_visible=True,
            is_above_fold=True,
            selector="a.cta-button",
        )
        assert cta.href == "https://example.com/buy"
        assert cta.is_above_fold is True


class TestFormInfo:
    def test_default_form(self):
        form = FormInfo()
        assert form.method == "GET"
        assert form.field_count == 0
        assert form.has_email_field is False

    def test_contact_form(self):
        form = FormInfo(
            action="/contact",
            method="POST",
            field_count=5,
            required_count=3,
            has_email_field=True,
            has_phone_field=True,
            submit_button_text="Send Message",
        )
        assert form.method == "POST"
        assert form.has_email_field is True


class TestNavigationInfo:
    def test_empty_navigation(self):
        nav = NavigationInfo()
        assert nav.links == []
        assert nav.has_hamburger is False
        assert nav.depth == 1

    def test_navigation_with_links(self):
        nav = NavigationInfo(
            links=[
                {"text": "Home", "href": "/"},
                {"text": "About", "href": "/about"},
            ],
            has_hamburger=True,
            depth=2,
        )
        assert len(nav.links) == 2
        assert nav.has_hamburger is True


class TestPageSnapshot:
    def test_minimal_snapshot(self):
        snapshot = PageSnapshot(url="https://example.com")
        assert snapshot.url == "https://example.com"
        assert snapshot.title == ""
        assert snapshot.headings == {"h1": [], "h2": [], "h3": []}

    def test_full_snapshot(self):
        snapshot = PageSnapshot(
            url="https://example.com",
            title="Example Page",
            headings={"h1": ["Main Title"], "h2": ["Section"], "h3": []},
            ctas=[CTAInfo(text="Click", type="button")],
            forms=[FormInfo(field_count=3)],
            whatsapp_links=[{"text": "WhatsApp", "href": "https://wa.me/123"}],
            console_errors=["TypeError: undefined"],
        )
        assert snapshot.title == "Example Page"
        assert len(snapshot.ctas) == 1
        assert len(snapshot.console_errors) == 1


class TestSnapshotData:
    def test_empty_snapshot_data(self):
        data = SnapshotData(url="https://example.com")
        assert data.pages == []
        assert data.total_ctas == 0

    def test_snapshot_data_with_pages(self):
        pages = [
            PageSnapshot(url="https://example.com", ctas=[CTAInfo(text="CTA1", type="link")]),
            PageSnapshot(url="https://example.com/about", ctas=[CTAInfo(text="CTA2", type="button")]),
        ]
        data = SnapshotData(
            url="https://example.com",
            pages=pages,
            total_ctas=2,
            total_forms=0,
        )
        assert len(data.pages) == 2
        assert data.total_ctas == 2


class TestCoreWebVitals:
    def test_empty_cwv(self):
        cwv = CoreWebVitals()
        assert cwv.lcp is None
        assert cwv.cls is None

    def test_full_cwv(self):
        cwv = CoreWebVitals(
            lcp=2500.0,
            fid=100.0,
            cls=0.1,
            ttfb=500.0,
            fcp=1500.0,
        )
        assert cwv.lcp == 2500.0
        assert cwv.cls == 0.1


class TestLighthouseScores:
    def test_empty_scores(self):
        scores = LighthouseScores()
        assert scores.performance is None

    def test_full_scores(self):
        scores = LighthouseScores(
            performance=85.0,
            accessibility=92.0,
            best_practices=88.0,
            seo=95.0,
        )
        assert scores.performance == 85.0
        assert scores.seo == 95.0


class TestLighthouseOpportunity:
    def test_opportunity(self):
        opp = LighthouseOpportunity(
            id="unused-javascript",
            title="Remove unused JavaScript",
            description="Reduce unused JavaScript to speed up page load",
            score=0.45,
            savings_ms=1200.0,
            display_value="Potential savings of 1.2s",
        )
        assert opp.id == "unused-javascript"
        assert opp.savings_ms == 1200.0


class TestSecurityHeaders:
    def test_empty_security(self):
        sec = SecurityHeaders()
        assert sec.present == {}
        assert sec.missing == []
        assert sec.score == 0

    def test_partial_security(self):
        sec = SecurityHeaders(
            present={"strict-transport-security": "max-age=31536000"},
            missing=["content-security-policy", "x-frame-options"],
            has_hsts=True,
            has_csp=False,
            score=33.3,
        )
        assert sec.has_hsts is True
        assert sec.has_csp is False
        assert len(sec.missing) == 2


class TestSSLInfo:
    def test_valid_ssl(self):
        ssl = SSLInfo(
            valid=True,
            issuer="Let's Encrypt",
            expires="Dec 31 2025",
            subject="example.com",
            days_until_expiry=365,
        )
        assert ssl.valid is True
        assert ssl.issuer == "Let's Encrypt"

    def test_invalid_ssl(self):
        ssl = SSLInfo(valid=False, error="Certificate expired")
        assert ssl.valid is False
        assert ssl.error == "Certificate expired"


class TestHttpProbeData:
    def test_http_probe(self):
        probe = HttpProbeData(
            url="https://example.com",
            final_url="https://www.example.com",
            status_code=200,
            redirect_chain=["https://example.com", "https://www.example.com"],
            redirect_count=1,
            response_time_ms=150.5,
            security_headers=SecurityHeaders(score=50.0),
            sitemap_exists=True,
        )
        assert probe.status_code == 200
        assert probe.redirect_count == 1
        assert probe.sitemap_exists is True


class TestStackInfo:
    def test_empty_stack(self):
        stack = StackInfo()
        assert stack.cms is None
        assert stack.framework is None

    def test_detected_stack(self):
        stack = StackInfo(
            cms="wordpress",
            framework="react",
            analytics=["google_analytics", "facebook_pixel"],
            tag_managers=["google_tag_manager"],
            cdn="cloudflare",
        )
        assert stack.cms == "wordpress"
        assert len(stack.analytics) == 2


class TestBusinessSignals:
    def test_empty_signals(self):
        signals = BusinessSignals()
        assert signals.detected_type is None
        assert signals.confidence == 0.0

    def test_detected_signals(self):
        signals = BusinessSignals(
            detected_type="real_estate",
            confidence=0.85,
            keyword_matches={"real_estate": ["property", "bedroom", "sqft"]},
            feature_indicators=["inquiry_form", "property_search"],
            industry_signals=["local", "premium"],
        )
        assert signals.detected_type == "real_estate"
        assert signals.confidence == 0.85
        assert len(signals.feature_indicators) == 2


class TestRawData:
    def test_minimal_raw_data(self):
        data = RawData(
            url="https://example.com",
            mode="fast",
        )
        assert data.url == "https://example.com"
        assert data.mode == "fast"
        assert data.pages_audited == []

    def test_full_raw_data(self):
        data = RawData(
            url="https://example.com",
            mode="full",
            pages_audited=["https://example.com", "https://example.com/about"],
            snapshot=SnapshotData(url="https://example.com"),
            lighthouse=LighthouseData(url="https://example.com"),
            http_probe=HttpProbeData(url="https://example.com", final_url="https://example.com"),
            detected_stack=StackInfo(cms="wordpress"),
            business_signals=BusinessSignals(detected_type="agency"),
            collected_at="2026-02-05T12:00:00",
            collection_errors=["Lighthouse timed out"],
        )
        assert data.mode == "full"
        assert len(data.pages_audited) == 2
        assert data.detected_stack.cms == "wordpress"
        assert len(data.collection_errors) == 1
