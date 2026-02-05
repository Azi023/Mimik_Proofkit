"""
AI-powered narrative generation from audit findings.

The Narrator transforms technical findings into persuasive, business-focused
narratives and generates Lovable concept prompts.
"""

from typing import List, Optional, Dict

from proofkit.schemas.finding import Finding
from proofkit.schemas.report import ReportNarrative
from proofkit.schemas.business import BusinessType
from proofkit.utils.logger import logger

from .claude_client import ClaudeClient
from .narrative_builder import NarrativeBuilder
from .concept_generator import ConceptGenerator
from .token_manager import TokenManager


class Narrator:
    """
    AI-powered narrative generation from audit findings.

    Transforms technical audit findings into business-focused narratives
    including executive summaries, quick wins, strategic priorities,
    and Lovable redesign prompts.
    """

    def __init__(self):
        """Initialize the Narrator with AI client and builders."""
        self.client = ClaudeClient()
        self.builder = NarrativeBuilder(self.client)
        self.concept_gen = ConceptGenerator(self.client)
        self.token_manager = TokenManager()

    def generate(
        self,
        findings: List[Finding],
        business_type: Optional[BusinessType] = None,
        conversion_goal: Optional[str] = None,
        generate_concept: bool = False,
    ) -> ReportNarrative:
        """
        Generate narrative from findings.

        Args:
            findings: List of findings from Analyzer
            business_type: Business context for tailored language
            conversion_goal: Primary conversion goal (inquiries, bookings, etc.)
            generate_concept: Whether to generate Lovable concept prompts

        Returns:
            ReportNarrative with all narrative content
        """
        logger.info(f"Generating narrative for {len(findings)} findings")

        # Budget check
        estimated_tokens = self.token_manager.estimate_usage(findings, generate_concept)
        self.token_manager.check_budget(estimated_tokens)

        # Prepare findings summary for AI
        findings_summary = self._prepare_findings_summary(findings)

        # Generate narrative sections
        logger.debug("Generating executive summary")
        executive_summary = self.builder.generate_executive_summary(
            findings_summary,
            business_type,
            conversion_goal,
        )

        logger.debug("Generating quick wins")
        quick_wins = self.builder.generate_quick_wins(findings_summary)

        logger.debug("Generating strategic priorities")
        strategic_priorities = self.builder.generate_strategic_priorities(
            findings_summary,
            business_type,
        )

        # Generate category insights
        category_insights = self._generate_category_insights(findings, business_type)

        # Generate concept prompts if requested
        lovable_concept = None
        if generate_concept:
            logger.debug("Generating Lovable concept")
            lovable_concept = self.concept_gen.generate_lovable_prompt(
                findings_summary,
                business_type,
            )

        # Track actual token usage
        self.token_manager.record_usage(self.client.get_total_usage())

        logger.info("Narrative generation complete")

        return ReportNarrative(
            executive_summary=executive_summary,
            quick_wins=quick_wins,
            strategic_priorities=strategic_priorities,
            category_insights=category_insights,
            lovable_concept=lovable_concept,
        )

    def _prepare_findings_summary(self, findings: List[Finding]) -> str:
        """
        Prepare findings for AI consumption.
        Limit to top findings to save tokens.
        """
        # Take top 15 findings by severity
        severity_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
        top_findings = sorted(
            findings,
            key=lambda f: severity_order.get(
                f.severity.value if hasattr(f.severity, "value") else str(f.severity),
                4
            )
        )[:15]

        summary_lines = []
        for f in top_findings:
            severity = f.severity.value if hasattr(f.severity, "value") else str(f.severity)
            category = f.category.value if hasattr(f.category, "value") else str(f.category)
            summary_lines.append(
                f"[{severity}] {category}: {f.title}\n"
                f"  Impact: {f.impact}\n"
                f"  Fix: {f.recommendation}"
            )

        return "\n\n".join(summary_lines)

    def _generate_category_insights(
        self,
        findings: List[Finding],
        business_type: Optional[BusinessType] = None,
    ) -> Dict[str, str]:
        """Generate brief insights for each category with findings."""
        # Group findings by category
        by_category: Dict[str, List[Finding]] = {}
        for f in findings:
            cat = f.category.value if hasattr(f.category, "value") else str(f.category)
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(f)

        insights = {}
        for category, cat_findings in by_category.items():
            if not cat_findings:
                continue

            # Count severities
            p0_count = sum(1 for f in cat_findings if self._get_severity(f) == "P0")
            p1_count = sum(1 for f in cat_findings if self._get_severity(f) == "P1")

            # Generate simple insight
            if p0_count > 0:
                insights[category] = f"{p0_count} critical issues require immediate attention"
            elif p1_count > 0:
                insights[category] = f"{p1_count} high-priority improvements identified"
            else:
                insights[category] = f"{len(cat_findings)} opportunities for improvement"

        return insights

    def _get_severity(self, finding: Finding) -> str:
        """Get severity value from finding."""
        if hasattr(finding.severity, "value"):
            return finding.severity.value
        return str(finding.severity)

    def get_usage_report(self) -> Dict:
        """Get token usage statistics."""
        return self.token_manager.get_usage_report()


__all__ = [
    "Narrator",
    "ClaudeClient",
    "NarrativeBuilder",
    "ConceptGenerator",
    "TokenManager",
]
