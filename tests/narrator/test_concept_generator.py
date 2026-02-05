"""Tests for the concept generator."""

import pytest
from unittest.mock import MagicMock, patch

from proofkit.narrator.concept_generator import ConceptGenerator
from proofkit.schemas.business import BusinessType


class TestConceptGenerator:
    @pytest.fixture
    def mock_client(self):
        """Create a mock client for testing."""
        return MagicMock()

    @pytest.fixture
    def generator(self, mock_client):
        """Create a concept generator with mock client."""
        return ConceptGenerator(mock_client)

    def test_generate_concept_bullets(self, mock_client, mock_claude_responses):
        """Test concept bullets generation."""
        mock_client.generate.return_value = mock_claude_responses["concept_bullets"]
        generator = ConceptGenerator(mock_client)

        result = generator.generate_concept_bullets(
            findings_summary="Test findings",
            business_type=BusinessType.AGENCY,
        )

        assert isinstance(result, list)
        assert len(result) > 0
        assert len(result) <= 6  # Max 6 concepts
        mock_client.generate.assert_called_once()

    def test_generate_concept_bullets_parses_correctly(self, mock_client, mock_claude_responses):
        """Test that concept bullets are parsed correctly."""
        mock_client.generate.return_value = mock_claude_responses["concept_bullets"]
        generator = ConceptGenerator(mock_client)

        result = generator.generate_concept_bullets(
            findings_summary="Test findings",
        )

        # Should have stripped bullet markers
        for item in result:
            assert not item.startswith("-")
            assert not item.startswith("•")

    def test_generate_lovable_prompt(self, mock_client, mock_claude_responses):
        """Test Lovable prompt generation."""
        mock_client.generate.return_value = mock_claude_responses["lovable_prompt"]
        generator = ConceptGenerator(mock_client)

        result = generator.generate_lovable_prompt(
            findings_summary="Test findings",
            business_type=BusinessType.ECOMMERCE,
        )

        assert isinstance(result, str)
        assert len(result) > 100  # Should be substantial
        mock_client.generate.assert_called_once()

    def test_generate_lovable_prompt_without_business_type(self, mock_client, mock_claude_responses):
        """Test Lovable prompt generation without business type."""
        mock_client.generate.return_value = mock_claude_responses["lovable_prompt"]
        generator = ConceptGenerator(mock_client)

        result = generator.generate_lovable_prompt(
            findings_summary="Test findings",
        )

        assert isinstance(result, str)
        # Should use generic guidance
        call_args = mock_client.generate.call_args
        assert "business" in call_args.kwargs["user_prompt"].lower()

    def test_design_guidance_real_estate(self, mock_client):
        """Test design guidance for real estate."""
        generator = ConceptGenerator(mock_client)
        guidance = generator._get_design_guidance(BusinessType.REAL_ESTATE)

        assert "property" in guidance.lower()
        assert "premium" in guidance.lower() or "elegant" in guidance.lower()

    def test_design_guidance_ecommerce(self, mock_client):
        """Test design guidance for e-commerce."""
        generator = ConceptGenerator(mock_client)
        guidance = generator._get_design_guidance(BusinessType.ECOMMERCE)

        assert "product" in guidance.lower()
        assert "cart" in guidance.lower()

    def test_design_guidance_saas(self, mock_client):
        """Test design guidance for SaaS."""
        generator = ConceptGenerator(mock_client)
        guidance = generator._get_design_guidance(BusinessType.SAAS)

        assert "pricing" in guidance.lower()
        assert "cta" in guidance.lower() or "trial" in guidance.lower()

    def test_design_guidance_hospitality(self, mock_client):
        """Test design guidance for hospitality."""
        generator = ConceptGenerator(mock_client)
        guidance = generator._get_design_guidance(BusinessType.HOSPITALITY)

        assert "booking" in guidance.lower()
        assert "room" in guidance.lower()

    def test_design_guidance_restaurant(self, mock_client):
        """Test design guidance for restaurant."""
        generator = ConceptGenerator(mock_client)
        guidance = generator._get_design_guidance(BusinessType.RESTAURANT)

        assert "menu" in guidance.lower()
        assert "food" in guidance.lower() or "ordering" in guidance.lower()

    def test_design_guidance_healthcare(self, mock_client):
        """Test design guidance for healthcare."""
        generator = ConceptGenerator(mock_client)
        guidance = generator._get_design_guidance(BusinessType.HEALTHCARE)

        assert "appointment" in guidance.lower()
        assert "trust" in guidance.lower() or "clean" in guidance.lower()

    def test_design_guidance_agency(self, mock_client):
        """Test design guidance for agency."""
        generator = ConceptGenerator(mock_client)
        guidance = generator._get_design_guidance(BusinessType.AGENCY)

        assert "portfolio" in guidance.lower()
        assert "creative" in guidance.lower() or "testimonial" in guidance.lower()

    def test_design_guidance_fallback(self, mock_client):
        """Test design guidance fallback for unknown types."""
        generator = ConceptGenerator(mock_client)
        guidance = generator._get_design_guidance(None)

        # Should have generic guidance
        assert "modern" in guidance.lower()
        assert "cta" in guidance.lower()
