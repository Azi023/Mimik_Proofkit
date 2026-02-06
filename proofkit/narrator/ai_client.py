"""
Unified AI Client - Supports multiple AI providers and models.

Allows flexible model selection based on task requirements:
- Fast models for simple tasks (gpt-4o-mini, claude-3-haiku)
- Balanced models for most tasks (gpt-4o, claude-3-sonnet)
- Powerful models for complex analysis (gpt-4-turbo, claude-3-opus, o1)
"""

import os
from pathlib import Path
from typing import Optional, Dict, Literal
from abc import ABC, abstractmethod
from enum import Enum


# Load .env file if it exists
def _load_env():
    """Load .env file from multiple possible locations."""
    try:
        from dotenv import load_dotenv

        # Possible locations for .env
        possible_paths = [
            Path.cwd() / ".env",
            Path(__file__).parent.parent.parent / ".env",  # proofkit/../.env
            Path(__file__).parent.parent.parent.parent / ".env",  # Mimik_Proofkit/.env
            Path.home() / ".proofkit" / ".env",  # User home
        ]

        # Also check parent directories of cwd
        for parent in Path.cwd().parents:
            possible_paths.append(parent / ".env")
            if parent.name in ["Mimik_Proofkit", "proofkit"]:
                break

        for env_path in possible_paths:
            if env_path.exists():
                load_dotenv(env_path, override=True)
                print(f"[ProofKit] Loaded .env from: {env_path}")
                return True

        print("[ProofKit] Warning: No .env file found")
        return False
    except ImportError:
        print("[ProofKit] Warning: python-dotenv not installed")
        return False

_load_env()

from proofkit.utils.config import get_config
from proofkit.utils.logger import logger
from proofkit.utils.exceptions import AIApiError


class ModelTier(Enum):
    """Model capability tiers for different tasks."""
    FAST = "fast"           # Quick, simple tasks - lowest cost
    BALANCED = "balanced"   # Most tasks - good balance of speed/quality
    POWERFUL = "powerful"   # Complex analysis - highest quality
    REASONING = "reasoning" # Deep reasoning tasks (o1, etc.)


# Model mappings by provider and tier
OPENAI_MODELS = {
    ModelTier.FAST: "gpt-4o-mini",
    ModelTier.BALANCED: "gpt-4o",
    ModelTier.POWERFUL: "gpt-4-turbo",
    ModelTier.REASONING: "o1-mini",  # or "o1-preview" for even more powerful
}

ANTHROPIC_MODELS = {
    ModelTier.FAST: "claude-3-haiku-20240307",
    ModelTier.BALANCED: "claude-sonnet-4-20250514",
    ModelTier.POWERFUL: "claude-opus-4-20250514",
    ModelTier.REASONING: "claude-opus-4-20250514",
}

# Task to model tier mapping
TASK_MODEL_MAPPING = {
    "quick_summary": ModelTier.FAST,
    "executive_summary": ModelTier.BALANCED,
    "quick_wins": ModelTier.FAST,
    "strategic_priorities": ModelTier.BALANCED,
    "concept_generation": ModelTier.BALANCED,
    "code_analysis": ModelTier.POWERFUL,
    "complex_reasoning": ModelTier.REASONING,
    "test_generation": ModelTier.BALANCED,
    "default": ModelTier.BALANCED,
}


class BaseAIClient(ABC):
    """Abstract base class for AI clients."""

    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1500,
        model_override: Optional[str] = None,
        task_type: Optional[str] = None,
    ) -> str:
        """Generate completion from AI model."""
        pass

    @abstractmethod
    def get_last_usage(self) -> Dict[str, int]:
        """Get token usage from last request."""
        pass

    @abstractmethod
    def list_available_models(self) -> Dict[str, str]:
        """List available models with descriptions."""
        pass


