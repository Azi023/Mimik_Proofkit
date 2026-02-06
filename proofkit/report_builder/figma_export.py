"""
Figma Report Generator

Generates structured data that can be used to create Figma designs via:
1. Figma Plugin import (using JSON structure)
2. Figma REST API (requires personal access token)
3. Manual template with variables

This module creates a structured JSON that maps directly to a Figma report template.
"""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from proofkit.schemas.finding import Finding, Severity
from proofkit.schemas.report import Report


class FigmaReportExporter:
    """Export audit reports in Figma-compatible format."""

    # Color scheme for severity levels
    SEVERITY_COLORS = {
        "P0": {"fill": "#EF4444", "text": "#FFFFFF"},  # Red - Critical
        "P1": {"fill": "#F97316", "text": "#FFFFFF"},  # Orange - High
        "P2": {"fill": "#EAB308", "text": "#000000"},  # Yellow - Medium
        "P3": {"fill": "#3B82F6", "text": "#FFFFFF"},  # Blue - Low
    }

    # Score colors
    SCORE_COLORS = {
        "excellent": "#22C55E",  # Green 75-100
        "good": "#84CC16",       # Lime 50-74
        "fair": "#EAB308",       # Yellow 25-49
        "poor": "#EF4444",       # Red 0-24
    }

    def __init__(self, report: Report):
        self.report = report

    def export_figma_variables(self) -> Dict[str, Any]:
        """
        Export report data as Figma Variables format.

        These can be imported directly into Figma using the
        Variables API or community plugins like 'Figma Tokens'.
        """
        client_name = self._extract_client_name()

        return {
            "version": "1.0",
            "collections": [
                {
                    "name": "Audit Report",
                    "modes": ["Default"],
                    "variables": {
                        # Header info
                        "report/client_name": client_name,
                        "report/url": self.report.meta.url,
                        "report/date": datetime.now().strftime("%B %d, %Y"),
                        "report/overall_score": str(self.report.overall_score),

                        # Scores by category
                        **{f"scores/{cat.lower()}": str(score)
                           for cat, score in self.report.scorecard.items()},

                        # Finding counts
                        "findings/total": str(len(self.report.findings)),
                        "findings/critical": str(self._count_by_severity("P0")),
                        "findings/high": str(self._count_by_severity("P1")),
                        "findings/medium": str(self._count_by_severity("P2")),
                        "findings/low": str(self._count_by_severity("P3")),

                        # Narrative sections
                        "narrative/executive_summary": self.report.narrative.executive_summary or "",
                        "narrative/quick_wins": "\n".join(self.report.narrative.quick_wins or []),
                        "narrative/priorities": "\n".join(self.report.narrative.strategic_priorities or []),
                    }
                }
            ]
        }

    def export_figma_json(self) -> Dict[str, Any]:
        """
        Export report as structured JSON for Figma design automation.

        This format is designed to work with:
        1. Figma Tokens plugin
        2. Figma REST API content replacement
        3. Manual copy-paste into template
        """
        client_name = self._extract_client_name()

        return {
            "meta": {
                "type": "proofkit_figma_export",
                "version": "1.0",
                "generated_at": datetime.now().isoformat(),
                "template_recommended": "ProofKit Audit Report Template v1",
            },
            "header": {
                "brand": "Mimik Creations",
                "title": "Website Performance & Inspection Report",
                "client": client_name,
                "url": self.report.meta.url,
                "date": datetime.now().strftime("%B %d, %Y"),
            },
            "scorecard": {
                "overall": {
                    "value": self.report.overall_score,
                    "color": self._get_score_color(self.report.overall_score),
                    "label": self._get_score_label(self.report.overall_score),
                },
                "categories": [
                    {
                        "name": cat,
                        "score": score,
                        "color": self._get_score_color(score),
                        "icon": self._get_category_icon(cat),
                    }
                    for cat, score in self.report.scorecard.items()
                ]
            },
            "executive_summary": {
                "text": self.report.narrative.executive_summary or
                        f"This audit analyzed {client_name}'s website across performance, UX, SEO, and conversion metrics.",
                "highlight_stats": [
                    {"label": "Total Findings", "value": str(len(self.report.findings))},
                    {"label": "Critical Issues", "value": str(self._count_by_severity("P0"))},
                    {"label": "Overall Score", "value": f"{self.report.overall_score}/100"},
                ]
            },
            "findings_summary": {
                "by_severity": [
                    {"severity": "P0", "count": self._count_by_severity("P0"), "label": "Critical", "color": "#EF4444"},
                    {"severity": "P1", "count": self._count_by_severity("P1"), "label": "High", "color": "#F97316"},
                    {"severity": "P2", "count": self._count_by_severity("P2"), "label": "Medium", "color": "#EAB308"},
                    {"severity": "P3", "count": self._count_by_severity("P3"), "label": "Low", "color": "#3B82F6"},
                ],
                "by_category": [
                    {"category": cat, "count": self._count_by_category(cat)}
                    for cat in set(self._get_finding_category(f) for f in self.report.findings)
                ]
            },
            "top_findings": [
                self._format_finding_for_figma(f)
                for f in sorted(self.report.findings,
                               key=lambda x: self._severity_order(x))[:10]
            ],
            "quick_wins": [
                {"text": win, "index": i + 1}
                for i, win in enumerate(self.report.narrative.quick_wins or [])
            ][:5],
            "strategic_priorities": [
                {"text": priority, "index": i + 1}
                for i, priority in enumerate(self.report.narrative.strategic_priorities or [])
            ][:5],
            "closing": {
                "summary": f"This inspection identifies {len(self.report.findings)} opportunities to improve {client_name}'s digital presence.",
                "benefits": [
                    "Improve perceived quality and responsiveness",
                    "Increase engagement from target audiences",
                    "Reduce bounce rates and increase conversions",
                    "Strengthen inquiry confidence",
                    "Align digital experience with brand stature",
                ],
                "cta": "Ready to transform your website? Let's discuss next steps.",
            }
        }

    def export_figma_api_payload(self, file_key: str, node_ids: Dict[str, str]) -> Dict[str, Any]:
        """
        Generate payload for Figma REST API to update text in existing design.

        Args:
            file_key: Figma file key (from URL)
            node_ids: Mapping of field names to Figma node IDs

        Returns:
            Payload for Figma API POST request

        Note: Requires Figma Personal Access Token for authentication.
        API endpoint: https://api.figma.com/v1/files/{file_key}/variables
        """
        data = self.export_figma_json()

        # Flatten the nested structure for text replacement
        text_updates = {
            "client_name": data["header"]["client"],
            "report_date": data["header"]["date"],
            "overall_score": str(data["scorecard"]["overall"]["value"]),
            "executive_summary": data["executive_summary"]["text"],
            "total_findings": str(len(self.report.findings)),
            "critical_count": str(self._count_by_severity("P0")),
        }

        # Add scores
        for cat in data["scorecard"]["categories"]:
            text_updates[f"score_{cat['name'].lower()}"] = str(cat["score"])

        return {
            "file_key": file_key,
            "node_updates": [
                {"node_id": node_ids.get(field, ""), "text": value}
                for field, value in text_updates.items()
                if field in node_ids
            ]
        }

    def _format_finding_for_figma(self, finding: Finding) -> Dict[str, Any]:
        """Format a single finding for Figma display."""
        severity = self._get_finding_severity(finding)
        category = self._get_finding_category(finding)

        return {
            "id": finding.id,
            "severity": severity,
            "severity_color": self.SEVERITY_COLORS.get(severity, {}).get("fill", "#666666"),
            "severity_text_color": self.SEVERITY_COLORS.get(severity, {}).get("text", "#FFFFFF"),
            "category": category,
            "title": finding.title,
            "summary": finding.summary[:200] + "..." if len(finding.summary) > 200 else finding.summary,
            "impact": finding.impact[:150] + "..." if len(finding.impact) > 150 else finding.impact,
            "recommendation": finding.recommendation,
        }

    def _extract_client_name(self) -> str:
        """Extract client name from URL."""
        url = self.report.meta.url
        name = url.replace("https://", "").replace("http://", "").replace("www.", "")
        name = name.split("/")[0]
        return name.replace("-", " ").replace(".", " ").title()

    def _count_by_severity(self, severity: str) -> int:
        """Count findings by severity."""
        return sum(1 for f in self.report.findings
                  if self._get_finding_severity(f) == severity)

    def _count_by_category(self, category: str) -> int:
        """Count findings by category."""
        return sum(1 for f in self.report.findings
                  if self._get_finding_category(f) == category)

    def _get_finding_severity(self, finding: Finding) -> str:
        """Get severity as string."""
        if hasattr(finding.severity, 'value'):
            return finding.severity.value
        return str(finding.severity)

    def _get_finding_category(self, finding: Finding) -> str:
        """Get category as string."""
        if hasattr(finding.category, 'value'):
            return finding.category.value
        return str(finding.category)

    def _severity_order(self, finding: Finding) -> int:
        """Get numeric order for severity sorting."""
        order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
        return order.get(self._get_finding_severity(finding), 99)

    def _get_score_color(self, score: int) -> str:
        """Get color for score value."""
        if score >= 75:
            return self.SCORE_COLORS["excellent"]
        elif score >= 50:
            return self.SCORE_COLORS["good"]
        elif score >= 25:
            return self.SCORE_COLORS["fair"]
        return self.SCORE_COLORS["poor"]

    def _get_score_label(self, score: int) -> str:
        """Get label for score value."""
        if score >= 75:
            return "Excellent"
        elif score >= 50:
            return "Good"
        elif score >= 25:
            return "Needs Improvement"
        return "Critical"

    def _get_category_icon(self, category: str) -> str:
        """Get icon name for category."""
        icons = {
            "PERFORMANCE": "zap",
            "SEO": "search",
            "CONVERSION": "trending-up",
            "UX": "layout",
            "SECURITY": "shield",
            "MAINTENANCE": "tool",
            "BUSINESS_LOGIC": "briefcase",
            "ACCESSIBILITY": "eye",
        }
        return icons.get(category, "circle")

    def save(self, output_dir: Path) -> Dict[str, str]:
        """
        Save all Figma export formats.

        Args:
            output_dir: Directory to save files

        Returns:
            Dict with paths to saved files
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        files = {}

        # Save Figma Variables format
        variables_path = output_dir / "figma_variables.json"
        variables_path.write_text(
            json.dumps(self.export_figma_variables(), indent=2),
            encoding='utf-8'
        )
        files["variables"] = str(variables_path)

        # Save full JSON format
        json_path = output_dir / "figma_report_data.json"
        json_path.write_text(
            json.dumps(self.export_figma_json(), indent=2),
            encoding='utf-8'
        )
        files["json"] = str(json_path)

        # Save text-only version for easy copy-paste
        text_path = output_dir / "figma_text_content.txt"
        text_path.write_text(self._generate_text_content(), encoding='utf-8')
        files["text"] = str(text_path)

        # Save instructions
        instructions_path = output_dir / "FIGMA_INSTRUCTIONS.md"
        instructions_path.write_text(self._generate_instructions(), encoding='utf-8')
        files["instructions"] = str(instructions_path)

        return files

    def _generate_text_content(self) -> str:
        """Generate plain text version of all content for copy-paste."""
        data = self.export_figma_json()
        client_name = self._extract_client_name()

        content = f"""
