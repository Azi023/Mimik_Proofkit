"""Tests for the narrative builder."""

import pytest
from unittest.mock import MagicMock, patch

from proofkit.narrator.narrative_builder import NarrativeBuilder
from proofkit.schemas.business import BusinessType


class TestNarrativeBuilder:
    @pytest.fixture
    def mock_client(self, mock_claude_responses):
        """Create a mock client for testing."""
        client = MagicMock()
        client.generate = MagicMock(side_effect=lambda **kwargs: mock_claude_responses.get(
            "executive_summary" if "executive" in kwargs.get("user_prompt", "").lower()
            else "quick_wins" if "quick" in kwargs.get("user_prompt", "").lower()
            else "strategic_priorities"
        ))
        return client

    @pytest.fixture
    def builder(self, mock_client):
        """Create a narrative builder with mock client."""
        with patch("proofkit.narrator.narrative_builder.PromptTemplates") as MockTemplates:
            mock_templates = MagicMock()
            mock_templates.get_system_prompt.return_value = "System prompt"
            MockTemplates.return_value = mock_templates
            return NarrativeBuilder(mock_client)

    def test_generate_executive_summary(self, mock_claude_responses):
        """Test executive summary generation."""
        mock_client = MagicMock()
        mock_client.generate.return_value = mock_claude_responses["executive_summary"]

        with patch("proofkit.narrator.narrative_builder.PromptTemplates") as MockTemplates:
            mock_templates = MagicMock()
            mock_templates.get_system_prompt.return_value = "System prompt"
            MockTemplates.return_value = mock_templates

            builder = NarrativeBuilder(mock_client)
            result = builder.generate_executive_summary(
                findings_summary="Test findings",
                business_type=BusinessType.AGENCY,
                conversion_goal="Lead generation",
            )

        assert isinstance(result, str)
        assert len(result) > 0
        mock_client.generate.assert_called_once()

    def test_generate_executive_summary_without_business_type(self, mock_claude_responses):
        """Test executive summary generation without business type."""
        mock_client = MagicMock()
        mock_client.generate.return_value = mock_claude_responses["executive_summary"]

        with patch("proofkit.narrator.narrative_builder.PromptTemplates") as MockTemplates:
            mock_templates = MagicMock()
            mock_templates.get_system_prompt.return_value = "System prompt"
            MockTemplates.return_value = mock_templates

            builder = NarrativeBuilder(mock_client)
            result = builder.generate_executive_summary(
                findings_summary="Test findings",
            )

        assert isinstance(result, str)
        # Should use default business context
        call_args = mock_client.generate.call_args
        assert "General business website" in call_args.kwargs["user_prompt"]

    def test_generate_quick_wins(self, mock_claude_responses):
        """Test quick wins generation."""
        mock_client = MagicMock()
        mock_client.generate.return_value = mock_claude_responses["quick_wins"]

        with patch("proofkit.narrator.narrative_builder.PromptTemplates") as MockTemplates:
            mock_templates = MagicMock()
            mock_templates.get_system_prompt.return_value = "System prompt"
            MockTemplates.return_value = mock_templates

            builder = NarrativeBuilder(mock_client)
            result = builder.generate_quick_wins(findings_summary="Test findings")

        assert isinstance(result, list)
        assert len(result) > 0
        assert len(result) <= 5  # Max 5 quick wins

    def test_generate_quick_wins_parses_bullets(self, mock_claude_responses):
        """Test that quick wins correctly parses bullet points."""
        mock_client = MagicMock()
        mock_client.generate.return_value = mock_claude_responses["quick_wins"]

        with patch("proofkit.narrator.narrative_builder.PromptTemplates") as MockTemplates:
            mock_templates = MagicMock()
            mock_templates.get_system_prompt.return_value = "System prompt"
            MockTemplates.return_value = mock_templates

            builder = NarrativeBuilder(mock_client)
            result = builder.generate_quick_wins(findings_summary="Test findings")

        # Should have parsed the bullet list
        for item in result:
            assert not item.startswith("-")
            assert not item.startswith("•")

    def test_generate_strategic_priorities(self, mock_claude_responses):
        """Test strategic priorities generation."""
        mock_client = MagicMock()
        mock_client.generate.return_value = mock_claude_responses["strategic_priorities"]

        with patch("proofkit.narrator.narrative_builder.PromptTemplates") as MockTemplates:
            mock_templates = MagicMock()
            mock_templates.get_system_prompt.return_value = "System prompt"
            MockTemplates.return_value = mock_templates

            builder = NarrativeBuilder(mock_client)
            result = builder.generate_strategic_priorities(
                findings_summary="Test findings",
                business_type=BusinessType.ECOMMERCE,
            )

        assert isinstance(result, list)
        assert len(result) > 0
        assert len(result) <= 5

    def test_generate_strategic_priorities_includes_industry(self, mock_claude_responses):
        """Test that strategic priorities include industry context."""
        mock_client = MagicMock()
        mock_client.generate.return_value = mock_claude_responses["strategic_priorities"]

        with patch("proofkit.narrator.narrative_builder.PromptTemplates") as MockTemplates:
            mock_templates = MagicMock()
            mock_templates.get_system_prompt.return_value = "System prompt"
            MockTemplates.return_value = mock_templates

            builder = NarrativeBuilder(mock_client)
            builder.generate_strategic_priorities(
                findings_summary="Test findings",
                business_type=BusinessType.REAL_ESTATE,
            )

        call_args = mock_client.generate.call_args
        assert "Real Estate" in call_args.kwargs["user_prompt"]
