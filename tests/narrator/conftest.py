"""Fixtures for narrator tests."""

import pytest
from unittest.mock import MagicMock, patch

from proofkit.schemas.finding import Finding, Severity, Category, Effort
from proofkit.schemas.business import BusinessType


@pytest.fixture
def mock_claude_client():
    """Create a mock Claude client."""
    with patch("proofkit.narrator.claude_client.anthropic") as mock_anthropic:
        # Create mock response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Mock AI response")]
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50

        # Configure mock client
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.Anthropic.return_value = mock_client

        yield mock_anthropic


@pytest.fixture
def mock_config():
    """Create a mock config."""
    with patch("proofkit.narrator.claude_client.get_config") as mock_get_config:
        mock_cfg = MagicMock()
        mock_cfg.anthropic_api_key = "test-api-key"
        mock_cfg.ai_model = "claude-sonnet-4-20250514"
        mock_cfg.ai_max_tokens = 2000
        mock_cfg.templates_dir = MagicMock()
        mock_cfg.templates_dir.__truediv__ = lambda self, x: MagicMock(exists=lambda: False)
        mock_get_config.return_value = mock_cfg
        yield mock_cfg


@pytest.fixture
def sample_findings():
    """Create sample findings for testing."""
    return [
        Finding(
            id="SEO-001",
            category=Category.SEO,
            severity=Severity.P0,
            title="Missing Page Title",
            summary="The homepage is missing a title tag.",
            impact="Pages without titles perform 40% worse in search rankings.",
            recommendation="Add a descriptive title tag with primary keyword.",
            effort=Effort.S,
        ),
        Finding(
            id="PERF-001",
            category=Category.PERFORMANCE,
            severity=Severity.P1,
            title="Slow Page Load Time",
            summary="Page takes over 5 seconds to load on mobile.",
            impact="Users abandon sites that take longer than 3 seconds.",
            recommendation="Optimize images, enable compression, use CDN.",
            effort=Effort.M,
        ),
        Finding(
            id="CONV-001",
            category=Category.CONVERSION,
            severity=Severity.P1,
            title="Missing CTA Above Fold",
            summary="No clear call-to-action visible without scrolling.",
            impact="Users may leave without taking action.",
            recommendation="Add prominent CTA button in hero section.",
            effort=Effort.S,
        ),
        Finding(
            id="SEC-001",
            category=Category.SECURITY,
            severity=Severity.P0,
            title="No HTTPS",
            summary="Site is served over HTTP.",
            impact="Users see security warnings, data is not encrypted.",
            recommendation="Install SSL certificate and redirect to HTTPS.",
            effort=Effort.S,
        ),
        Finding(
            id="UX-001",
            category=Category.UX,
            severity=Severity.P2,
            title="Poor Mobile Navigation",
            summary="Hamburger menu is difficult to use on mobile.",
            impact="Mobile users struggle to navigate the site.",
            recommendation="Improve mobile menu accessibility and size.",
            effort=Effort.M,
        ),
    ]


@pytest.fixture
def mock_claude_responses():
    """Provide realistic mock responses for different prompts."""
    return {
        "executive_summary": (
            "Your website is losing potential customers due to critical technical issues. "
            "The absence of HTTPS and missing page titles are damaging search rankings and "
            "eroding user trust. With mobile load times exceeding 5 seconds, visitors are "
            "abandoning your site before seeing your value proposition. These issues represent "
            "a significant opportunity - addressing them could dramatically improve both traffic and conversion."
        ),
        "quick_wins": """- Install SSL certificate and enable HTTPS (2 hours, critical security fix)
- Add page title with target keywords (30 minutes, high SEO impact)
- Add prominent CTA button to hero section (1 hour, high conversion impact)
- Compress and optimize hero images (2 hours, 2-3s faster load)
- Increase mobile menu touch target size (1 hour, better UX)""",
        "strategic_priorities": """Implement comprehensive performance optimization including CDN, lazy loading, and code splitting to achieve sub-3-second load times
Develop a mobile-first redesign that prioritizes touch-friendly navigation and conversion-focused layouts
Build an SEO foundation with proper meta tags, structured data, and internal linking strategy
Create a security-first infrastructure with HSTS, CSP headers, and regular vulnerability scanning
Establish analytics and conversion tracking to measure and optimize ongoing performance""",
        "concept_bullets": """- Modern hero section with animated CTA and trust badges
- Mobile-optimized navigation with bottom sheet menu
- Lazy-loaded image gallery with WebP format support
- Sticky header with prominent contact options
- Performance-optimized design with minimal JavaScript""",
        "lovable_prompt": (
            "Create a modern, professional business website with a clean, minimalist aesthetic. "
            "The homepage should feature a full-width hero section with a compelling headline, "
            "subtext, and a prominent CTA button. Include a sticky header with logo and navigation, "
            "transitioning to a hamburger menu on mobile with large touch targets. Use a card-based "
            "layout for services/features with icons. Include a testimonials section and a simple "
            "contact form. Design for mobile-first with a color scheme of deep blue and white with "
            "orange accents for CTAs. Ensure all images are optimized with lazy loading."
        ),
    }
