"""Prompt templates for AI generation."""

from pathlib import Path
from typing import Optional

from proofkit.utils.config import get_config


class PromptTemplates:
    """
    Manages prompt templates for AI generation.

    Loads templates from files when available, falls back to
    built-in templates otherwise.
    """

    # Fallback templates if files don't exist
    FALLBACK_TEMPLATES = {
        "executive_summary": """You are a website audit expert at a professional web agency.
Write concise, business-focused content that emphasizes impact and opportunity.
Avoid technical jargon unless necessary. Focus on what matters to business owners:
- Revenue impact
- Customer experience
- Competitive positioning
- Brand perception

Write in a confident, professional tone. Be direct but not alarmist.
Do not use bullet points in executive summaries - write in flowing prose.""",

        "quick_wins": """You are a pragmatic web consultant identifying high-impact, low-effort improvements.
Focus on changes that:
- Can be implemented quickly (hours to days)
- Have measurable impact on conversion or user experience
- Don't require major technical overhaul
- Provide visible results to justify further investment

Be specific about time estimates and expected impact.""",

        "strategic_priorities": """You are a digital strategy consultant creating a transformation roadmap.
Think about:
- Root causes, not just symptoms
- Industry best practices and competitive positioning
- Long-term sustainability and scalability
- Return on investment for each recommendation

Focus on initiatives that would transform the site's performance.""",

        "lovable_concept": """You are an expert web designer creating concepts for modern, high-converting websites.
Your designs should:
- Follow current design trends (2024-2025)
- Prioritize mobile experience
- Optimize for conversion
- Load fast and perform well
- Reflect the brand's positioning in their market

Write prompts that can be used directly with AI website builders like Lovable.dev.""",

        "category_insight": """You are a web expert providing brief, actionable insights.
Be concise - one sentence summarizing the key issue and opportunity for this category.
Focus on business impact, not technical details.""",
    }

    def __init__(self):
        """Initialize templates with config."""
        self.config = get_config()
        self.templates_dir = self.config.templates_dir / "prompts"

    def get_system_prompt(self, template_name: str) -> str:
        """
        Get system prompt for a template.
        Tries file first, falls back to built-in.

        Args:
            template_name: Name of the template (e.g., "executive_summary")

        Returns:
            System prompt text
        """
        # Try loading from file
        template_path = self.templates_dir / f"{template_name}.txt"
        if template_path.exists():
            return template_path.read_text()

        # Fall back to built-in
        return self.FALLBACK_TEMPLATES.get(
            template_name,
            "You are a helpful website audit assistant."
        )

    def get_industry_template(self, business_type: str) -> Optional[str]:
        """
        Get industry-specific template if available.

        Args:
            business_type: Business type (e.g., "real_estate")

        Returns:
            Industry template text or None
        """
        industry_path = self.templates_dir / "industry" / f"{business_type}.txt"
        if industry_path.exists():
            return industry_path.read_text()
        return None

    def list_available_templates(self) -> list:
        """List all available template names."""
        templates = list(self.FALLBACK_TEMPLATES.keys())

        # Add any file-based templates
        if self.templates_dir.exists():
            for f in self.templates_dir.glob("*.txt"):
                name = f.stem
                if name not in templates:
                    templates.append(name)

        return sorted(templates)
