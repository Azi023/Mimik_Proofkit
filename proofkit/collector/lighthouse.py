"""Lighthouse performance audit collector."""

import subprocess
import json
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List

from proofkit.utils.logger import logger
from proofkit.utils.exceptions import LighthouseError

from .models import (
    LighthouseData,
    LighthouseScores,
    CoreWebVitals,
    LighthouseOpportunity,
)


class LighthouseCollector:
    """Lighthouse performance audit collector using CLI."""

    # Opportunity audit IDs to extract
    OPPORTUNITY_AUDITS = [
        "render-blocking-resources",
        "unused-css-rules",
        "unused-javascript",
        "modern-image-formats",
        "uses-optimized-images",
        "uses-responsive-images",
        "efficient-animated-content",
        "uses-text-compression",
        "uses-rel-preconnect",
        "server-response-time",
        "redirects",
        "uses-long-cache-ttl",
        "total-byte-weight",
        "dom-size",
        "font-display",
        "offscreen-images",
        "unminified-css",
        "unminified-javascript",
        "legacy-javascript",
    ]

    def __init__(self):
        self._lighthouse_available = None
        self._chrome_path = None

    def is_available(self) -> bool:
        """Check if Lighthouse CLI is available."""
        if self._lighthouse_available is None:
            self._lighthouse_available = shutil.which("lighthouse") is not None
        return self._lighthouse_available

    def _find_chrome(self) -> Optional[str]:
        """Find Chrome/Chromium executable."""
        if self._chrome_path:
            return self._chrome_path

        # Common Chrome/Chromium paths
        chrome_paths = [
            shutil.which("google-chrome"),
            shutil.which("google-chrome-stable"),
            shutil.which("chromium"),
            shutil.which("chromium-browser"),
            "/usr/bin/google-chrome",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
            "/snap/bin/chromium",
        ]

        # Try to find Playwright's bundled Chromium
        try:
            from playwright._impl._driver import compute_driver_executable
            pw_dir = Path(compute_driver_executable()).parent.parent
            pw_chrome = pw_dir / "chromium-" / "chrome-linux" / "chrome"
            if pw_chrome.exists():
                chrome_paths.append(str(pw_chrome))
        except Exception:
            pass

        for path in chrome_paths:
            if path and Path(path).exists():
                self._chrome_path = path
                return path

        return None

    def check_requirements(self) -> Dict[str, Any]:
        """Check if all requirements for Lighthouse are met."""
        lighthouse_installed = self.is_available()
        chrome_path = self._find_chrome()

        return {
            "lighthouse_cli": lighthouse_installed,
            "chrome_available": chrome_path is not None,
            "chrome_path": chrome_path,
            "ready": lighthouse_installed and chrome_path is not None,
            "setup_instructions": self._get_setup_instructions(lighthouse_installed, chrome_path),
        }

    def _get_setup_instructions(self, lighthouse_ok: bool, chrome_path: Optional[str]) -> str:
        """Get setup instructions for missing requirements."""
        instructions = []

        if not lighthouse_ok:
            instructions.append(
                "Install Lighthouse CLI:\n"
                "  npm install -g lighthouse"
            )

        if not chrome_path:
            instructions.append(
                "Install Chrome/Chromium:\n"
                "  # Ubuntu/Debian:\n"
                "  sudo apt-get install chromium-browser\n"
                "  # Or install Google Chrome:\n"
                "  wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb\n"
                "  sudo dpkg -i google-chrome-stable_current_amd64.deb"
            )

        return "\n\n".join(instructions) if instructions else "All requirements met!"

    def collect(self, url: str, output_dir: Path) -> LighthouseData:
        """
        Run Lighthouse audits for mobile and desktop.

        Args:
            url: Target URL to audit
            output_dir: Directory to save Lighthouse reports

        Returns:
            LighthouseData with mobile and desktop results
        """
        if not self.is_available():
            logger.warning("Lighthouse CLI not available, returning empty data")
            return LighthouseData(url=url)

        output_dir.mkdir(parents=True, exist_ok=True)

        # Run mobile audit
        logger.info(f"Running Lighthouse mobile audit for {url}")
        mobile_result = self._run_lighthouse(url, output_dir, "mobile")

        # Run desktop audit
        logger.info(f"Running Lighthouse desktop audit for {url}")
        desktop_result = self._run_lighthouse(url, output_dir, "desktop")

        return LighthouseData(
            url=url,
            mobile=mobile_result,
            desktop=desktop_result,
            mobile_scores=self._extract_scores(mobile_result),
            desktop_scores=self._extract_scores(desktop_result),
            mobile_cwv=self._extract_cwv(mobile_result),
            desktop_cwv=self._extract_cwv(desktop_result),
            opportunities=self._extract_opportunities(mobile_result),
        )

    def _run_lighthouse(
        self,
        url: str,
        output_dir: Path,
        mode: str,
    ) -> Dict[str, Any]:
        """
        Run Lighthouse CLI and return JSON result.

        Args:
            url: Target URL
            output_dir: Directory for output file
            mode: "mobile" or "desktop"

        Returns:
            Parsed JSON result or empty dict on failure
        """
        output_path = output_dir / f"lighthouse_{mode}.json"

        # Find Chrome path
        chrome_path = self._find_chrome()

        cmd = [
            "lighthouse",
            url,
            "--output=json",
            f"--output-path={output_path}",
            "--chrome-flags=--headless --no-sandbox --disable-gpu --disable-dev-shm-usage",
            "--quiet",
            "--only-categories=performance,accessibility,best-practices,seo",
        ]

        # Add Chrome path if found
        if chrome_path:
            cmd.append(f"--chrome-path={chrome_path}")

        if mode == "desktop":
            cmd.append("--preset=desktop")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180,  # 3 minute timeout
            )

            if result.returncode != 0 and result.stderr:
                logger.warning(f"Lighthouse {mode} warning: {result.stderr[:500]}")

            if output_path.exists():
                with open(output_path, "r") as f:
                    data = json.load(f)
                logger.info(f"Lighthouse {mode} audit complete")
                return data
            else:
                logger.error(f"Lighthouse output not found: {output_path}")
                return {}

        except subprocess.TimeoutExpired:
            logger.error(f"Lighthouse {mode} audit timed out")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Lighthouse output: {e}")
            return {}
        except Exception as e:
            logger.error(f"Lighthouse {mode} failed: {e}")
            return {}

    def _extract_scores(self, result: Dict[str, Any]) -> LighthouseScores:
        """Extract category scores from Lighthouse result."""
        categories = result.get("categories", {})

        def get_score(cat_id: str) -> Optional[float]:
            cat = categories.get(cat_id, {})
            score = cat.get("score")
            if score is not None:
                return round(score * 100, 1)
            return None

        return LighthouseScores(
            performance=get_score("performance"),
            accessibility=get_score("accessibility"),
            best_practices=get_score("best-practices"),
            seo=get_score("seo"),
        )

    def _extract_cwv(self, result: Dict[str, Any]) -> CoreWebVitals:
        """Extract Core Web Vitals from Lighthouse result."""
        audits = result.get("audits", {})

        def get_metric(key: str) -> Optional[float]:
            audit = audits.get(key, {})
            value = audit.get("numericValue")
            if value is not None:
                return round(value, 2)
            return None

        return CoreWebVitals(
            lcp=get_metric("largest-contentful-paint"),
            fid=get_metric("max-potential-fid"),
            cls=get_metric("cumulative-layout-shift"),
            inp=get_metric("experimental-interaction-to-next-paint"),
            ttfb=get_metric("server-response-time"),
            tbt=get_metric("total-blocking-time"),
            fcp=get_metric("first-contentful-paint"),
            si=get_metric("speed-index"),
        )

    def _extract_opportunities(self, result: Dict[str, Any]) -> List[LighthouseOpportunity]:
        """Extract optimization opportunities from Lighthouse result."""
        opportunities = []
        audits = result.get("audits", {})

        for audit_id in self.OPPORTUNITY_AUDITS:
            audit = audits.get(audit_id, {})
            score = audit.get("score")

            # Only include if there's room for improvement
            if score is not None and score < 1:
                details = audit.get("details", {})

                # Get savings
                savings_ms = details.get("overallSavingsMs")
                savings_bytes = details.get("overallSavingsBytes")

                opportunities.append(LighthouseOpportunity(
                    id=audit_id,
                    title=audit.get("title", audit_id),
                    description=audit.get("description", ""),
                    score=round(score * 100, 1) if score else None,
                    savings_ms=round(savings_ms, 0) if savings_ms else None,
                    savings_bytes=int(savings_bytes) if savings_bytes else None,
                    display_value=audit.get("displayValue", ""),
                ))

        # Sort by potential savings (ms first, then bytes)
        opportunities.sort(
            key=lambda x: (x.savings_ms or 0, x.savings_bytes or 0),
            reverse=True
        )

        return opportunities[:15]  # Top 15 opportunities

    def collect_simple(self, url: str) -> Dict[str, Any]:
        """
        Run a simplified Lighthouse audit without saving files.

        Useful for quick checks or when disk space is limited.

        Args:
            url: Target URL

        Returns:
            Dict with key metrics
        """
        if not self.is_available():
            return {"error": "Lighthouse CLI not available"}

        cmd = [
            "lighthouse",
            url,
            "--output=json",
            "--output-path=stdout",
            "--chrome-flags=--headless --no-sandbox --disable-gpu",
            "--quiet",
            "--only-categories=performance",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.stdout:
                data = json.loads(result.stdout)
                return {
                    "performance_score": self._extract_scores(data).performance,
                    "cwv": self._extract_cwv(data).model_dump(),
                }

        except Exception as e:
            logger.error(f"Simple Lighthouse audit failed: {e}")

        return {"error": "Audit failed"}
