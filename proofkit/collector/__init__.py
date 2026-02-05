"""Collector module for ProofKit - data collection from websites."""

import json
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from proofkit.schemas.audit import AuditMode
from proofkit.utils.config import get_config
from proofkit.utils.logger import logger
from proofkit.utils.exceptions import CollectorError

from .models import RawData, SnapshotData, LighthouseData, HttpProbeData, StackInfo, BusinessSignals
from .playwright_snapshot import PlaywrightCollector
from .lighthouse import LighthouseCollector
from .http_probe import HttpProbeCollector
from .stack_detector import StackDetector
from .business_detector import BusinessDetector


class Collector:
    """
    Main collector that orchestrates all data collection.

    Coordinates Playwright (DOM extraction), Lighthouse (performance),
    HTTP probe (headers/SSL), stack detection, and business type detection.
    """

    def __init__(self):
        self.config = get_config()
        self.playwright = PlaywrightCollector()
        self.lighthouse = LighthouseCollector()
        self.http_probe = HttpProbeCollector()
        self.stack_detector = StackDetector()
        self.business_detector = BusinessDetector()

    def collect(
        self,
        url: str,
        mode: AuditMode,
        output_dir: Path,
    ) -> RawData:
        """
        Collect all raw data for a URL.

        Args:
            url: Target URL to audit
            mode: fast (homepage + key pages) or full (crawl)
            output_dir: Where to save raw data and screenshots

        Returns:
            RawData containing all collected information
        """
        logger.info(f"Starting collection for {url} in {mode.value if hasattr(mode, 'value') else mode} mode")

        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        errors = []
        mode_str = mode.value if hasattr(mode, 'value') else str(mode)

        # Determine pages to audit
        try:
            pages = self._get_pages_to_audit(url, mode)
            logger.info(f"Pages to audit: {len(pages)}")
        except Exception as e:
            logger.error(f"Failed to discover pages: {e}")
            pages = [url]
            errors.append(f"Page discovery failed: {e}")

        # Run Playwright collector
        try:
            snapshot = self.playwright.collect(url, pages, output_dir)
            logger.info(f"Playwright collected {len(snapshot.pages)} pages")
        except Exception as e:
            logger.error(f"Playwright collection failed: {e}")
            snapshot = SnapshotData(url=url)
            errors.append(f"Playwright failed: {e}")

        # Run Lighthouse collector
        try:
            lighthouse = self.lighthouse.collect(url, output_dir)
            logger.info("Lighthouse audit complete")
        except Exception as e:
            logger.error(f"Lighthouse collection failed: {e}")
            lighthouse = LighthouseData(url=url)
            errors.append(f"Lighthouse failed: {e}")

        # Run HTTP probe
        try:
            http_probe = self.http_probe.collect(url)
            logger.info("HTTP probe complete")
        except Exception as e:
            logger.error(f"HTTP probe failed: {e}")
            http_probe = HttpProbeData(url=url, final_url=url)
            errors.append(f"HTTP probe failed: {e}")

        # Run stack detection
        try:
            detected_stack = self.stack_detector.detect(snapshot)
            if detected_stack.cms:
                logger.info(f"Detected CMS: {detected_stack.cms}")
            if detected_stack.framework:
                logger.info(f"Detected framework: {detected_stack.framework}")
        except Exception as e:
            logger.warning(f"Stack detection failed: {e}")
            detected_stack = StackInfo()

        # Run business type detection
        try:
            business_signals = self.business_detector.detect(snapshot)
            if business_signals.detected_type:
                logger.info(f"Detected business type: {business_signals.detected_type} (confidence: {business_signals.confidence})")
        except Exception as e:
            logger.warning(f"Business detection failed: {e}")
            business_signals = BusinessSignals()

        # Assemble raw data
        raw_data = RawData(
            url=url,
            mode=mode_str,
            pages_audited=pages,
            snapshot=snapshot,
            lighthouse=lighthouse,
            http_probe=http_probe,
            detected_stack=detected_stack,
            business_signals=business_signals,
            collected_at=datetime.utcnow().isoformat(),
            collection_errors=errors,
        )

        # Save raw data
        self._save_raw_data(raw_data, output_dir)

        return raw_data

    def collect_single(
        self,
        url: str,
        output_dir: Path,
        collectors: Optional[List[str]] = None,
    ) -> RawData:
        """
        Collect from a single page with specified collectors.

        Args:
            url: Target URL
            output_dir: Output directory
            collectors: List of collectors to run ("playwright", "lighthouse", "http")

        Returns:
            RawData with collected information
        """
        collectors = collectors or ["playwright", "lighthouse", "http"]
        output_dir.mkdir(parents=True, exist_ok=True)

        errors = []
        snapshot = SnapshotData(url=url)
        lighthouse = LighthouseData(url=url)
        http_probe = HttpProbeData(url=url, final_url=url)

        if "playwright" in collectors:
            try:
                snapshot = self.playwright.collect(url, [url], output_dir)
            except Exception as e:
                errors.append(f"Playwright: {e}")

        if "lighthouse" in collectors:
            try:
                lighthouse = self.lighthouse.collect(url, output_dir)
            except Exception as e:
                errors.append(f"Lighthouse: {e}")

        if "http" in collectors:
            try:
                http_probe = self.http_probe.collect(url)
            except Exception as e:
                errors.append(f"HTTP probe: {e}")

        return RawData(
            url=url,
            mode="single",
            pages_audited=[url],
            snapshot=snapshot,
            lighthouse=lighthouse,
            http_probe=http_probe,
            detected_stack=self.stack_detector.detect(snapshot),
            business_signals=self.business_detector.detect(snapshot),
            collected_at=datetime.utcnow().isoformat(),
            collection_errors=errors,
        )

    def _get_pages_to_audit(self, url: str, mode: AuditMode) -> List[str]:
        """Determine which pages to audit based on mode."""
        mode_str = mode.value if hasattr(mode, 'value') else str(mode)

        if mode_str == "fast":
            max_pages = self.config.max_pages_fast
            return self.playwright.discover_key_pages(url, max_pages=max_pages)
        else:
            max_pages = self.config.max_pages_full
            return self.playwright.crawl_site(url, max_pages=max_pages)

    def _save_raw_data(self, data: RawData, output_dir: Path) -> None:
        """Save collected data to JSON files."""
        # Save complete raw data
        raw_path = output_dir / "raw_data.json"
        with open(raw_path, "w") as f:
            f.write(data.model_dump_json(indent=2))

        # Save individual collector outputs for easier inspection
        (output_dir / "snapshot.json").write_text(
            data.snapshot.model_dump_json(indent=2)
        )

        if data.lighthouse.mobile or data.lighthouse.desktop:
            (output_dir / "lighthouse_summary.json").write_text(
                json.dumps({
                    "mobile_scores": data.lighthouse.mobile_scores.model_dump(),
                    "desktop_scores": data.lighthouse.desktop_scores.model_dump(),
                    "mobile_cwv": data.lighthouse.mobile_cwv.model_dump(),
                    "desktop_cwv": data.lighthouse.desktop_cwv.model_dump(),
                    "opportunities": [o.model_dump() for o in data.lighthouse.opportunities],
                }, indent=2)
            )

        (output_dir / "http_probe.json").write_text(
            data.http_probe.model_dump_json(indent=2)
        )

        (output_dir / "stack.json").write_text(
            data.detected_stack.model_dump_json(indent=2)
        )

        (output_dir / "business_signals.json").write_text(
            data.business_signals.model_dump_json(indent=2)
        )

        logger.info(f"Raw data saved to {output_dir}")


# Export main classes and models
__all__ = [
    "Collector",
    "PlaywrightCollector",
    "LighthouseCollector",
    "HttpProbeCollector",
    "StackDetector",
    "BusinessDetector",
    "RawData",
    "SnapshotData",
    "LighthouseData",
    "HttpProbeData",
    "StackInfo",
    "BusinessSignals",
]
