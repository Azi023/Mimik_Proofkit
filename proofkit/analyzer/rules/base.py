"""Base class for all analyzer rules."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from proofkit.schemas.finding import Finding, Evidence, Severity, Category, Effort
from proofkit.schemas.business import BusinessType
from proofkit.collector.models import RawData


class BaseRule(ABC):
    """
    Base class for all analyzer rules.

    Subclasses should:
    - Set the `category` class attribute
    - Implement the `run()` method
    - Use `add_finding()` to record issues
    """

    category: Category = Category.UX  # Override in subclass

    def __init__(
        self,
        raw_data: RawData,
        business_type: Optional[BusinessType] = None,
    ):
        """
        Initialize the rule with collected data.

        Args:
            raw_data: Raw data from collectors
            business_type: Optional business type for context-aware rules
        """
        self.raw_data = raw_data
        self.business_type = business_type
        self.findings: List[Finding] = []
        self._finding_counter: Dict[str, int] = {}

    @abstractmethod
    def run(self) -> List[Finding]:
        """
        Execute the rule and return findings.

        Returns:
            List of Finding objects
        """
        pass

    def add_finding(
        self,
        id: str,
        severity: Severity,
        title: str,
        summary: str,
        impact: str,
        recommendation: str,
        effort: Effort = Effort.M,
        evidence: Optional[List[Evidence]] = None,
        tags: Optional[List[str]] = None,
        confidence: float = 1.0,
    ) -> Finding:
        """
        Add a finding to the results.

        Args:
            id: Unique finding ID (e.g., "SEO-H1-001")
            severity: Finding severity (P0-P3)
            title: Short title
            summary: Detailed summary
            impact: Business impact description
            recommendation: How to fix
            effort: Estimated fix effort (S/M/L)
            evidence: Supporting evidence
            tags: Additional tags for categorization
            confidence: Detection confidence (0-1)

        Returns:
            The created Finding object
        """
        # Ensure unique ID by adding counter if needed
        if id in self._finding_counter:
            self._finding_counter[id] += 1
            id = f"{id}-{self._finding_counter[id]}"
        else:
            self._finding_counter[id] = 1

        finding = Finding(
            id=id,
            category=self.category,
            severity=severity,
            title=title,
            summary=summary,
            impact=impact,
            recommendation=recommendation,
            effort=effort,
            evidence=evidence or [],
            tags=tags or [],
            confidence=confidence,
        )

        self.findings.append(finding)
        return finding

    def evidence_from_page(
        self,
        url: str,
        selector: Optional[str] = None,
        screenshot_path: Optional[str] = None,
        note: Optional[str] = None,
        metric: Optional[Dict[str, str]] = None,
    ) -> Evidence:
        """
        Create an Evidence object from page data.

        Args:
            url: Page URL
            selector: CSS selector if applicable
            screenshot_path: Path to screenshot
            note: Additional note
            metric: Metric data if applicable

        Returns:
            Evidence object
        """
        return Evidence(
            url=url,
            selector=selector,
            screenshot_path=screenshot_path,
            note=note,
            metric=metric,
        )

    def evidence_with_metric(
        self,
        url: str,
        metric_name: str,
        metric_value: Any,
        threshold: Optional[Any] = None,
    ) -> Evidence:
        """
        Create evidence with metric data.

        Args:
            url: Page URL
            metric_name: Name of the metric
            metric_value: Actual value
            threshold: Expected threshold (if applicable)

        Returns:
            Evidence object with metric data
        """
        metric = {metric_name: str(metric_value)}
        if threshold is not None:
            metric["threshold"] = str(threshold)

        return Evidence(url=url, metric=metric)

    def _page_name(self, url: str) -> str:
        """Extract readable page name from URL."""
        path = url.rstrip("/").split("/")[-1]
        if not path or path == url:
            return "homepage"
        # Clean up query params
        path = path.split("?")[0]
        return path or "homepage"

    def _get_homepage(self):
        """Get the homepage snapshot if available."""
        for page in self.raw_data.snapshot.pages:
            if self._page_name(page.url) == "homepage":
                return page
        # Return first page as fallback
        if self.raw_data.snapshot.pages:
            return self.raw_data.snapshot.pages[0]
        return None