PROOFKIT AUDIT REPORT - TEXT CONTENT FOR FIGMA
================================================

[HEADER]
Client: {client_name}
URL: {self.report.meta.url}
Date: {data['header']['date']}
Brand: Mimik Creations

[OVERALL SCORE]
Score: {self.report.overall_score}/100
Rating: {data['scorecard']['overall']['label']}

[CATEGORY SCORES]
"""
        for cat in data['scorecard']['categories']:
            content += f"{cat['name']}: {cat['score']}/100\n"

        content += f"""
[EXECUTIVE SUMMARY]
{data['executive_summary']['text']}

[FINDINGS SUMMARY]
Total: {len(self.report.findings)}
Critical (P0): {self._count_by_severity('P0')}
High (P1): {self._count_by_severity('P1')}
Medium (P2): {self._count_by_severity('P2')}
Low (P3): {self._count_by_severity('P3')}

[TOP FINDINGS]
"""
        for i, f in enumerate(data['top_findings'][:5], 1):
            content += f"\n{i}. [{f['severity']}] {f['title']}\n   {f['summary']}\n"

        content += "\n[QUICK WINS]\n"
        for win in data['quick_wins']:
            content += f"{win['index']}. {win['text']}\n"

        content += "\n[STRATEGIC PRIORITIES]\n"
        for priority in data['strategic_priorities']:
            content += f"{priority['index']}. {priority['text']}\n"

        content += f"""
