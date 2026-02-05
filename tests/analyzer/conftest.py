"""Fixtures for analyzer tests."""

import pytest

from proofkit.collector.models import (
    RawData,
    SnapshotData,
    PageSnapshot,
    CTAInfo,
    FormInfo,
    NavigationInfo,
    LighthouseData,
    LighthouseScores,
    CoreWebVitals,
    LighthouseOpportunity,
    HttpProbeData,
    SecurityHeaders,
    SSLInfo,
    StackInfo,
    BusinessSignals,
)


@pytest.fixture
def sample_raw_data():
    """Create sample raw data for testing."""
    return RawData(
        url="https://example.com",
        mode="fast",
        pages_audited=["https://example.com"],
        snapshot=SnapshotData(
            url="https://example.com",
            pages=[
                PageSnapshot(
                    url="https://example.com",
                    title="Example Website - Home",
                    headings={
                        "h1": ["Welcome to Example"],
                        "h2": ["Our Services", "Contact Us"],
                        "h3": [],
                    },
                    ctas=[
                        CTAInfo(text="Contact Us", type="link", is_visible=True, is_above_fold=True),
                        CTAInfo(text="Learn More", type="button", is_visible=True, is_above_fold=False),
                    ],
                    mobile_ctas=[
                        CTAInfo(text="Contact Us", type="link", is_visible=True, is_above_fold=True),
                    ],
                    forms=[
                        FormInfo(
                            action="/contact",
                            method="POST",
                            field_count=4,
                            required_count=2,
                            has_email_field=True,
                            has_phone_field=True,
                            submit_button_text="Send Message",
                        ),
                    ],
                    navigation=NavigationInfo(
                        links=[
                            {"text": "Home", "href": "/"},
                            {"text": "About", "href": "/about"},
                            {"text": "Services", "href": "/services"},
                            {"text": "Contact", "href": "/contact"},
                        ],
                        has_hamburger=True,
                        depth=2,
                    ),
                    whatsapp_links=[
                        {"text": "WhatsApp", "href": "https://wa.me/1234567890", "is_visible": True, "is_above_fold": True},
                    ],
                    contact_info={
                        "phones": ["+1 234 567 890"],
                        "emails": ["info@example.com"],
                        "has_tel_link": True,
                        "has_mailto_link": True,
                    },
                    hamburger_menu_works=True,
                    console_errors=[],
                    meta_tags={
                        "description": "Example website providing great services.",
                        "viewport": "width=device-width, initial-scale=1",
                    },
                )
            ],
            total_ctas=2,
            total_forms=1,
        ),
        lighthouse=LighthouseData(
            url="https://example.com",
            mobile_scores=LighthouseScores(
                performance=75.0,
                accessibility=88.0,
                best_practices=92.0,
                seo=85.0,
            ),
            desktop_scores=LighthouseScores(
                performance=90.0,
                accessibility=90.0,
                best_practices=95.0,
                seo=90.0,
            ),
            mobile_cwv=CoreWebVitals(
                lcp=2800.0,
                fid=120.0,
                cls=0.08,
                tbt=250.0,
                fcp=1600.0,
                ttfb=600.0,
            ),
            desktop_cwv=CoreWebVitals(
                lcp=1800.0,
                fid=80.0,
                cls=0.05,
                tbt=150.0,
                fcp=1200.0,
                ttfb=400.0,
            ),
            opportunities=[
                LighthouseOpportunity(
                    id="unused-javascript",
                    title="Remove unused JavaScript",
                    description="Reduce unused JavaScript",
                    score=0.6,
                    savings_ms=800.0,
                    display_value="Potential savings of 0.8s",
                ),
            ],
        ),
        http_probe=HttpProbeData(
            url="https://example.com",
            final_url="https://example.com",
            status_code=200,
            redirect_chain=["https://example.com"],
            response_time_ms=150.0,
            security_headers=SecurityHeaders(
                present={
                    "strict-transport-security": "max-age=31536000",
                    "x-frame-options": "SAMEORIGIN",
                },
                missing=["content-security-policy", "x-content-type-options"],
                has_hsts=True,
                has_csp=False,
                has_xframe=True,
                score=60.0,
            ),
            ssl_info=SSLInfo(
                valid=True,
                issuer="Let's Encrypt",
                expires="Dec 31 2026",
                days_until_expiry=365,
            ),
            sitemap_exists=True,
            robots_txt="User-agent: *\nAllow: /\nSitemap: https://example.com/sitemap.xml",
        ),
        detected_stack=StackInfo(
            cms=None,
            framework="react",
            analytics=["google_analytics"],
        ),
        business_signals=BusinessSignals(
            detected_type="agency",
            confidence=0.75,
        ),
    )


@pytest.fixture
def poor_raw_data():
    """Create raw data with many issues for testing."""
    return RawData(
        url="http://example.com",  # HTTP not HTTPS
        mode="fast",
        pages_audited=["http://example.com"],
        snapshot=SnapshotData(
            url="http://example.com",
            pages=[
                PageSnapshot(
                    url="http://example.com",
                    title="",  # Missing title
                    headings={"h1": [], "h2": [], "h3": ["Random H3"]},  # No H1, H3 without H2
                    ctas=[],  # No CTAs
                    mobile_ctas=[],
                    forms=[],  # No forms
                    navigation=NavigationInfo(links=[], has_hamburger=False),  # No nav
                    whatsapp_links=[],
                    contact_info={},
                    hamburger_menu_works=None,
                    console_errors=["TypeError: undefined is not a function"],
                    meta_tags={},  # Missing viewport
                )
            ],
            total_ctas=0,
            total_forms=0,
        ),
        lighthouse=LighthouseData(
            url="http://example.com",
            mobile_scores=LighthouseScores(performance=35.0),
            mobile_cwv=CoreWebVitals(
                lcp=5000.0,  # Poor LCP
                cls=0.35,    # Poor CLS
                tbt=800.0,   # Poor TBT
            ),
        ),
        http_probe=HttpProbeData(
            url="http://example.com",
            final_url="http://example.com",  # No HTTPS
            status_code=200,
            security_headers=SecurityHeaders(
                present={},
                missing=[
                    "strict-transport-security",
                    "content-security-policy",
                    "x-frame-options",
                ],
                has_hsts=False,
                has_csp=False,
                has_xframe=False,
                score=0.0,
            ),
            ssl_info=SSLInfo(valid=False, error="Not using HTTPS"),
            sitemap_exists=False,
            robots_txt=None,
        ),
        detected_stack=StackInfo(),
        business_signals=BusinessSignals(),
    )
