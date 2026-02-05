"""
Visual QA Rules - AI-powered screenshot analysis for design issues.

Uses vision capabilities to detect:
- Misaligned elements
- Inconsistent spacing
- Overlapping content
- Typography issues
- Color contrast problems
"""

import base64
import os
import json
from pathlib import Path
from typing import List, Optional

from proofkit.schemas.finding import Finding, Evidence, Severity, Category, Effort
from proofkit.utils.logger import logger
from .base import BaseRule


class VisualQARules(BaseRule):
    """
    AI-powered visual analysis of website screenshots.

    This rule uses vision-capable AI models (GPT-4o or Claude) to analyze
    screenshots for visual issues that are difficult to detect programmatically.
    """

    category = Category.UX

    def __init__(self, raw_data, business_type=None):
        super().__init__(raw_data, business_type)
        self._vision_available = self._check_vision_availability()
        self._analyzed_count = 0
        self._max_screenshots = 3  # Limit to control API costs

    def _check_vision_availability(self) -> bool:
        """Check if vision API is available."""
        provider = os.getenv("AI_PROVIDER", "anthropic").lower()

        if provider == "openai":
            # GPT-4o and gpt-4-turbo support vision, gpt-4o-mini does NOT
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            api_key = os.getenv("OPENAI_API_KEY")
            # gpt-4o-mini doesn't support vision well, need full gpt-4o
            has_vision_model = "gpt-4o" in model and "mini" not in model
            return bool(api_key) and has_vision_model
        elif provider == "anthropic":
            # Claude 3+ supports vision
            api_key = os.getenv("ANTHROPIC_API_KEY")
            return bool(api_key)

        return False

    def run(self) -> List[Finding]:
        """Run visual QA analysis."""
        if not self._vision_available:
            logger.info("Vision API not available, skipping visual QA analysis")
            return self.findings

        # Analyze screenshots from pages
        for page in self.raw_data.snapshot.pages:
            if self._analyzed_count >= self._max_screenshots:
                logger.debug(f"Reached max screenshot limit ({self._max_screenshots})")
                break

            for screenshot_path in page.screenshots:
                if self._analyzed_count >= self._max_screenshots:
                    break

                if Path(screenshot_path).exists():
                    self._analyze_screenshot(screenshot_path, page.url)
                    self._analyzed_count += 1

        return self.findings

    def _analyze_screenshot(self, screenshot_path: str, page_url: str):
        """Analyze a single screenshot for visual issues."""
        try:
            # Read and encode image
            image_data = self._encode_image(screenshot_path)

            # Determine if mobile or desktop
            is_mobile = "mobile" in screenshot_path.lower()

            # Create analysis prompt and call API
            analysis = self._call_vision_api(image_data, is_mobile)

            # Parse findings from analysis
            self._parse_visual_findings(analysis, screenshot_path, page_url)

        except Exception as e:
            logger.warning(f"Visual analysis failed for {screenshot_path}: {e}")

    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64."""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _call_vision_api(self, image_data: str, is_mobile: bool) -> str:
        """Call vision API for analysis."""
        device_context = "mobile device (390x844 viewport)" if is_mobile else "desktop (1440x900 viewport)"

        prompt = f"""
Analyze this website screenshot taken on a {device_context} for visual QA issues.

Check for these specific issues:

1. LAYOUT ISSUES:
   - Elements that appear misaligned
   - Inconsistent margins or padding
   - Content that seems cut off or overflowing
   - Broken grid structure

2. TYPOGRAPHY ISSUES:
   - Text that's too small to read comfortably (< 14px on mobile)
   - Poor contrast between text and background
   - Inconsistent font sizes for similar elements
   - Text that overflows its container

3. VISUAL HIERARCHY:
   - CTAs that don't stand out
   - Confusing visual flow
   - Important elements buried below the fold

4. MOBILE-SPECIFIC (if mobile):
   - Touch targets that appear too small (< 44px)
   - Horizontal scrolling issues
   - Content that doesn't fit the viewport

5. DESIGN CONSISTENCY:
   - Buttons with different styles
   - Inconsistent color usage
   - Mismatched icon styles

For each issue found, provide:
- Issue type (layout/typography/hierarchy/mobile/consistency)
- Severity (critical/major/minor)
- Location description
- Specific recommendation

Format as JSON array:
[
  {{
    "type": "layout",
    "severity": "major",
    "title": "Navigation menu misaligned",
    "description": "The navigation items appear unevenly spaced",
    "location": "Header area, top of page",
    "recommendation": "Use flexbox with consistent gap spacing"
  }}
]

If the page looks well-designed with no significant issues, return an empty array: []
"""

        provider = os.getenv("AI_PROVIDER", "anthropic").lower()

        if provider == "openai":
            return self._call_openai_vision(image_data, prompt)
        else:
            return self._call_anthropic_vision(image_data, prompt)

    def _call_openai_vision(self, image_data: str, prompt: str) -> str:
        """Call OpenAI GPT-4 Vision."""
        try:
            from openai import OpenAI
        except ImportError:
            logger.warning("OpenAI package not installed")
            return "[]"

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        response = client.chat.completions.create(
            model="gpt-4o",  # Need full GPT-4o for vision
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000,
        )

        return response.choices[0].message.content or "[]"

    def _call_anthropic_vision(self, image_data: str, prompt: str) -> str:
        """Call Anthropic Claude Vision."""
        try:
            import anthropic
        except ImportError:
            logger.warning("Anthropic package not installed")
            return "[]"

        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        response = client.messages.create(
            model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_data,
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )

        return response.content[0].text

    def _parse_visual_findings(self, analysis: str, screenshot_path: str, page_url: str):
        """Parse vision API response into findings."""
        try:
            # Extract JSON from response
            start = analysis.find("[")
            end = analysis.rfind("]") + 1

            if start == -1 or end == 0:
                logger.debug("No visual issues found in analysis")
                return

            issues = json.loads(analysis[start:end])

            severity_map = {
                "critical": Severity.P0,
                "major": Severity.P1,
                "minor": Severity.P2,
            }

            type_to_prefix = {
                "layout": "LAY",
                "typography": "TYP",
                "hierarchy": "HIE",
                "mobile": "MOB",
                "consistency": "CON",
            }

            for i, issue in enumerate(issues[:5]):  # Limit to 5 issues per screenshot
                issue_type = issue.get("type", "general")
                severity = severity_map.get(issue.get("severity", "minor"), Severity.P2)
                prefix = type_to_prefix.get(issue_type, "VIS")

                self.add_finding(
                    id=f"VIS-{prefix}-{i:03d}",
                    severity=severity,
                    title=issue.get("title", "Visual issue detected"),
                    summary=issue.get("description", ""),
                    impact=f"Visual quality issue affecting user experience. Location: {issue.get('location', 'Page')}",
                    recommendation=issue.get("recommendation", "Review and fix the visual issue"),
                    effort=Effort.S if severity == Severity.P2 else Effort.M,
                    evidence=[Evidence(
                        url=page_url,
                        screenshot_path=screenshot_path,
                        note=f"Visual QA: {issue_type} issue",
                    )],
                    tags=["visual-qa", issue_type],
                    confidence=0.8,  # Vision analysis has some uncertainty
                )

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse visual analysis response: {e}")
        except Exception as e:
            logger.warning(f"Error parsing visual findings: {e}")