class OpenAIClient(BaseAIClient):
    """OpenAI GPT client implementation with multi-model support."""

    AVAILABLE_MODELS = {
        "gpt-4o-mini": "Fast & cheap - good for simple tasks ($0.15/1M in, $0.60/1M out)",
        "gpt-4o": "Balanced - good for most tasks ($2.50/1M in, $10/1M out)",
        "gpt-4-turbo": "Powerful - complex analysis ($10/1M in, $30/1M out)",
        "gpt-4": "Original GPT-4 - high quality ($30/1M in, $60/1M out)",
        "o1-mini": "Reasoning model - deep thinking ($3/1M in, $12/1M out)",
        "o1-preview": "Advanced reasoning - most powerful ($15/1M in, $60/1M out)",
        "gpt-3.5-turbo": "Legacy fast model - very cheap ($0.50/1M in, $1.50/1M out)",
    }

    def __init__(self, default_model: Optional[str] = None):
        try:
            from openai import OpenAI
        except ImportError:
            raise AIApiError("OpenAI package not installed. Run: pip install openai")

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise AIApiError("OPENAI_API_KEY not set in environment")

        self.client = OpenAI(api_key=api_key)
        self.default_model = default_model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self._last_usage: Dict[str, int] = {}
        self._total_usage: Dict[str, int] = {"input_tokens": 0, "output_tokens": 0}
        self._last_model_used: str = ""

        logger.info(f"OpenAI client initialized with default model: {self.default_model}")

    def _get_model_for_task(self, task_type: Optional[str]) -> str:
        """Get appropriate model based on task type."""
        if not task_type:
            return self.default_model

        tier = TASK_MODEL_MAPPING.get(task_type, ModelTier.BALANCED)
        return OPENAI_MODELS.get(tier, self.default_model)

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1500,
        model_override: Optional[str] = None,
        task_type: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate completion using OpenAI.

        Args:
            system_prompt: System context
            user_prompt: User message
            max_tokens: Maximum tokens in response
            model_override: Specific model to use (overrides task-based selection)
            task_type: Type of task for automatic model selection
            temperature: Creativity level (0-1)

        Returns:
            Generated text
        """
        # Determine model to use
        if model_override:
            model = model_override
        elif task_type:
            model = self._get_model_for_task(task_type)
        else:
            model = self.default_model

        self._last_model_used = model

        try:
            # Handle reasoning models differently (o1 series)
            if model.startswith("o1"):
                # o1 models don't support system prompts or temperature
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "user", "content": f"{system_prompt}\n\n{user_prompt}"}
                    ],
                    max_completion_tokens=max_tokens,
                )
            else:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature,
                )

            # Track usage
            if response.usage:
                self._last_usage = {
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens,
                    "model": model,
                }
                self._total_usage["input_tokens"] += response.usage.prompt_tokens
                self._total_usage["output_tokens"] += response.usage.completion_tokens

            logger.debug(
                f"OpenAI [{model}]: {self._last_usage.get('input_tokens', 0)} in, "
                f"{self._last_usage.get('output_tokens', 0)} out"
            )

            return response.choices[0].message.content or ""

        except Exception as e:
            logger.error(f"OpenAI API error ({model}): {e}")
            raise AIApiError(f"OpenAI API error: {e}")

    def get_last_usage(self) -> Dict[str, int]:
        return self._last_usage.copy()

    def get_total_usage(self) -> Dict[str, int]:
        return self._total_usage.copy()

    def reset_usage(self) -> None:
        self._last_usage = {}
        self._total_usage = {"input_tokens": 0, "output_tokens": 0}

    def list_available_models(self) -> Dict[str, str]:
        return self.AVAILABLE_MODELS.copy()

    def get_last_model_used(self) -> str:
        return self._last_model_used


class AnthropicClient(BaseAIClient):
    """Anthropic Claude client implementation with multi-model support."""

    AVAILABLE_MODELS = {
        "claude-3-haiku-20240307": "Fast & cheap - simple tasks ($0.25/1M in, $1.25/1M out)",
        "claude-sonnet-4-20250514": "Balanced - most tasks ($3/1M in, $15/1M out)",
        "claude-opus-4-20250514": "Powerful - complex analysis ($15/1M in, $75/1M out)",
        "claude-3-5-sonnet-20241022": "Latest Sonnet - great balance ($3/1M in, $15/1M out)",
    }

    def __init__(self, default_model: Optional[str] = None):
        try:
            import anthropic
        except ImportError:
            raise AIApiError("Anthropic package not installed. Run: pip install anthropic")

        config = get_config()
        api_key = config.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise AIApiError("ANTHROPIC_API_KEY not set in environment")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.default_model = default_model or os.getenv("ANTHROPIC_MODEL", config.ai_model)
        self._last_usage: Dict[str, int] = {}
        self._total_usage: Dict[str, int] = {"input_tokens": 0, "output_tokens": 0}
        self._last_model_used: str = ""

        logger.info(f"Anthropic client initialized with default model: {self.default_model}")

    def _get_model_for_task(self, task_type: Optional[str]) -> str:
        """Get appropriate model based on task type."""
        if not task_type:
            return self.default_model

        tier = TASK_MODEL_MAPPING.get(task_type, ModelTier.BALANCED)
        return ANTHROPIC_MODELS.get(tier, self.default_model)

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1500,
        model_override: Optional[str] = None,
        task_type: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate completion using Anthropic Claude.

        Args:
            system_prompt: System context
            user_prompt: User message
            max_tokens: Maximum tokens in response
            model_override: Specific model to use
            task_type: Type of task for automatic model selection
            temperature: Creativity level (0-1)

        Returns:
            Generated text
        """
        # Determine model to use
        if model_override:
            model = model_override
        elif task_type:
            model = self._get_model_for_task(task_type)
        else:
            model = self.default_model

        self._last_model_used = model

        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
            )

            # Track usage
            self._last_usage = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "model": model,
            }
            self._total_usage["input_tokens"] += response.usage.input_tokens
            self._total_usage["output_tokens"] += response.usage.output_tokens

            logger.debug(
                f"Anthropic [{model}]: {self._last_usage['input_tokens']} in, "
                f"{self._last_usage['output_tokens']} out"
            )

            return response.content[0].text

        except Exception as e:
            logger.error(f"Anthropic API error ({model}): {e}")
            raise AIApiError(f"Anthropic API error: {e}")

    def get_last_usage(self) -> Dict[str, int]:
        return self._last_usage.copy()

    def get_total_usage(self) -> Dict[str, int]:
        return self._total_usage.copy()

    def reset_usage(self) -> None:
        self._last_usage = {}
        self._total_usage = {"input_tokens": 0, "output_tokens": 0}

    def list_available_models(self) -> Dict[str, str]:
        return self.AVAILABLE_MODELS.copy()

    def get_last_model_used(self) -> str:
        return self._last_model_used


