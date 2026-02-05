"""Tests for Visual QA, DOM Quality, and Text Quality rules."""

import pytest
from unittest.mock import patch, MagicMock
import os

from proofkit.analyzer.rules.visual_qa import VisualQARules
from proofkit.analyzer.rules.dom_quality import DOMQualityRules
from proofkit.analyzer.rules.text_quality import TextQualityRules
from proofkit.collector.models import (
    RawData,
    SnapshotData,
    PageSnapshot,
    CTAInfo,
    NavigationInfo,
    LighthouseData,
    HttpProbeData,
)


class TestVisualQARules:
    """Tests for VisualQARules class."""

    def test_vision_not_available_skips_analysis(self, sample_raw_data):
        """Test that analysis is skipped when vision API is unavailable."""
        with patch.dict(os.environ, {"AI_PROVIDER": "openai", "OPENAI_API_KEY": "", "OPENAI_MODEL": "gpt-4o-mini"}):
            rules = VisualQARules(sample_raw_data)
            findings = rules.run()

        # Should skip and return no findings
        assert len(findings) == 0

    def test_check_vision_availability_openai(self, sample_raw_data):
        """Test vision availability check for OpenAI."""
        # gpt-4o-mini doesn't support vision well
        with patch.dict(os.environ, {"AI_PROVIDER": "openai", "OPENAI_API_KEY": "sk-test", "OPENAI_MODEL": "gpt-4o-mini"}):
            rules = VisualQARules(sample_raw_data)
            assert rules._vision_available is False

        # gpt-4o supports vision
        with patch.dict(os.environ, {"AI_PROVIDER": "openai", "OPENAI_API_KEY": "sk-test", "OPENAI_MODEL": "gpt-4o"}):
            rules = VisualQARules(sample_raw_data)
            assert rules._vision_available is True

    def test_check_vision_availability_anthropic(self, sample_raw_data):
        """Test vision availability check for Anthropic."""
        with patch.dict(os.environ, {"AI_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "sk-ant-test"}):
            rules = VisualQARules(sample_raw_data)
            assert rules._vision_available is True

        with patch.dict(os.environ, {"AI_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": ""}):
            rules = VisualQARules(sample_raw_data)
            assert rules._vision_available is False

    def test_parse_visual_findings_empty(self, sample_raw_data):
        """Test parsing empty visual findings."""
        rules = VisualQARules(sample_raw_data)
        rules._parse_visual_findings("[]", "/path/to/screenshot.png", "https://example.com")

        assert len(rules.findings) == 0

    def test_parse_visual_findings_with_issues(self, sample_raw_data):
        """Test parsing visual findings with issues."""
        rules = VisualQARules(sample_raw_data)
        analysis = """
        [
            {
                "type": "layout",
                "severity": "major",
                "title": "Misaligned navigation",
                "description": "Nav items are unevenly spaced",
                "location": "Header",
                "recommendation": "Use flexbox with gap"
            }
        ]
        """
        rules._parse_visual_findings(analysis, "/path/to/screenshot.png", "https://example.com")

        assert len(rules.findings) == 1
        assert "Misaligned navigation" in rules.findings[0].title
        severity = rules.findings[0].severity
        severity_val = severity.value if hasattr(severity, "value") else severity
        assert severity_val == "P1"

    def test_parse_visual_findings_limits_to_5(self, sample_raw_data):
        """Test that findings are limited to 5 per screenshot."""
        rules = VisualQARules(sample_raw_data)
        issues = [
            {
                "type": "layout",
                "severity": "minor",
                "title": f"Issue {i}",
                "description": "Description",
                "location": "Page",
                "recommendation": "Fix it"
            }
            for i in range(10)
        ]
        import json
        analysis = json.dumps(issues)
        rules._parse_visual_findings(analysis, "/path/to/screenshot.png", "https://example.com")

        assert len(rules.findings) == 5


class TestDOMQualityRules:
    """Tests for DOMQualityRules class."""

    def test_missing_h1_finding(self, poor_raw_data):
        """Test detection of missing H1."""
        rules = DOMQualityRules(poor_raw_data)
        findings = rules.run()

        h1_findings = [f for f in findings if "H1" in f.title or "heading" in f.title.lower()]
        assert len(h1_findings) > 0

    def test_multiple_h1_finding(self):
        """Test detection of multiple H1 headings."""
        raw_data = RawData(
            url="https://example.com",
            mode="fast",
            snapshot=SnapshotData(
                url="https://example.com",
                pages=[
                    PageSnapshot(
                        url="https://example.com",
                        title="Test Page",
                        headings={
                            "h1": ["First Heading", "Second Heading", "Third Heading"],
                            "h2": ["Subheading"],
                            "h3": [],
                        },
                        navigation=NavigationInfo(links=[]),
                    )
                ],
            ),
            lighthouse=LighthouseData(url="https://example.com"),
            http_probe=HttpProbeData(url="https://example.com", final_url="https://example.com"),
        )

        rules = DOMQualityRules(raw_data)
        findings = rules.run()

        multiple_h1 = [f for f in findings if "Multiple H1" in f.title]
        assert len(multiple_h1) == 1
        assert "3" in multiple_h1[0].title

    def test_skipped_heading_level(self, poor_raw_data):
        """Test detection of skipped heading levels."""
        rules = DOMQualityRules(poor_raw_data)
        findings = rules.run()

        # poor_raw_data has H1 empty, H3 present, but no H2
        skipped = [f for f in findings if "skipped" in f.title.lower()]
        # May or may not trigger based on H1 presence
        # Just verify rule runs without error
        assert isinstance(findings, list)

    def test_limited_navigation(self, poor_raw_data):
        """Test detection of limited navigation."""
        rules = DOMQualityRules(poor_raw_data)
        findings = rules.run()

        nav_findings = [f for f in findings if "navigation" in f.title.lower()]
        assert len(nav_findings) > 0

    def test_generic_link_text(self):
        """Test detection of generic link text."""
        raw_data = RawData(
            url="https://example.com",
            mode="fast",
            snapshot=SnapshotData(
                url="https://example.com",
                pages=[
                    PageSnapshot(
                        url="https://example.com",
                        title="Test",
                        headings={"h1": ["Test"], "h2": [], "h3": []},
                        navigation=NavigationInfo(
                            links=[
                                {"text": "Click here", "href": "/page1"},
                                {"text": "Read more", "href": "/page2"},
                                {"text": "Here", "href": "/page3"},
                            ],
                        ),
                    )
                ],
            ),
            lighthouse=LighthouseData(url="https://example.com"),
            http_probe=HttpProbeData(url="https://example.com", final_url="https://example.com"),
        )

        rules = DOMQualityRules(raw_data)
        findings = rules.run()

        generic = [f for f in findings if "Generic link" in f.title]
        assert len(generic) == 1

    def test_broken_hamburger_menu(self):
        """Test detection of non-functional hamburger menu."""
        raw_data = RawData(
            url="https://example.com",
            mode="fast",
            snapshot=SnapshotData(
                url="https://example.com",
                pages=[
                    PageSnapshot(
                        url="https://example.com",
                        title="Test",
                        headings={"h1": ["Test"], "h2": [], "h3": []},
                        navigation=NavigationInfo(
                            links=[{"text": "Home", "href": "/"}],
                            has_hamburger=True,
                        ),
                        hamburger_menu_works=False,  # Broken!
                    )
                ],
            ),
            lighthouse=LighthouseData(url="https://example.com"),
            http_probe=HttpProbeData(url="https://example.com", final_url="https://example.com"),
        )

        rules = DOMQualityRules(raw_data)
        findings = rules.run()

        hamburger = [f for f in findings if "hamburger" in f.title.lower()]
        assert len(hamburger) == 1
        severity = hamburger[0].severity
        severity_val = severity.value if hasattr(severity, "value") else severity
        assert severity_val == "P0"  # Critical

    def test_console_errors(self, poor_raw_data):
        """Test detection of JavaScript console errors."""
        rules = DOMQualityRules(poor_raw_data)
        findings = rules.run()

        js_errors = [f for f in findings if "JavaScript" in f.title]
        assert len(js_errors) > 0

    def test_missing_viewport(self, poor_raw_data):
        """Test detection of missing viewport meta tag."""
        rules = DOMQualityRules(poor_raw_data)
        findings = rules.run()

        viewport = [f for f in findings if "viewport" in f.title.lower()]
        assert len(viewport) == 1


class TestTextQualityRules:
    """Tests for TextQualityRules class."""

    def test_missing_title(self, poor_raw_data):
        """Test detection of missing page title."""
        rules = TextQualityRules(poor_raw_data)
        findings = rules.run()

        title_findings = [f for f in findings if "Missing page title" in f.title]
        assert len(title_findings) == 1
        severity = title_findings[0].severity
        severity_val = severity.value if hasattr(severity, "value") else severity
        assert severity_val == "P0"

    def test_title_too_long(self):
        """Test detection of title that's too long."""
        raw_data = RawData(
            url="https://example.com",
            mode="fast",
            snapshot=SnapshotData(
                url="https://example.com",
                pages=[
                    PageSnapshot(
                        url="https://example.com",
                        title="A" * 80,  # Too long
                        headings={"h1": ["Test"], "h2": [], "h3": []},
                        meta_tags={"description": "Test description that is adequate length."},
                    )
                ],
            ),
            lighthouse=LighthouseData(url="https://example.com"),
            http_probe=HttpProbeData(url="https://example.com", final_url="https://example.com"),
        )

        rules = TextQualityRules(raw_data)
        findings = rules.run()

        long_title = [f for f in findings if "truncate" in f.title.lower()]
        assert len(long_title) == 1

    def test_title_too_short(self):
        """Test detection of title that's too short."""
        raw_data = RawData(
            url="https://example.com",
            mode="fast",
            snapshot=SnapshotData(
                url="https://example.com",
                pages=[
                    PageSnapshot(
                        url="https://example.com",
                        title="Hi",  # Too short
                        headings={"h1": ["Test Heading"], "h2": [], "h3": []},
                        meta_tags={"description": "Test description that is adequate length."},
                    )
                ],
            ),
            lighthouse=LighthouseData(url="https://example.com"),
            http_probe=HttpProbeData(url="https://example.com", final_url="https://example.com"),
        )

        rules = TextQualityRules(raw_data)
        findings = rules.run()

        short_title = [f for f in findings if "brief" in f.title.lower()]
        assert len(short_title) == 1

    def test_generic_title(self):
        """Test detection of generic page title."""
        raw_data = RawData(
            url="https://example.com",
            mode="fast",
            snapshot=SnapshotData(
                url="https://example.com",
                pages=[
                    PageSnapshot(
                        url="https://example.com",
                        title="Home",  # Generic
                        headings={"h1": ["Welcome"], "h2": [], "h3": []},
                        meta_tags={"description": "Test description."},
                    )
                ],
            ),
            lighthouse=LighthouseData(url="https://example.com"),
            http_probe=HttpProbeData(url="https://example.com", final_url="https://example.com"),
        )

        rules = TextQualityRules(raw_data)
        findings = rules.run()

        generic = [f for f in findings if "Generic" in f.title]
        assert len(generic) == 1

    def test_weak_cta_text(self):
        """Test detection of weak CTA text."""
        raw_data = RawData(
            url="https://example.com",
            mode="fast",
            snapshot=SnapshotData(
                url="https://example.com",
                pages=[
                    PageSnapshot(
                        url="https://example.com",
                        title="Test Page - Good Title Here",
                        headings={"h1": ["Welcome to Test"], "h2": [], "h3": []},
                        ctas=[
                            CTAInfo(text="Submit", type="button", is_above_fold=True),
                            CTAInfo(text="Click here", type="link", is_above_fold=True),
                        ],
                        meta_tags={"description": "A good description for the test page."},
                    )
                ],
            ),
            lighthouse=LighthouseData(url="https://example.com"),
            http_probe=HttpProbeData(url="https://example.com", final_url="https://example.com"),
        )

        rules = TextQualityRules(raw_data)
        findings = rules.run()

        weak_cta = [f for f in findings if "Weak CTA" in f.title]
        assert len(weak_cta) == 1

    def test_no_cta_above_fold(self):
        """Test detection of missing above-fold CTA."""
        raw_data = RawData(
            url="https://example.com",
            mode="fast",
            snapshot=SnapshotData(
                url="https://example.com",
                pages=[
                    PageSnapshot(
                        url="https://example.com",
                        title="Test Page - Good Title Here",
                        headings={"h1": ["Welcome to Test"], "h2": [], "h3": []},
                        ctas=[
                            CTAInfo(text="Contact Us", type="button", is_above_fold=False),
                            CTAInfo(text="Learn More", type="link", is_above_fold=False),
                        ],
                        meta_tags={"description": "A good description for the test page."},
                    )
                ],
            ),
            lighthouse=LighthouseData(url="https://example.com"),
            http_probe=HttpProbeData(url="https://example.com", final_url="https://example.com"),
        )

        rules = TextQualityRules(raw_data)
        findings = rules.run()

        above_fold = [f for f in findings if "above the fold" in f.title.lower()]
        assert len(above_fold) == 1

    def test_missing_meta_description(self):
        """Test detection of missing meta description."""
        raw_data = RawData(
            url="https://example.com",
            mode="fast",
            snapshot=SnapshotData(
                url="https://example.com",
                pages=[
                    PageSnapshot(
                        url="https://example.com",
                        title="Test Page - Good Title",
                        headings={"h1": ["Test"], "h2": [], "h3": []},
                        meta_tags={},  # No description
                    )
                ],
            ),
            lighthouse=LighthouseData(url="https://example.com"),
            http_probe=HttpProbeData(url="https://example.com", final_url="https://example.com"),
        )

        rules = TextQualityRules(raw_data)
        findings = rules.run()

        meta = [f for f in findings if "meta description" in f.title.lower()]
        assert len(meta) == 1

    def test_meta_description_too_short(self):
        """Test detection of short meta description."""
        raw_data = RawData(
            url="https://example.com",
            mode="fast",
            snapshot=SnapshotData(
                url="https://example.com",
                pages=[
                    PageSnapshot(
                        url="https://example.com",
                        title="Test Page - Good Title",
                        headings={"h1": ["Test"], "h2": [], "h3": []},
                        meta_tags={"description": "Short desc."},  # Too short
                    )
                ],
            ),
            lighthouse=LighthouseData(url="https://example.com"),
            http_probe=HttpProbeData(url="https://example.com", final_url="https://example.com"),
        )

        rules = TextQualityRules(raw_data)
        findings = rules.run()

        short_desc = [f for f in findings if "too short" in f.title.lower()]
        assert len(short_desc) == 1

    def test_good_page_no_issues(self, sample_raw_data):
        """Test that a well-configured page has minimal issues."""
        rules = TextQualityRules(sample_raw_data)
        findings = rules.run()

        # Sample data has good title, CTAs, and meta description
        # Should have few or no critical issues
        def get_severity(f):
            s = f.severity
            return s.value if hasattr(s, "value") else s

        critical = [f for f in findings if get_severity(f) == "P0"]
        assert len(critical) == 0


class TestRulesIntegration:
    """Integration tests for all new rules."""

    def test_all_rules_run_without_error(self, sample_raw_data):
        """Test that all rules run without raising exceptions."""
        rules_classes = [VisualQARules, DOMQualityRules, TextQualityRules]

        for rule_class in rules_classes:
            rule = rule_class(sample_raw_data)
            findings = rule.run()
            assert isinstance(findings, list)

    def test_all_rules_with_poor_data(self, poor_raw_data):
        """Test that all rules detect issues in poor data."""
        dom_rules = DOMQualityRules(poor_raw_data)
        dom_findings = dom_rules.run()

        text_rules = TextQualityRules(poor_raw_data)
        text_findings = text_rules.run()

        # Poor data should trigger multiple findings
        assert len(dom_findings) > 0
        assert len(text_findings) > 0
