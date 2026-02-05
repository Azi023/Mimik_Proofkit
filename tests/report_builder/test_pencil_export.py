"""Tests for Pencil export functionality."""

import pytest
import json
from pathlib import Path
from datetime import datetime

from proofkit.report_builder.pencil_export import (
    PencilReportGenerator,
    generate_pencil_report,
)
from proofkit.schemas.report import Report, ReportMeta, ReportNarrative
from proofkit.schemas.finding import Finding, Category, Severity, Effort


@pytest.fixture
def sample_findings():
    """Create sample findings for testing."""
    return [
        Finding(
            id="UX-001",
            category=Category.UX,
            severity=Severity.P1,
            title="Mobile Navigation Issues",
            summary="Navigation menu is difficult to use on mobile devices",
            impact="Users may struggle to find content, increasing bounce rate",
            recommendation="Implement hamburger menu with clear touch targets",
            effort=Effort.M,
        ),
        Finding(
            id="SEO-001",
            category=Category.SEO,
            severity=Severity.P0,
            title="Missing Meta Description",
            summary="Page lacks meta description tag",
            impact="Poor search result snippets may reduce click-through rate",
            recommendation="Add unique meta descriptions to all pages",
            effort=Effort.S,
        ),
        Finding(
            id="CONV-001",
            category=Category.CONVERSION,
            severity=Severity.P1,
            title="Weak CTA Visibility",
            summary="Primary call-to-action buttons lack visual prominence",
            impact="Lower conversion rates due to missed CTA opportunities",
            recommendation="Use contrasting colors and larger buttons for CTAs",
            effort=Effort.S,
        ),
        Finding(
            id="SEC-001",
            category=Category.SECURITY,
            severity=Severity.P2,
            title="Missing Security Headers",
            summary="Several security headers are not configured",
            impact="Site may be vulnerable to certain attacks",
            recommendation="Add X-Frame-Options, CSP, and other security headers",
            effort=Effort.M,
        ),
    ]


@pytest.fixture
def sample_report(sample_findings):
    """Create a sample report for testing."""
    return Report(
        meta=ReportMeta(
            audit_id="test-123",
            url="https://www.example-business.com",
            business_type="real_estate",
            conversion_goal="lead_generation",
            generated_at=datetime.now(),
            proofkit_version="0.1.0",
            mode="fast",
            pages_analyzed=5,
        ),
        overall_score=72,
        scorecard={
            "OVERALL": 72,
            "PERFORMANCE": 85,
            "SEO": 65,
            "CONVERSION": 70,
            "UX": 75,
            "SECURITY": 68,
        },
        findings=sample_findings,
        narrative=ReportNarrative(
            executive_summary="This audit reveals several opportunities to improve the website's performance, SEO, and user experience.",
            quick_wins=[
                "Add meta descriptions to all pages",
                "Increase CTA button visibility",
                "Fix mobile navigation issues",
            ],
            strategic_priorities=[
                "Implement comprehensive SEO strategy",
                "Redesign mobile experience",
                "Add security headers and monitoring",
            ],
            category_insights={
                "UX": "Mobile experience needs significant improvement",
                "SEO": "Basic SEO elements are missing",
            },
            lovable_concept="Create a modern real estate website with...",
        ),
    )


