"""Generates Lovable-ready concept prompts and rebuild suggestions."""

from typing import List, Optional

from proofkit.schemas.business import BusinessType

from .claude_client import ClaudeClient
from .prompts import PromptTemplates


class ConceptGenerator:
    """
    Generates Lovable-ready concept prompts and rebuild suggestions.

    Creates detailed prompts that can be used directly with AI website
    builders like Lovable.dev to generate redesign concepts.
    """

    def __init__(self, client: ClaudeClient):
        """
        Initialize the concept generator.

        Args:
            client: Claude client for AI generation
        """
        self.client = client
        self.templates = PromptTemplates()

    def generate_concept_bullets(
        self,
        findings_summary: str,
        business_type: Optional[BusinessType] = None,
    ) -> List[str]:
        """
        Generate concept bullets for "What we can build" section.

        Args:
            findings_summary: Prepared findings text
            business_type: Business context

        Returns:
            List of concept improvement bullets
        """
        system_prompt = """You are a web design consultant creating concept ideas for a website redesign.
Focus on modern, conversion-optimized design patterns that address the audit findings."""

        industry = "business"
        if business_type:
            industry = business_type.value.replace("_", " ")

        user_prompt = f"""
Based on these audit findings, suggest 4-6 concept improvements:

{findings_summary}

Industry: {industry}

Format as brief, compelling bullets that would excite a client:
- [Improvement]: [Brief benefit]

Focus on:
- Modern UX patterns
- Conversion optimization
- Visual improvements
- Mobile experience
- Speed/performance
"""

        response = self.client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=400,
        )

        lines = response.strip().split("\n")
        concepts = [
            line.strip().lstrip("- •").strip()
            for line in lines
            if line.strip() and not line.startswith("#") and len(line.strip()) > 10
        ]

        return concepts[:6]

    def generate_lovable_prompt(
        self,
        findings_summary: str,
        business_type: Optional[BusinessType] = None,
    ) -> str:
        """
        Generate ready-to-use prompt for Lovable.dev.
        This creates a redesign concept that addresses audit findings.

        Args:
            findings_summary: Prepared findings text
            business_type: Business context

        Returns:
            Lovable.dev prompt text
        """
        system_prompt = """You are an expert at writing prompts for AI website builders like Lovable.dev.
Create detailed, specific prompts that result in professional, modern websites."""

        industry = "business"
        if business_type:
            industry = business_type.value.replace("_", " ")

        # Get industry-specific design guidance
        design_guidance = self._get_design_guidance(business_type)

        user_prompt = f"""
Create a Lovable.dev prompt for a {industry} website redesign that addresses these issues:

{findings_summary}

{design_guidance}

The prompt should:
1. Describe the overall design direction (style, mood, aesthetics)
2. Specify the homepage structure (hero, sections, CTA placement)
3. Include specific UI components that fix the audit issues
4. Mention color scheme and typography suggestions
5. Include mobile responsiveness requirements
6. Specify performance considerations (image optimization, lazy loading)

Write a single comprehensive prompt that can be pasted directly into Lovable.
Start with "Create a..." and be specific but not overly technical.
"""

        return self.client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=800,
        )

    def _get_design_guidance(self, business_type: Optional[BusinessType]) -> str:
        """
        Get industry-specific design guidance.

        Args:
            business_type: Business type for context

        Returns:
            Design guidance text
        """
        guidance = {
            BusinessType.REAL_ESTATE: """
Design guidance for real estate:
- Elegant, minimalist aesthetic with high-quality property imagery
- Dark mode option for premium feel
- Prominent property search/filter
- Large hero images with property highlights
- Trust badges, awards, agent profiles
- WhatsApp and direct contact prominently displayed
- Virtual tour integration
""",
            BusinessType.ECOMMERCE: """
Design guidance for e-commerce:
- Clean product grid with quick-view
- Prominent search and filters
- Clear pricing and availability
- Trust badges (secure payment, returns policy)
- Sticky cart indicator
- Mobile-first checkout flow
""",
            BusinessType.SAAS: """
Design guidance for SaaS:
- Modern, professional aesthetic
- Clear value proposition above fold
- Feature highlights with icons
- Pricing table with comparison
- Social proof (logos, testimonials)
- Strong CTA for free trial/demo
""",
            BusinessType.HOSPITALITY: """
Design guidance for hospitality:
- Immersive imagery showcasing property
- Easy date picker for availability
- Room/suite showcase
- Amenities highlights
- Location and nearby attractions
- Reviews integration
- Direct booking CTA
""",
            BusinessType.RESTAURANT: """
Design guidance for restaurants:
- Appetizing food photography
- Easy-to-read menu with prices
- Online ordering or reservation CTAs
- Location and hours prominently displayed
- Mobile-optimized for on-the-go customers
- Social proof and reviews
""",
            BusinessType.HEALTHCARE: """
Design guidance for healthcare:
- Clean, trustworthy aesthetic
- Easy appointment booking
- Doctor/provider profiles
- Services clearly listed
- Insurance information
- HIPAA-compliant design considerations
- Accessibility focus
""",
            BusinessType.AGENCY: """
Design guidance for agencies:
- Portfolio showcase with case studies
- Clear service offerings
- Team profiles
- Client testimonials and logos
- Strong contact CTA
- Modern, creative aesthetic
""",
        }

        return guidance.get(business_type, """
Design guidance:
- Clean, modern aesthetic
- Clear navigation
- Prominent CTA above fold
- Mobile-responsive layout
- Fast loading with optimized images
- Trust signals and social proof
""")
