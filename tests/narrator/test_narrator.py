"""Integration tests for the narrator module."""

import pytest
from unittest.mock import MagicMock, patch

from proofkit.narrator import Narrator
from proofkit.schemas.report import ReportNarrative
from proofkit.schemas.business import BusinessType
from proofkit.utils.exceptions import TokenLimitError


class TestNarrator:
    @pytest.fixture
    def mock_narrator_deps(self, mock_claude_responses):
        """Mock all narrator dependencies."""
        with patch("proofkit.narrator.ClaudeClient") as MockClient, \
             patch("proofkit.narrator.NarrativeBuilder") as MockBuilder, \
             patch("proofkit.narrator.ConceptGenerator") as MockGenerator, \
             patch("proofkit.narrator.TokenManager") as MockTokenManager:

            # Configure mock client
            mock_client = MagicMock()
            mock_client.get_total_usage.return_value = {"input_tokens": 500, "output_tokens": 300}
            MockClient.return_value = mock_client

            # Configure mock builder
            mock_builder = MagicMock()
            mock_builder.generate_executive_summary.return_value = mock_claude_responses["executive_summary"]
            mock_builder.generate_quick_wins.return_value = [
                "Fix 1",
                "Fix 2",
                "Fix 3",
            ]
            mock_builder.generate_strategic_priorities.return_value = [
                "Priority 1",
                "Priority 2",
            ]
            MockBuilder.return_value = mock_builder

            # Configure mock generator
            mock_generator = MagicMock()
            mock_generator.generate_concept_bullets.return_value = ["Concept 1", "Concept 2"]
            mock_generator.generate_lovable_prompt.return_value = mock_claude_responses["lovable_prompt"]
            MockGenerator.return_value = mock_generator

            # Configure mock token manager
            mock_token_manager = MagicMock()
            mock_token_manager.estimate_usage.return_value = 2000
            mock_token_manager.check_budget.return_value = None
            mock_token_manager.get_usage_report.return_value = {
                "input_tokens": 500,
                "output_tokens": 300,
                "total_tokens": 800,
                "estimated_cost": 0.05,
                "remaining_budget": 14.95,
                "budget_used_percent": 0.3,
            }
            MockTokenManager.return_value = mock_token_manager

            yield {
                "client": mock_client,
                "builder": mock_builder,
                "generator": mock_generator,
                "token_manager": mock_token_manager,
            }

    def test_generate_returns_report_narrative(self, mock_narrator_deps, sample_findings):
        """Test that generate returns a ReportNarrative."""
        narrator = Narrator()
        result = narrator.generate(sample_findings)

        assert isinstance(result, ReportNarrative)

    def test_generate_populates_all_fields(self, mock_narrator_deps, sample_findings):
        """Test that generate populates all narrative fields."""
        narrator = Narrator()
        result = narrator.generate(sample_findings)

        assert result.executive_summary
        assert isinstance(result.quick_wins, list)
        assert len(result.quick_wins) > 0
        assert isinstance(result.strategic_priorities, list)
        assert len(result.strategic_priorities) > 0

    def test_generate_without_concept(self, mock_narrator_deps, sample_findings):
        """Test generation without concept prompt."""
        narrator = Narrator()
        result = narrator.generate(sample_findings, generate_concept=False)

        assert result.lovable_concept is None
        mock_narrator_deps["generator"].generate_lovable_prompt.assert_not_called()

    def test_generate_with_concept(self, mock_narrator_deps, sample_findings, mock_claude_responses):
        """Test generation with concept prompt."""
        narrator = Narrator()
        result = narrator.generate(sample_findings, generate_concept=True)

        assert result.lovable_concept is not None
        mock_narrator_deps["generator"].generate_lovable_prompt.assert_called_once()

    def test_generate_with_business_type(self, mock_narrator_deps, sample_findings):
        """Test generation with business type."""
        narrator = Narrator()
        narrator.generate(
            sample_findings,
            business_type=BusinessType.ECOMMERCE,
        )

        mock_narrator_deps["builder"].generate_executive_summary.assert_called_once()
        call_args = mock_narrator_deps["builder"].generate_executive_summary.call_args
        # Check positional args (findings_summary, business_type, conversion_goal)
        assert call_args.args[1] == BusinessType.ECOMMERCE

    def test_generate_with_conversion_goal(self, mock_narrator_deps, sample_findings):
        """Test generation with conversion goal."""
        narrator = Narrator()
        narrator.generate(
            sample_findings,
            conversion_goal="Online bookings",
        )

        mock_narrator_deps["builder"].generate_executive_summary.assert_called_once()
        call_args = mock_narrator_deps["builder"].generate_executive_summary.call_args
        # Check positional args (findings_summary, business_type, conversion_goal)
        assert call_args.args[2] == "Online bookings"

    def test_generate_checks_budget(self, mock_narrator_deps, sample_findings):
        """Test that generate checks token budget."""
        narrator = Narrator()
        narrator.generate(sample_findings)

        mock_narrator_deps["token_manager"].check_budget.assert_called_once()

    def test_generate_records_usage(self, mock_narrator_deps, sample_findings):
        """Test that generate records token usage."""
        narrator = Narrator()
        narrator.generate(sample_findings)

        mock_narrator_deps["token_manager"].record_usage.assert_called_once()

    def test_generate_budget_exceeded_raises(self, mock_narrator_deps, sample_findings):
        """Test that budget exceeded raises error."""
        mock_narrator_deps["token_manager"].check_budget.side_effect = TokenLimitError(
            "Budget exceeded"
        )

        narrator = Narrator()
        with pytest.raises(TokenLimitError):
            narrator.generate(sample_findings)

    def test_get_usage_report(self, mock_narrator_deps):
        """Test getting usage report."""
        narrator = Narrator()
        report = narrator.get_usage_report()

        assert "input_tokens" in report
        assert "output_tokens" in report
        assert "estimated_cost" in report


