"""
Intelligent QA Module - Automatic feature discovery and test generation.

This module automatically discovers interactive features on web pages
and generates Playwright test scripts for them.
"""

from .feature_discovery import FeatureDiscovery, DiscoveredFeature, FeatureType
from .test_generator import TestGenerator

__all__ = [
    "FeatureDiscovery",
    "DiscoveredFeature",
    "FeatureType",
    "TestGenerator",
]
