"""Main audit orchestration for ProofKit."""

from pathlib import Path
from datetime import datetime
from typing import Callable, Optional, List, Any
import json

from proofkit.schemas.audit import AuditConfig, AuditResult, AuditStatus
from proofkit.schemas.finding import Finding
from proofkit.schemas.report import Report, ReportMeta, ReportNarrative
from proofkit.utils.config import get_config
from proofkit.utils.logger import logger
from proofkit.utils.paths import setup_run_directories
from proofkit import __version__


class AuditRunner:
    """
    Main orchestrator that coordinates collectors, analyzer, and narrator.
    """

    def __init__(self, config: AuditConfig):
        self.config = config
        self.settings = get_config()
        self.run_id = f"run_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        self.output_dir = self._setup_output_dir()

    def _setup_output_dir(self) -> Path:
        """Set up the output directory structure."""
        base = self.config.output_dir or self.settings.output_dir
        run_dir = base / self.run_id
        setup_run_directories(run_dir)
        return run_dir

    def run(
        self, progress_callback: Optional[Callable[[int], None]] = None
    ) -> AuditResult:
        """
        Execute full audit pipeline.

        Args:
            progress_callback: Optional callback for progress updates (0-100)

        Returns:
            AuditResult with status and output paths
        """
        result = AuditResult(
            audit_id=self.run_id,
            config=self.config,
            status=AuditStatus.PENDING,
            started_at=datetime.utcnow(),
            output_dir=self.output_dir,
        )

        try:
            # Phase 1: Collect (0-40%)
            result.status = AuditStatus.COLLECTING
            logger.info(f"Starting collection for {self.config.url}")
            if progress_callback:
                progress_callback(5)

            raw_data = self._run_collectors()
            if progress_callback:
                progress_callback(40)

            # Phase 2: Analyze (40-70%)
            result.status = AuditStatus.ANALYZING
            logger.info("Running analysis")
            findings = self._run_analyzer(raw_data)
            if progress_callback:
                progress_callback(70)

            # Phase 3: Narrate (70-90%)
            result.status = AuditStatus.NARRATING
            logger.info("Generating narrative")
            narrative = self._run_narrator(findings)
            if progress_callback:
                progress_callback(90)

            # Phase 4: Build Report (90-100%)
            logger.info("Building report")
            report = self._build_report(raw_data, findings, narrative)
            self._save_outputs(report)

            result.status = AuditStatus.COMPLETE
            result.completed_at = datetime.utcnow()
            result.scorecard = report.scorecard
            result.finding_count = len(findings)
            if progress_callback:
                progress_callback(100)

            logger.info(f"Audit complete: {result.finding_count} findings")

        except Exception as e:
            result.status = AuditStatus.FAILED
            result.error = str(e)
            logger.error(f"Audit failed: {e}")
            raise

        return result

    def _run_collectors(self) -> dict:
        """
        Run all collectors and return raw data.

        Returns:
            Dict containing raw data from all collectors
        """
        # TODO: Implement when collector module is ready
        # For now, return empty structure
        logger.warning("Collector module not yet implemented, using stub data")
        return {
            "playwright": {},
            "lighthouse": {},
            "http_probe": {},
        }

    def _run_analyzer(self, raw_data: dict) -> List[Finding]:
        """
        Run analyzer on raw data.

        Args:
            raw_data: Raw data from collectors

        Returns:
            List of findings
        """
        # TODO: Implement when analyzer module is ready
        logger.warning("Analyzer module not yet implemented, returning empty findings")
        return []

    def _run_narrator(self, findings: List[Finding]) -> ReportNarrative:
        """
        Generate AI narrative from findings.

        Args:
            findings: List of findings from analyzer

        Returns:
            ReportNarrative with AI-generated content
        """
        # TODO: Implement when narrator module is ready
        logger.warning("Narrator module not yet implemented, returning empty narrative")
        return ReportNarrative()

    def _build_report(
        self,
        raw_data: dict,
        findings: List[Finding],
        narrative: ReportNarrative,
    ) -> Report:
        """
        Assemble final report from all components.

        Args:
            raw_data: Raw data from collectors
            findings: List of findings
            narrative: AI-generated narrative

        Returns:
            Complete Report object
        """
        meta = ReportMeta(
            audit_id=self.run_id,
            url=str(self.config.url),
            business_type=self.config.business_type,
            conversion_goal=self.config.conversion_goal,
            generated_at=datetime.utcnow(),
            proofkit_version=__version__,
            mode=self.config.mode.value if hasattr(self.config.mode, 'value') else str(self.config.mode),
            pages_analyzed=1,  # TODO: Get from collector
        )

        # Calculate scores
        scorecard = self._calculate_scorecard(findings)
        overall_score = self._calculate_overall_score(scorecard)

        return Report(
            meta=meta,
            overall_score=overall_score,
            scorecard=scorecard,
            findings=findings,
            narrative=narrative,
            raw_data_paths={
                "playwright": str(self.output_dir / "raw" / "playwright.json"),
                "lighthouse": str(self.output_dir / "raw" / "lighthouse.json"),
                "http_probe": str(self.output_dir / "raw" / "http_probe.json"),
            },
        )

    def _calculate_scorecard(self, findings: List[Finding]) -> dict:
        """Calculate scores by category."""
        # Start with perfect scores
        scorecard = {
            "PERFORMANCE": 100,
            "SEO": 100,
            "CONVERSION": 100,
            "UX": 100,
            "SECURITY": 100,
            "MAINTENANCE": 100,
            "BUSINESS_LOGIC": 100,
            "ACCESSIBILITY": 100,
        }

        # Deduct points based on findings
        severity_deductions = {"P0": 25, "P1": 15, "P2": 8, "P3": 3}

        for finding in findings:
            category = finding.category
            if isinstance(category, str):
                cat_key = category
            else:
                cat_key = category.value if hasattr(category, 'value') else str(category)

            severity = finding.severity
            if isinstance(severity, str):
                sev_key = severity
            else:
                sev_key = severity.value if hasattr(severity, 'value') else str(severity)

            if cat_key in scorecard:
                deduction = severity_deductions.get(sev_key, 5)
                scorecard[cat_key] = max(0, scorecard[cat_key] - deduction)

        return scorecard

    def _calculate_overall_score(self, scorecard: dict) -> int:
        """Calculate weighted overall score."""
        weights = self.settings.score_weights
        total_weight = sum(weights.get(cat, 0) for cat in scorecard)

        if total_weight == 0:
            return 100

        weighted_sum = sum(
            scorecard[cat] * weights.get(cat, 0)
            for cat in scorecard
            if cat in weights
        )

        return int(weighted_sum / total_weight)

    def _save_outputs(self, report: Report) -> None:
        """Save report and related files to output directory."""
        out_dir = self.output_dir / "out"

        # Save JSON report
        report_path = out_dir / "report.json"
        with open(report_path, "w") as f:
            f.write(report.model_dump_json(indent=2))

        logger.info(f"Report saved to {report_path}")

        # Save findings summary
        findings_path = out_dir / "findings.json"
        with open(findings_path, "w") as f:
            json.dump(
                [f.model_dump() for f in report.findings],
                f,
                indent=2,
                default=str,
            )

        # Save narrative (if present)
        if report.narrative.executive_summary:
            narrative_path = out_dir / "narrative.md"
            with open(narrative_path, "w") as f:
                f.write(f"# Audit Report: {report.meta.url}\n\n")
                f.write(f"## Executive Summary\n\n{report.narrative.executive_summary}\n\n")

                if report.narrative.quick_wins:
                    f.write("## Quick Wins\n\n")
                    for win in report.narrative.quick_wins:
                        f.write(f"- {win}\n")
                    f.write("\n")

                if report.narrative.strategic_priorities:
                    f.write("## Strategic Priorities\n\n")
                    for priority in report.narrative.strategic_priorities:
                        f.write(f"- {priority}\n")
                    f.write("\n")

                if report.narrative.lovable_concept:
                    f.write("## Lovable Redesign Concept\n\n")
                    f.write(f"```\n{report.narrative.lovable_concept}\n```\n")