class TestPencilReportGenerator:
    """Tests for PencilReportGenerator class."""

    def test_init_groups_findings(self, sample_report):
        """Test that findings are grouped by category on init."""
        generator = PencilReportGenerator(sample_report)

        assert "UX" in generator.findings_by_category
        assert "SEO" in generator.findings_by_category
        assert "CONVERSION" in generator.findings_by_category
        assert "SECURITY" in generator.findings_by_category

    def test_extract_client_name(self, sample_report):
        """Test client name extraction from URL."""
        generator = PencilReportGenerator(sample_report)
        name = generator._extract_client_name()

        assert "Example" in name or "Business" in name

    def test_extract_client_name_with_www(self, sample_report):
        """Test client name extraction handles www prefix."""
        sample_report.meta.url = "https://www.my-company.com"
        generator = PencilReportGenerator(sample_report)
        name = generator._extract_client_name()

        assert "My Company Com" in name

    def test_truncate_short_text(self, sample_report):
        """Test truncation of text shorter than max length."""
        generator = PencilReportGenerator(sample_report)
        result = generator._truncate("Short text", 100)

        assert result == "Short text"

    def test_truncate_long_text(self, sample_report):
        """Test truncation of text longer than max length."""
        generator = PencilReportGenerator(sample_report)
        long_text = "A" * 200
        result = generator._truncate(long_text, 50)

        assert len(result) == 50
        assert result.endswith("...")

    def test_generate_full_report_prompt(self, sample_report):
        """Test full report prompt generation."""
        generator = PencilReportGenerator(sample_report)
        prompt = generator.generate_full_report_prompt()

        # Check key sections are present
        assert "Website Performance & Inspection Report" in prompt
        assert "Executive Summary" in prompt
        assert "UX Audit Findings" in prompt
        assert "SEO Findings" in prompt
        assert "Lead Generation Findings" in prompt
        assert "Recommendations Summary" in prompt

    def test_generate_full_report_prompt_includes_findings(self, sample_report):
        """Test that full report prompt includes findings."""
        generator = PencilReportGenerator(sample_report)
        prompt = generator.generate_full_report_prompt()

        # Check findings are mentioned
        assert "Mobile Navigation" in prompt or "P1" in prompt
        assert "Meta Description" in prompt or "P0" in prompt

    def test_generate_full_report_prompt_includes_scorecard(self, sample_report):
        """Test that full report prompt includes scorecard."""
        generator = PencilReportGenerator(sample_report)
        prompt = generator.generate_full_report_prompt()

        assert "Scores:" in prompt or "PERFORMANCE" in prompt

    def test_generate_section_prompts(self, sample_report):
        """Test individual section prompt generation."""
        generator = PencilReportGenerator(sample_report)
        prompts = generator.generate_section_prompts()

        assert "cover" in prompts
        assert "executive_summary" in prompts
        assert "ux_findings" in prompts
        assert "seo_findings" in prompts
        assert "recommendations" in prompts
        assert "closing" in prompts

    def test_generate_section_prompts_cover_content(self, sample_report):
        """Test cover section prompt content."""
        generator = PencilReportGenerator(sample_report)
        prompts = generator.generate_section_prompts()

        cover = prompts["cover"]
        assert "hello." in cover
        assert "Website Performance & Inspection Report" in cover
        assert "Mimik Creations" in cover

    def test_generate_section_prompts_executive_summary_content(self, sample_report):
        """Test executive summary section content."""
        generator = PencilReportGenerator(sample_report)
        prompts = generator.generate_section_prompts()

        summary = prompts["executive_summary"]
        assert "PURPOSE OF THIS AUDIT" in summary
        assert "AUDIT FRAMEWORK" in summary
        assert "User Experience" in summary

    def test_format_recommendations(self, sample_report):
        """Test recommendations formatting."""
        generator = PencilReportGenerator(sample_report)
        result = generator._format_recommendations()

        assert "Quick Wins:" in result
        assert "Strategic Priorities:" in result
        assert "meta descriptions" in result.lower() or "Add" in result

    def test_format_scorecard(self, sample_report):
        """Test scorecard formatting."""
        generator = PencilReportGenerator(sample_report)
        result = generator._format_scorecard()

        assert "Scores:" in result
        # Check emojis based on scores
        assert "🟢" in result or "🟡" in result or "🔴" in result

    def test_format_findings_for_prompt(self, sample_report):
        """Test findings formatting for prompts."""
        generator = PencilReportGenerator(sample_report)

        ux_findings = generator._format_findings_for_prompt("UX")
        assert "Mobile Navigation" in ux_findings or "P1" in ux_findings

    def test_format_findings_for_prompt_empty_category(self, sample_report):
        """Test findings formatting for empty category."""
        generator = PencilReportGenerator(sample_report)

        maintenance_findings = generator._format_findings_for_prompt("MAINTENANCE")
        assert "No critical findings" in maintenance_findings


