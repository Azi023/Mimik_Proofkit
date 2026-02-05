"""Custom exceptions for ProofKit."""


class ProofKitError(Exception):
    """Base exception for ProofKit."""
    pass


# Collector exceptions
class CollectorError(ProofKitError):
    """Base exception for collector module."""
    pass


class PlaywrightError(CollectorError):
    """Playwright operation failed."""
    pass


class PlaywrightTimeoutError(PlaywrightError):
    """Playwright operation timed out."""
    pass


class LighthouseError(CollectorError):
    """Lighthouse audit failed."""
    pass


class HttpProbeError(CollectorError):
    """HTTP probe failed."""
    pass


# Analyzer exceptions
class AnalyzerError(ProofKitError):
    """Base exception for analyzer module."""
    pass


class RuleExecutionError(AnalyzerError):
    """Rule execution failed."""
    pass


class ScoringError(AnalyzerError):
    """Score calculation failed."""
    pass


# Narrator exceptions
class NarratorError(ProofKitError):
    """Base exception for narrator module."""
    pass


class AIApiError(NarratorError):
    """AI API call failed."""
    pass


class TokenLimitError(NarratorError):
    """Token limit exceeded."""
    pass


class PromptError(NarratorError):
    """Prompt template error."""
    pass


# Report exceptions
class ReportError(ProofKitError):
    """Base exception for report builder."""
    pass


class TemplateError(ReportError):
    """Report template error."""
    pass


# Configuration exceptions
class ConfigError(ProofKitError):
    """Configuration error."""
    pass


class MissingApiKeyError(ConfigError):
    """Required API key is missing."""
    pass
