"""
Claude Client - Now uses AIClientFactory for provider flexibility.
Kept for backwards compatibility with existing code.
"""

from typing import Optional, Dict

from proofkit.utils.logger import logger
from .ai_client import get_ai_client, BaseAIClient, AIClientFactory


class ClaudeClient:
    """
    Wrapper for AI client that maintains backwards compatibility.
    Actual implementation delegated to AIClientFactory.

    This class preserves the original interface while allowing
    seamless switching between AI providers (OpenAI, Anthropic).
    """

    def __init__(self):
        """Initialize the Claude client with the configured AI provider."""
        self._client: BaseAIClient = get_ai_client()
        logger.debug(f"ClaudeClient initialized with {type(self._client).__name__}")

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate completion from configured AI provider.

        Args:
            system_prompt: System context for the AI
            user_prompt: User message/request
            max_tokens: Override default max tokens (default: 1500)

        Returns:
            Generated text response

        Raises:
            AIApiError: If API call fails
        """
        return self._client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens or 1500,
        )

    def get_last_usage(self) -> Dict[str, int]:
        """Get token usage from last request."""
        return self._client.get_last_usage()

    def get_total_usage(self) -> Dict[str, int]:
        """Get total token usage across all requests."""
        if hasattr(self._client, 'get_total_usage'):
            return self._client.get_total_usage()
        return {"input_tokens": 0, "output_tokens": 0}

    def reset_usage(self) -> None:
        """Reset usage counters."""
        if hasattr(self._client, 'reset_usage'):
            self._client.reset_usage()

    def estimate_tokens(self, text: str) -> int:
        """
        Rough estimate of token count.
        Both Claude and GPT use ~4 chars per token on average.

        Args:
            text: Text to estimate tokens for

        Returns:
            Estimated token count
        """
        return len(text) // 4

    @staticmethod
    def reset_factory() -> None:
        """Reset the AI client factory (useful for testing)."""
        AIClientFactory.reset()