class TestPrepareFindings:
    """Tests for findings preparation - these don't need full mocking."""

    def test_prepare_findings_summary(self, sample_findings):
        """Test findings summary preparation."""
        # Import Narrator internals directly to test the method
        from proofkit.narrator import Narrator

        # Create a mock narrator without initializing (to avoid API key requirement)
        with patch("proofkit.narrator.ClaudeClient"), \
             patch("proofkit.narrator.NarrativeBuilder"), \
             patch("proofkit.narrator.ConceptGenerator"), \
             patch("proofkit.narrator.TokenManager"):
            narrator = Narrator()

        summary = narrator._prepare_findings_summary(sample_findings)

        assert isinstance(summary, str)
        # Should include finding info
        assert "P0" in summary or "P1" in summary
        assert "Impact:" in summary
        assert "Fix:" in summary

    def test_prepare_findings_limits_to_15(self, sample_findings):
        """Test that findings are limited to 15."""
        with patch("proofkit.narrator.ClaudeClient"), \
             patch("proofkit.narrator.NarrativeBuilder"), \
             patch("proofkit.narrator.ConceptGenerator"), \
             patch("proofkit.narrator.TokenManager"):
            narrator = Narrator()

        # Create more than 15 findings
        many_findings = sample_findings * 5  # 25 findings

        summary = narrator._prepare_findings_summary(many_findings)

        # Count how many findings are included (each has "Impact:")
        impact_count = summary.count("Impact:")
        assert impact_count <= 15

    def test_prepare_findings_sorts_by_severity(self, sample_findings):
        """Test that findings are sorted by severity."""
        with patch("proofkit.narrator.ClaudeClient"), \
             patch("proofkit.narrator.NarrativeBuilder"), \
             patch("proofkit.narrator.ConceptGenerator"), \
             patch("proofkit.narrator.TokenManager"):
            narrator = Narrator()

        summary = narrator._prepare_findings_summary(sample_findings)

        # P0 should appear before P1 in the summary
        p0_pos = summary.find("[P0]")
        p1_pos = summary.find("[P1]")

        if p0_pos != -1 and p1_pos != -1:
            assert p0_pos < p1_pos


class TestCategoryInsights:
    """Tests for category insights generation."""

    def test_generate_category_insights(self, sample_findings):
        """Test category insights generation."""
        with patch("proofkit.narrator.ClaudeClient"), \
             patch("proofkit.narrator.NarrativeBuilder"), \
             patch("proofkit.narrator.ConceptGenerator"), \
             patch("proofkit.narrator.TokenManager"):
            narrator = Narrator()

        insights = narrator._generate_category_insights(sample_findings)

        assert isinstance(insights, dict)
        # Should have insights for categories with findings
        assert "SEO" in insights
        assert "PERFORMANCE" in insights

    def test_category_insights_mentions_critical(self, sample_findings):
        """Test that critical issues are highlighted."""
        with patch("proofkit.narrator.ClaudeClient"), \
             patch("proofkit.narrator.NarrativeBuilder"), \
             patch("proofkit.narrator.ConceptGenerator"), \
             patch("proofkit.narrator.TokenManager"):
            narrator = Narrator()

        insights = narrator._generate_category_insights(sample_findings)

        # SEO has P0 finding
        assert "critical" in insights.get("SEO", "").lower()

    def test_category_insights_mentions_high_priority(self, sample_findings):
        """Test that high priority issues are mentioned."""
        with patch("proofkit.narrator.ClaudeClient"), \
             patch("proofkit.narrator.NarrativeBuilder"), \
             patch("proofkit.narrator.ConceptGenerator"), \
             patch("proofkit.narrator.TokenManager"):
            narrator = Narrator()

        insights = narrator._generate_category_insights(sample_findings)

        # PERFORMANCE has P1 finding
        perf_insight = insights.get("PERFORMANCE", "").lower()
        assert "high" in perf_insight or "priority" in perf_insight or "improvement" in perf_insight