[CLOSING NOTE]
{data['closing']['summary']}

Benefits of addressing these issues:
"""
        for benefit in data['closing']['benefits']:
            content += f"- {benefit}\n"

        content += f"\n{data['closing']['cta']}\n"

        return content

    def _generate_instructions(self) -> str:
        """Generate instructions for using Figma export."""
        return """
# Using ProofKit Reports with Figma

## Option 1: Manual Template (Easiest)

1. Open the Figma template: `ProofKit Audit Report Template`
2. Duplicate the template for your new report
3. Open `figma_text_content.txt`
4. Copy-paste each section into the corresponding Figma text layers
5. Update colors based on scores (see figma_report_data.json for colors)

## Option 2: Figma Tokens Plugin

1. Install the "Figma Tokens" plugin from Figma Community
2. Open your report template in Figma
3. In the plugin, go to Import > JSON
4. Upload `figma_variables.json`
5. The variables will be imported and can be applied to text layers

## Option 3: Figma REST API (Advanced)

1. Get a Personal Access Token from Figma (Account Settings > Personal Access Tokens)
2. Create a template file with named text nodes
3. Use the API to update text content:

```python
import requests

FIGMA_TOKEN = "your-personal-access-token"
FILE_KEY = "your-file-key-from-url"

headers = {"X-FIGMA-TOKEN": FIGMA_TOKEN}

# Get file structure
response = requests.get(
    f"https://api.figma.com/v1/files/{FILE_KEY}",
    headers=headers
)

# Note: Figma API doesn't directly support text replacement.
# You would need to use Figma's Plugin API for automated text updates.
```

## Option 4: Use with Pencil.dev

For easier design generation, use the Pencil prompts instead:
1. Open `../pencil/pencil_full_report.txt`
2. Paste into Pencil.dev
3. Generate the design
4. Export to Figma if needed

## Color Reference

Severity Colors:
- P0 (Critical): #EF4444 (Red)
- P1 (High): #F97316 (Orange)
- P2 (Medium): #EAB308 (Yellow)
- P3 (Low): #3B82F6 (Blue)

Score Colors:
- 75-100: #22C55E (Green - Excellent)
- 50-74: #84CC16 (Lime - Good)
- 25-49: #EAB308 (Yellow - Needs Improvement)
- 0-24: #EF4444 (Red - Critical)

## Files in This Directory

- `figma_variables.json` - Figma Variables format for plugins
- `figma_report_data.json` - Full structured data with colors
- `figma_text_content.txt` - Plain text for copy-paste
- `FIGMA_INSTRUCTIONS.md` - This file
"""


def generate_figma_export(report: Report, output_dir: Path) -> Dict[str, str]:
    """Convenience function to generate Figma export."""
    exporter = FigmaReportExporter(report)
    return exporter.save(output_dir)
