"""
Finding Deduplication Engine

Consolidates duplicate and similar findings into single, impactful entries.
Reduces finding count from 400+ to 50-80 unique, actionable items.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from collections import defaultdict
import re
from difflib import SequenceMatcher

from proofkit.schemas.finding import Finding, Severity, Effort, Category, Evidence
from proofkit.utils.logger import logger


@dataclass
class ConsolidatedFinding:
    """A finding that may represent multiple occurrences."""
    original: Finding
    occurrences: int
    affected_pages: List[str]
    examples: List[str]  # Up to 3 specific examples


class FindingDeduplicator:
    """
    Deduplicates and consolidates findings.

    Rules:
    1. Exact duplicates → Merge with count
    2. Similar titles (>80% match) → Merge with examples
    3. Same rule ID on different pages → Consolidate
    4. Low severity duplicates → Keep only 1 representative
    """

    SIMILARITY_THRESHOLD = 0.8
    MAX_EXAMPLES = 3

    def __init__(self, findings: List[Finding]):
        self.findings = findings
        self.consolidated: List[ConsolidatedFinding] = []
        self._stats = {
            "original_count": len(findings),
            "after_rule_id_dedup": 0,
            "after_similarity_dedup": 0,
            "duplicates_merged": 0,
        }

    def deduplicate(self) -> List[Finding]:
        """
        Main deduplication process.

        Returns:
            Deduplicated list of findings
        """
        if not self.findings:
            return []

        logger.info(f"Starting deduplication of {len(self.findings)} findings")

        # Step 1: Group by rule_id (finding.id prefix)
        by_rule = defaultdict(list)
        for f in self.findings:
            rule_id = self._get_rule_id(f)
            by_rule[rule_id].append(f)

        deduplicated = []

        for rule_id, group in by_rule.items():
            if len(group) == 1:
                deduplicated.append(group[0])
            else:
                # Consolidate duplicates
                consolidated = self._consolidate_group(group)
                deduplicated.append(consolidated)
                self._stats["duplicates_merged"] += len(group) - 1

        self._stats["after_rule_id_dedup"] = len(deduplicated)
        logger.debug(f"After rule ID dedup: {len(deduplicated)} findings")

        # Step 2: Similarity-based deduplication for remaining findings
        final = self._dedupe_by_similarity(deduplicated)

        self._stats["after_similarity_dedup"] = len(final)
        logger.info(
            f"Deduplication complete: {self._stats['original_count']} → {len(final)} findings "
            f"({self._stats['duplicates_merged']} merged)"
        )

        return final

    def get_stats(self) -> Dict[str, int]:
        """Return deduplication statistics."""
        return self._stats

    def _get_rule_id(self, finding: Finding) -> str:
        """
        Extract or generate a rule ID for grouping.

        The finding.id is usually like "UX-CTA-001", so we use the prefix
        without the page-specific suffix for grouping.
        """
        # Use the base ID without any numeric suffix that might be page-specific
        base_id = finding.id

        # Also create a normalized title key for additional grouping
        title_key = self._normalize_title(finding.title)

        # Combine category and normalized title as the rule identifier
        category = finding.category.value if hasattr(finding.category, 'value') else finding.category
        return f"{category}_{title_key}"

    def _normalize_title(self, title: str) -> str:
        """Normalize title for comparison."""
        # Remove page-specific info like URLs
        title = re.sub(r'https?://\S+', '', title)
        # Remove numbers that might be page-specific
        title = re.sub(r'\(\d+ occurrences?\)', '', title)
        # Normalize whitespace and case
        title = title.lower().strip()
        title = re.sub(r'\s+', '_', title)
        title = re.sub(r'[^\w_]', '', title)
        return title[:50]  # Limit length for key

    def _consolidate_group(self, group: List[Finding]) -> Finding:
        """Consolidate multiple identical findings into one."""
        # Take the highest severity finding as primary
        severity_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
        group.sort(
            key=lambda f: severity_order.get(
                f.severity.value if hasattr(f.severity, 'value') else f.severity,
                3
            )
        )

        primary = group[0]
        count = len(group)

        # Collect affected pages from evidence
        affected_pages = []
        all_evidence = []

        for f in group:
            for ev in f.evidence:
                if ev.url and ev.url not in affected_pages:
                    affected_pages.append(ev.url)
                all_evidence.append(ev)

        # Limit evidence to MAX_EXAMPLES
        consolidated_evidence = all_evidence[:self.MAX_EXAMPLES]

        # Update title with count if multiple
        new_title = primary.title
        if count > 1:
            # Remove any existing count
            new_title = re.sub(r'\s*\(\d+ occurrences?\)', '', new_title)
            if not any(x in new_title.lower() for x in ['multiple', 'several', 'pages']):
                new_title = f"{new_title} ({count} occurrences)"

        # Update summary with scope
        new_summary = primary.summary
        if count > 1 and affected_pages:
            page_list = ', '.join(affected_pages[:3])
            if len(affected_pages) > 3:
                page_list += f" and {len(affected_pages) - 3} more"
            new_summary = f"{primary.summary}\n\nAffected pages: {page_list}"

        # Create consolidated finding
        return Finding(
            id=primary.id,
            title=new_title,
            summary=new_summary,
            category=primary.category,
            severity=primary.severity,
            impact=primary.impact,
            recommendation=primary.recommendation,
            effort=primary.effort,
            evidence=consolidated_evidence,
            tags=primary.tags,
            confidence=primary.confidence,
        )

    def _dedupe_by_similarity(self, findings: List[Finding]) -> List[Finding]:
        """Remove findings with very similar titles."""
        if not findings:
            return []

        kept = []
        seen_titles = []

        # Sort by severity (keep higher severity ones)
        severity_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
        sorted_findings = sorted(
            findings,
            key=lambda f: severity_order.get(
                f.severity.value if hasattr(f.severity, 'value') else f.severity,
                3
            )
        )

        for finding in sorted_findings:
            is_duplicate = False
            normalized_title = finding.title.lower()

            for seen in seen_titles:
                similarity = SequenceMatcher(
                    None,
                    normalized_title,
                    seen.lower()
                ).ratio()

                if similarity > self.SIMILARITY_THRESHOLD:
                    is_duplicate = True
                    logger.debug(
                        f"Similarity duplicate: '{finding.title[:40]}...' "
                        f"matches '{seen[:40]}...' ({similarity:.0%})"
                    )
                    break

            if not is_duplicate:
                kept.append(finding)
                seen_titles.append(finding.title)

        return kept


def deduplicate_findings(findings: List[Finding]) -> List[Finding]:
    """
    Convenience function for deduplication.

    Args:
        findings: List of findings to deduplicate

    Returns:
        Deduplicated list of findings
    """
    deduper = FindingDeduplicator(findings)
    return deduper.deduplicate()


def deduplicate_with_stats(findings: List[Finding]) -> tuple[List[Finding], Dict[str, int]]:
    """
    Deduplicate findings and return statistics.

    Args:
        findings: List of findings to deduplicate

    Returns:
        Tuple of (deduplicated findings, stats dict)
    """
    deduper = FindingDeduplicator(findings)
    result = deduper.deduplicate()
    return result, deduper.get_stats()
