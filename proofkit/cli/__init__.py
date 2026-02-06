"""CLI interface for ProofKit."""

# Lazy import to avoid RuntimeWarning when running as __main__
def get_app():
    """Get the CLI app instance."""
    from .main import app
    return app

# For backwards compatibility, but may trigger warning if running as module
try:
    from .main import app
except RuntimeWarning:
    app = None

__all__ = ["app", "get_app"]
