"""
Unified AI Client - Supports both Anthropic Claude and OpenAI GPT models.
Allows seamless switching between providers via environment variable.
"""

import os
from pathlib import Path
from typing import Optional, Dict
from abc import ABC, abstractmethod

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    # Try to find .env in current dir or parent directories
    env_path = Path.cwd() / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        # Try common project root locations
        for parent in Path.cwd().parents:
            env_path = parent / ".env"
            if env_path.exists():
                load_dotenv(env_path)
                break
except ImportError:
    pass  # dotenv not installed, rely on environment variables

from proofkit.utils.config import get_config
from proofkit.utils.logger import logger
from proofkit.utils.exceptions import AIApiError


class BaseAIClient(ABC):
    """Abstract base class for AI clients."""

    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1500,
    ) -> str:
        """Generate completion from AI model."""
        pass

    @abstractmethod
    def get_last_usage(self) -> Dict[str, int]:
        """Get token usage from last request."""
        pass


class OpenAIClient(BaseAIClient):
    """OpenAI GPT client implementation."""

    def __init__(self):
        try:
            from openai import OpenAI
        except ImportError:
            raise AIApiError("OpenAI package not installed. Run: pip install openai")

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise AIApiError("OPENAI_API_KEY not set in environment")

        self.client = OpenAI(api_key=api_key)
        # Use gpt-4o-mini for cost efficiency (~$0.15/1M input, $0.60/1M output)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self._last_usage: Dict[str, int] = {}
        self._total_usage: Dict[str, int] = {"input_tokens": 0, "output_tokens": 0}

        logger.info(f"OpenAI client initialized with model: {self.model}")

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1500,
    ) -> str:
        """Generate completion using OpenAI."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7,
            )

            # Track usage
            if response.usage:
                self._last_usage = {
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens,
                }
                # Accumulate total usage
                self._total_usage["input_tokens"] += response.usage.prompt_tokens
                self._total_usage["output_tokens"] += response.usage.completion_tokens

            logger.debug(
                f"OpenAI API: {self._last_usage.get('input_tokens', 0)} in, "
                f"{self._last_usage.get('output_tokens', 0)} out"
            )

            return response.choices[0].message.content or ""

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise AIApiError(f"OpenAI API error: {e}")

    def get_last_usage(self) -> Dict[str, int]:
        return self._last_usage.copy()

    def get_total_usage(self) -> Dict[str, int]:
        """Get total token usage across all requests."""
        return self._total_usage.copy()

    def reset_usage(self) -> None:
        """Reset usage counters."""
        self._last_usage = {}
        self._total_usage = {"input_tokens": 0, "output_tokens": 0}


class AnthropicClient(BaseAIClient):
    """Anthropic Claude client implementation."""

    def __init__(self):
        try:
            import anthropic
        except ImportError:
            raise AIApiError("Anthropic package not installed. Run: pip install anthropic")

        config = get_config()
        api_key = config.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise AIApiError("ANTHROPIC_API_KEY not set in environment")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = os.getenv("ANTHROPIC_MODEL", config.ai_model)
        self._last_usage: Dict[str, int] = {}
        self._total_usage: Dict[str, int] = {"input_tokens": 0, "output_tokens": 0}

        logger.info(f"Anthropic client initialized with model: {self.model}")

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1500,
    ) -> str:
        """Generate completion using Anthropic Claude."""
        try:
            import anthropic

            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ],
            )

            # Track usage
            self._last_usage = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            }
            # Accumulate total usage
            self._total_usage["input_tokens"] += response.usage.input_tokens
            self._total_usage["output_tokens"] += response.usage.output_tokens

            logger.debug(
                f"Anthropic API: {self._last_usage['input_tokens']} in, "
                f"{self._last_usage['output_tokens']} out"
            )

            return response.content[0].text

        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise AIApiError(f"Anthropic API error: {e}")

    def get_last_usage(self) -> Dict[str, int]:
        return self._last_usage.copy()

    def get_total_usage(self) -> Dict[str, int]:
        """Get total token usage across all requests."""
        return self._total_usage.copy()

    def reset_usage(self) -> None:
        """Reset usage counters."""
        self._last_usage = {}
        self._total_usage = {"input_tokens": 0, "output_tokens": 0}


class AIClientFactory:
    """Factory for creating AI clients based on configuration."""

    _instance: Optional[BaseAIClient] = None

    @classmethod
    def get_client(cls) -> BaseAIClient:
        """Get or create the AI client singleton."""
        if cls._instance is None:
            provider = os.getenv("AI_PROVIDER", "anthropic").lower()

            if provider == "openai":
                cls._instance = OpenAIClient()
            elif provider == "anthropic":
                cls._instance = AnthropicClient()
            else:
                raise AIApiError(f"Unknown AI provider: {provider}")

            logger.info(f"AI Client initialized: {provider}")

        return cls._instance

    @classmethod
    def reset(cls):
        """Reset the client (useful for testing)."""
        cls._instance = None


# Convenience function
def get_ai_client() -> BaseAIClient:
    """Get the configured AI client."""
    return AIClientFactory.get_client()