class TestSavePrompts:
    """Tests for saving prompts to files."""

    def test_save_prompts_creates_directory(self, sample_report, tmp_path):
        """Test that save_prompts creates output directory."""
        output_dir = tmp_path / "pencil_output"
        generator = PencilReportGenerator(sample_report)

        generator.save_prompts(output_dir)

        assert output_dir.exists()

    def test_save_prompts_creates_full_report(self, sample_report, tmp_path):
        """Test that full report prompt file is created."""
        output_dir = tmp_path / "pencil_output"
        generator = PencilReportGenerator(sample_report)

        result = generator.save_prompts(output_dir)

        full_report_path = Path(result["full_prompt_path"])
        assert full_report_path.exists()

        content = full_report_path.read_text()
        assert "Website Performance & Inspection Report" in content

    def test_save_prompts_creates_section_files(self, sample_report, tmp_path):
        """Test that section prompt files are created."""
        output_dir = tmp_path / "pencil_output"
        generator = PencilReportGenerator(sample_report)

        result = generator.save_prompts(output_dir)

        for section in result["section_prompts"]:
            section_path = output_dir / f"pencil_{section}.txt"
            assert section_path.exists()

    def test_save_prompts_creates_summary_json(self, sample_report, tmp_path):
        """Test that summary JSON is created."""
        output_dir = tmp_path / "pencil_output"
        generator = PencilReportGenerator(sample_report)

        result = generator.save_prompts(output_dir)

        summary_path = Path(result["summary_path"])
        assert summary_path.exists()

        summary = json.loads(summary_path.read_text())
        assert "client" in summary
        assert "url" in summary
        assert "scorecard" in summary
        assert "finding_count" in summary

    def test_save_prompts_summary_content(self, sample_report, tmp_path):
        """Test summary JSON content."""
        output_dir = tmp_path / "pencil_output"
        generator = PencilReportGenerator(sample_report)

        generator.save_prompts(output_dir)

        summary_path = output_dir / "pencil_summary.json"
        summary = json.loads(summary_path.read_text())

        assert summary["finding_count"] == 4
        assert "OVERALL" in summary["scorecard"]


class TestGeneratePencilReport:
    """Tests for the convenience function."""

    def test_generate_pencil_report(self, sample_report, tmp_path):
        """Test the convenience function."""
        output_dir = tmp_path / "pencil_output"

        result = generate_pencil_report(sample_report, output_dir)

        assert "full_prompt_path" in result
        assert "section_prompts" in result
        assert "summary_path" in result
        assert output_dir.exists()


class TestEmptyReport:
    """Tests for handling reports with minimal data."""

    def test_empty_findings(self, tmp_path):
        """Test handling report with no findings."""
        report = Report(
            meta=ReportMeta(
                audit_id="test-empty",
                url="https://www.empty-site.com",
                generated_at=datetime.now(),
                proofkit_version="0.1.0",
                mode="fast",
            ),
            overall_score=100,
            scorecard={},
            findings=[],
            narrative=ReportNarrative(),
        )

        generator = PencilReportGenerator(report)
        prompt = generator.generate_full_report_prompt()

        assert "Website Performance & Inspection Report" in prompt
        assert "No critical findings" in prompt

    def test_empty_narrative(self, tmp_path):
        """Test handling report with empty narrative."""
        report = Report(
            meta=ReportMeta(
                audit_id="test-empty",
                url="https://www.empty-site.com",
                generated_at=datetime.now(),
                proofkit_version="0.1.0",
                mode="fast",
            ),
            overall_score=100,
            scorecard={},
            findings=[],
        )

        generator = PencilReportGenerator(report)
        result = generator._format_recommendations()

        # Should handle empty gracefully
        assert "Quick Wins" in result or "Recommendations" in result
