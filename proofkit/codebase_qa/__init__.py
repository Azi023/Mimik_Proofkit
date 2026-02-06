"""
Codebase QA Module - Analyze codebases and generate tests.

This module provides tools to:
- Analyze codebase structure and architecture
- Discover components, functions, and dependencies
- Generate test scripts for discovered code
- Create documentation and README files
- Provide AI-powered code insights
- Generate visual HTML reports with charts
"""

from .analyzer import CodebaseAnalyzer, AnalysisResult
from .test_generator import CodebaseTestGenerator
from .visual_report import VisualReportGenerator, generate_visual_report

__all__ = [
    "CodebaseAnalyzer",
    "AnalysisResult",
    "CodebaseTestGenerator",
    "VisualReportGenerator",
    "generate_visual_report",
]
