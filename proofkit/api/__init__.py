"""
ProofKit API - REST API for website audits.

Provides endpoints for creating audits, checking status,
and retrieving reports.
"""

from .main import create_app, app

__all__ = ["create_app", "app"]