class AIClientFactory:
    """Factory for creating AI clients based on configuration."""

    _instance: Optional[BaseAIClient] = None
    _provider: Optional[str] = None

    @classmethod
    def get_client(cls, provider: Optional[str] = None, model: Optional[str] = None) -> BaseAIClient:
        """
        Get or create the AI client.

        Args:
            provider: 'openai' or 'anthropic' (default from env)
            model: Default model to use

        Returns:
            Configured AI client
        """
        requested_provider = provider or os.getenv("AI_PROVIDER", "anthropic").lower()

        # Create new instance if provider changed or first time
        if cls._instance is None or cls._provider != requested_provider:
            if requested_provider == "openai":
                cls._instance = OpenAIClient(default_model=model)
            elif requested_provider == "anthropic":
                cls._instance = AnthropicClient(default_model=model)
            else:
                raise AIApiError(f"Unknown AI provider: {requested_provider}")

            cls._provider = requested_provider
            logger.info(f"AI Client initialized: {requested_provider}")

        return cls._instance

    @classmethod
    def reset(cls):
        """Reset the client (useful for testing or switching providers)."""
        cls._instance = None
        cls._provider = None

    @classmethod
    def get_provider(cls) -> Optional[str]:
        """Get current provider name."""
        return cls._provider


# Convenience functions
def get_ai_client(provider: Optional[str] = None, model: Optional[str] = None) -> BaseAIClient:
    """Get the configured AI client."""
    return AIClientFactory.get_client(provider=provider, model=model)


def list_available_models() -> Dict[str, Dict[str, str]]:
    """List all available models from all providers."""
    return {
        "openai": OpenAIClient.AVAILABLE_MODELS,
        "anthropic": AnthropicClient.AVAILABLE_MODELS,
    }


def get_model_for_task(task_type: str, provider: Optional[str] = None) -> str:
    """
    Get recommended model for a specific task type.

    Args:
        task_type: Type of task (e.g., 'executive_summary', 'code_analysis')
        provider: AI provider ('openai' or 'anthropic')

    Returns:
        Recommended model name
    """
    provider = provider or os.getenv("AI_PROVIDER", "anthropic").lower()
    tier = TASK_MODEL_MAPPING.get(task_type, ModelTier.BALANCED)

    if provider == "openai":
        return OPENAI_MODELS.get(tier, "gpt-4o-mini")
    else:
        return ANTHROPIC_MODELS.get(tier, "claude-sonnet-4-20250514")
