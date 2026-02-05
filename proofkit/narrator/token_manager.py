"""Manages AI token budget to stay within cost limits."""

from typing import Dict, List

from proofkit.schemas.finding import Finding
from proofkit.utils.logger import logger
from proofkit.utils.exceptions import TokenLimitError


class TokenManager:
    """
    Manages AI token budget to stay within cost limits.

    Tracks token usage across requests and enforces budget limits
    to prevent unexpected API costs.
    """

    # Estimated tokens per section
    SECTION_ESTIMATES = {
        "executive_summary": 500,
        "quick_wins": 600,
        "strategic_priorities": 700,
        "concept_bullets": 500,
        "lovable_prompt": 1000,
    }

    # Cost per 1K tokens (approximate for Claude Sonnet)
    COST_PER_1K_INPUT = 0.003
    COST_PER_1K_OUTPUT = 0.015

    def __init__(self, monthly_budget: float = 15.0):
        """
        Initialize the token manager.

        Args:
            monthly_budget: Maximum monthly spending in USD
        """
        self.monthly_budget = monthly_budget
        self.monthly_usage: Dict[str, int] = {
            "input_tokens": 0,
            "output_tokens": 0,
        }

    def estimate_usage(
        self,
        findings: List[Finding],
        generate_concept: bool = False,
    ) -> int:
        """
        Estimate tokens needed for this audit.

        Args:
            findings: List of findings to process
            generate_concept: Whether concept generation is included

        Returns:
            Estimated total token count
        """
        # Input: findings summary
        findings_text = sum(
            len(f.title) + len(f.impact) + len(f.recommendation)
            for f in findings[:15]
        )
        input_estimate = findings_text // 4  # ~4 chars per token

        # Output: all sections
        output_estimate = (
            self.SECTION_ESTIMATES["executive_summary"] +
            self.SECTION_ESTIMATES["quick_wins"] +
            self.SECTION_ESTIMATES["strategic_priorities"]
        )

        if generate_concept:
            output_estimate += (
                self.SECTION_ESTIMATES["concept_bullets"] +
                self.SECTION_ESTIMATES["lovable_prompt"]
            )

        return input_estimate + output_estimate

    def check_budget(self, estimated_tokens: int) -> None:
        """
        Check if we have budget for this request.

        Args:
            estimated_tokens: Estimated tokens for the request

        Raises:
            TokenLimitError: If estimated cost exceeds remaining budget
        """
        estimated_cost = self._estimate_cost(estimated_tokens)
        remaining_budget = self._get_remaining_budget()

        if estimated_cost > remaining_budget:
            raise TokenLimitError(
                f"Estimated cost ${estimated_cost:.2f} exceeds remaining "
                f"budget ${remaining_budget:.2f}. Try reducing findings or "
                f"disabling concept generation."
            )

        logger.debug(
            f"Token budget check: ~{estimated_tokens} tokens, "
            f"~${estimated_cost:.3f} estimated"
        )

    def record_usage(self, usage: Dict[str, int]) -> None:
        """
        Record actual token usage after API call.

        Args:
            usage: Dict with input_tokens and output_tokens
        """
        self.monthly_usage["input_tokens"] += usage.get("input_tokens", 0)
        self.monthly_usage["output_tokens"] += usage.get("output_tokens", 0)

        logger.info(
            f"Token usage: {usage.get('input_tokens', 0)} in, "
            f"{usage.get('output_tokens', 0)} out. "
            f"Monthly total: {self.monthly_usage['input_tokens']} in, "
            f"{self.monthly_usage['output_tokens']} out"
        )

    def _estimate_cost(self, total_tokens: int) -> float:
        """
        Estimate cost for tokens (assumes 1:1 input:output ratio).

        Args:
            total_tokens: Total estimated tokens

        Returns:
            Estimated cost in USD
        """
        half = total_tokens // 2
        return (
            (half / 1000) * self.COST_PER_1K_INPUT +
            (half / 1000) * self.COST_PER_1K_OUTPUT
        )

    def _get_remaining_budget(self) -> float:
        """
        Calculate remaining monthly budget.

        Returns:
            Remaining budget in USD
        """
        used = (
            (self.monthly_usage["input_tokens"] / 1000) * self.COST_PER_1K_INPUT +
            (self.monthly_usage["output_tokens"] / 1000) * self.COST_PER_1K_OUTPUT
        )
        return self.monthly_budget - used

    def get_usage_report(self) -> Dict:
        """
        Get usage statistics.

        Returns:
            Dict with usage statistics including costs and percentages
        """
        used_cost = (
            (self.monthly_usage["input_tokens"] / 1000) * self.COST_PER_1K_INPUT +
            (self.monthly_usage["output_tokens"] / 1000) * self.COST_PER_1K_OUTPUT
        )

        return {
            "input_tokens": self.monthly_usage["input_tokens"],
            "output_tokens": self.monthly_usage["output_tokens"],
            "total_tokens": sum(self.monthly_usage.values()),
            "estimated_cost": round(used_cost, 3),
            "remaining_budget": round(self.monthly_budget - used_cost, 2),
            "budget_used_percent": round((used_cost / self.monthly_budget) * 100, 1),
        }

    def reset_usage(self) -> None:
        """Reset monthly usage counters."""
        self.monthly_usage = {
            "input_tokens": 0,
            "output_tokens": 0,
        }
