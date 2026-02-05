"""Builds narrative sections from findings using AI."""

from typing import List, Optional

from proofkit.schemas.business import BusinessType

from .claude_client import ClaudeClient
from .prompts import PromptTemplates


class NarrativeBuilder:
    """
    Builds narrative sections from findings using AI.

    Generates executive summaries, quick wins, and strategic
    priorities from audit findings.
    """

    def __init__(self, client: ClaudeClient):
        """
        Initialize the narrative builder.

        Args:
            client: Claude client for AI generation
        """
        self.client = client
        self.templates = PromptTemplates()

    def generate_executive_summary(
        self,
        findings_summary: str,
        business_type: Optional[BusinessType] = None,
        conversion_goal: Optional[str] = None,
    ) -> str:
        """
        Generate executive summary for report.
        Target: 3-4 sentences, business-focused.

        Args:
            findings_summary: Prepared findings text
            business_type: Business context
            conversion_goal: Primary conversion goal

        Returns:
            Executive summary text
        """
        system_prompt = self.templates.get_system_prompt("executive_summary")

        business_context = "General business website"
        if business_type:
            business_context = business_type.value.replace("_", " ").title()

        user_prompt = f"""
Business Type: {business_context}
Conversion Goal: {conversion_goal or "Lead generation / inquiries"}

Audit Findings:
{findings_summary}

Write a concise executive summary (3-4 sentences) that:
1. Leads with the most critical business impact
2. Quantifies the problem where possible
3. Hints at the transformation potential
4. Maintains professional but confident tone

Do NOT use bullet points. Write in flowing prose.
"""

        return self.client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=400,
        )

    def generate_quick_wins(self, findings_summary: str) -> List[str]:
        """
        Generate quick wins list.
        Target: 3-5 items that can be fixed in days with high impact.

        Args:
            findings_summary: Prepared findings text

        Returns:
            List of quick win recommendations
        """
        system_prompt = self.templates.get_system_prompt("quick_wins")

        user_prompt = f"""
Audit Findings:
{findings_summary}

Identify 3-5 "Quick Wins" - fixes that:
- Can be implemented in hours to days (not weeks)
- Have high impact on conversion or user experience
- Don't require major redesign or infrastructure changes

Format each as a single line:
- [Fix description] ([time estimate], [impact level])

Example:
- Add WhatsApp CTA to header (2 hours, high conversion impact)
- Convert hero images to WebP format (1 day, 3-5s faster load)
"""

        response = self.client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=500,
        )

        # Parse response into list
        lines = response.strip().split("\n")
        quick_wins = [
            line.strip().lstrip("- •").strip()
            for line in lines
            if line.strip() and not line.startswith("#") and len(line.strip()) > 10
        ]

        return quick_wins[:5]

    def generate_strategic_priorities(
        self,
        findings_summary: str,
        business_type: Optional[BusinessType] = None,
    ) -> List[str]:
        """
        Generate strategic priority recommendations.
        Target: 3-5 items that require more investment but transform the site.

        Args:
            findings_summary: Prepared findings text
            business_type: Business context

        Returns:
            List of strategic priority recommendations
        """
        system_prompt = self.templates.get_system_prompt("strategic_priorities")

        industry_context = ""
        if business_type:
            industry_context = f"Industry: {business_type.value.replace('_', ' ').title()}. Consider industry-specific best practices."

        user_prompt = f"""
{industry_context}

Audit Findings:
{findings_summary}

Identify 3-5 Strategic Priorities - investments that:
- Require more effort (weeks, not days)
- Would significantly transform site performance or conversion
- Address root causes, not just symptoms
- Position the business competitively in their industry

Format each as a single line explaining the initiative and expected outcome.
Do not number the items.
"""

        response = self.client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=600,
        )

        # Parse response into list
        lines = response.strip().split("\n")
        priorities = [
            line.strip().lstrip("- •0123456789.").strip()
            for line in lines
            if line.strip() and len(line.strip()) > 20
        ]

        return priorities[:5]
