"""
Pencil.dev Report Generator

Generates prompts for Pencil to create professional audit reports.
Pencil (pencil.dev) is a free AI-powered design tool that can generate
designs from text prompts.
"""

from typing import List, Dict, Any
from pathlib import Path
import json

from proofkit.schemas.finding import Finding, Category, Severity
from proofkit.schemas.report import Report, ReportNarrative


class PencilReportGenerator:
    """Generate Pencil-compatible prompts for audit reports."""

    # Report template structure matching professional audit report design
    REPORT_SECTIONS = [
        "cover",
        "executive_summary",
        "audit_scope",
        "ux_findings",
        "seo_findings",
        "conversion_findings",
        "maintenance_findings",
        "recommendations",
        "closing",
    ]

    def __init__(self, report: Report):
        self.report = report
        self.findings_by_category = self._group_findings()

    def _group_findings(self) -> Dict[str, List[Finding]]:
        """Group findings by category."""
        grouped: Dict[str, List[Finding]] = {}
        for finding in self.report.findings:
            cat = finding.category if isinstance(finding.category, str) else finding.category.value
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append(finding)
        return grouped

    def generate_full_report_prompt(self) -> str:
        """Generate a single prompt for complete report."""

        client_name = self._extract_client_name()

        prompt = f"""
Design a professional website audit report with the following specifications:

## Report Details
- **Client:** {client_name}
- **Report Type:** Website Performance & Inspection Report
- **Brand:** Mimik Creations
- **Style:** Clean, professional, minimal with accent colors

## Page Structure

### Page 1: Cover Page
- Large "hello." branding at top left
- Main title: "Website Performance & Inspection Report"
- Subtitle: "{client_name}"
- Footer: "Mimik Creations"
- Gradient accent in bottom right (pink/purple/blue)
- Page number: 00

### Page 2: Executive Summary
- Page number: 01
- Two-column layout
- Left column: "PURPOSE OF THIS AUDIT" heading
- Content: {self._truncate(self.report.narrative.executive_summary, 200) if self.report.narrative.executive_summary else "Comprehensive website audit..."}
- Right column: "AUDIT FRAMEWORK" with bullet list:
  • Web Design & User Experience (UX)
  • Technical SEO & Content Effectiveness
  • Lead Generation
  • General Maintenance & Site Health
- "AUDIT STATUS" section at bottom

### Page 3: Audit Scope & Methodology
- Page number: 02
- "AUDIT SCOPE" section listing the 4 audit areas
- "METHODOLOGY" section with methods used

### Pages 4-5: UX Audit Findings
- Page number: 03-04
- Table format with columns: Evaluation Areas, Details, Findings/Comments
- Include these findings:
{self._format_findings_for_prompt("UX")}

### Pages 6-7: Technical SEO Findings
- Page number: 05-06
- Performance metrics and SEO analysis
- Include these findings:
{self._format_findings_for_prompt("SEO")}
{self._format_findings_for_prompt("PERFORMANCE")}

### Pages 8-9: Lead Generation Findings
- Page number: 07-08
- CTA analysis, form analysis, trust signals
- Include these findings:
{self._format_findings_for_prompt("CONVERSION")}

### Pages 10-11: Maintenance & Security Findings
- Page number: 09-10
- Infrastructure, security headers, code health
- Include these findings:
{self._format_findings_for_prompt("SECURITY")}
{self._format_findings_for_prompt("MAINTENANCE")}

### Page 12: Recommendations Summary
- Quick wins list
- Strategic priorities
{self._format_recommendations()}

### Page 13: Closing Note
- Page number: 11
- Summary paragraph
- List of benefits from addressing issues
- Call to action for next steps

## Design Guidelines
- Font: Clean sans-serif (Inter or similar)
- Colors:
  - Primary text: #1a1a1a
  - Secondary text: #666666
  - Accent: #4098F9 (blue)
  - Background: #F2F2F2 for cards
- Spacing: Generous whitespace
- Include page numbers in top right
- Severity badges: P0=Red, P1=Orange, P2=Yellow, P3=Blue

## Scorecard (include on executive summary or separate page)
{self._format_scorecard()}
"""
        return prompt.strip()

    def generate_section_prompts(self) -> Dict[str, str]:
        """Generate individual prompts for each section."""
        prompts = {}

        # Cover page
        prompts["cover"] = f"""
Design a report cover page:
- Top left: "hello." in bold black text
- Center: "Website Performance & Inspection Report"
- Below title: "{self._extract_client_name()}"
- Bottom left: "Mimik Creations" with underline
- Bottom right: Gradient blob (pink → purple → blue)
- Page number "00" in top right
- Clean, minimal, professional style
"""

        # Executive Summary
        prompts["executive_summary"] = f"""
Design an executive summary page for a website audit:

Page number: 01

LEFT COLUMN:
Heading: "PURPOSE OF THIS AUDIT"
Content: {self.report.narrative.executive_summary if self.report.narrative.executive_summary else "Audit summary..."}

Heading: "AUDIT FRAMEWORK"
Bullet list:
• Web Design & User Experience (UX)
• Technical SEO & Content Effectiveness
• Lead Generation
• General Maintenance & Site Health

RIGHT COLUMN:
Heading: "AUDIT STATUS"
Content: "At this stage, this document defines the audit structure and evaluation criteria."

Style: Two-column layout, clean typography, page number in corner
"""

        # Findings pages
        for category in ["UX", "SEO", "CONVERSION", "SECURITY"]:
            prompts[f"{category.lower()}_findings"] = self._generate_findings_page_prompt(category)

        # Recommendations
        prompts["recommendations"] = self._generate_recommendations_prompt()

        # Closing
        prompts["closing"] = self._generate_closing_prompt()

        return prompts

    def _generate_findings_page_prompt(self, category: str) -> str:
        """Generate prompt for a findings page."""
        findings = self.findings_by_category.get(category, [])

        category_titles = {
            "UX": "Web Design & User Experience (UX) Audit",
            "SEO": "Technical SEO & Content Audit",
            "PERFORMANCE": "Performance Audit",
            "CONVERSION": "Lead Generation & Conversion Audit",
            "SECURITY": "Security & Maintenance Audit",
            "MAINTENANCE": "General Maintenance & Site Health Audit",
        }

        title = category_titles.get(category, f"{category} Audit")

        findings_text = ""
        for f in findings[:5]:  # Limit to 5 per page
            severity = f.severity if isinstance(f.severity, str) else f.severity.value
            findings_text += f"""
- **{f.title}** [{severity}]
  Summary: {f.summary}
  Impact: {f.impact}
  Recommendation: {f.recommendation}
"""

        return f"""
Design an audit findings page:

Title: "{title}"
Objective: Evaluate website {category.lower()} aspects

FINDINGS TABLE:
| Evaluation Area | Details | Findings |
{findings_text if findings_text else "  (No critical findings in this category)"}

RECOMMENDATIONS SECTION:
List actionable recommendations based on findings above.

Style: Professional table layout, severity badges (P0=red, P1=orange, P2=yellow, P3=blue)
Include relevant screenshots or evidence placeholders.
"""

    def _generate_recommendations_prompt(self) -> str:
        """Generate recommendations page prompt."""
        quick_wins = self.report.narrative.quick_wins if self.report.narrative else []
        priorities = self.report.narrative.strategic_priorities if self.report.narrative else []

        quick_wins_text = "\n".join(f"• {w}" for w in quick_wins[:5]) if quick_wins else "• No quick wins identified"
        priorities_text = "\n".join(f"• {p}" for p in priorities[:5]) if priorities else "• No strategic priorities identified"

        return f"""
Design a recommendations summary page:

QUICK WINS (can be fixed in days):
{quick_wins_text}

STRATEGIC PRIORITIES (require more investment):
{priorities_text}

Style: Two-column layout, numbered or bulleted lists, clear hierarchy
Use icons or visual indicators for effort level (S/M/L)
"""

    def _generate_closing_prompt(self) -> str:
        """Generate closing page prompt."""
        return f"""
Design a closing page for the audit report:

Title: "Closing Note"
Page number: 11

Content:
"This inspection confirms that {self._extract_client_name()}'s digital foundation shows opportunities for improvement.

Addressing the identified issues would:
• Improve perceived quality and responsiveness
• Increase engagement from international audiences
• Reduce bounce rates
• Strengthen inquiry confidence
• Align the digital experience with the brand's real-world stature

This report is intended to provide clarity and direction, enabling informed decisions on next steps."

Style: Clean, professional, with a subtle call-to-action feel
"""

    def _format_findings_for_prompt(self, category: str) -> str:
        """Format findings for inclusion in prompt."""
        findings = self.findings_by_category.get(category, [])
        if not findings:
            return "  (No critical findings in this category)"

        lines = []
        for f in findings[:3]:  # Top 3 per category
            severity = f.severity if isinstance(f.severity, str) else f.severity.value
            lines.append(f"  - [{severity}] {f.title}: {self._truncate(f.summary, 100)}")
        return "\n".join(lines)

    def _format_scorecard(self) -> str:
        """Format scorecard for prompt."""
        if not self.report.scorecard:
            return "Scores not available"

        lines = ["Scores:"]
        for cat, score in self.report.scorecard.items():
            emoji = "🟢" if score >= 75 else "🟡" if score >= 50 else "🔴"
            lines.append(f"  {emoji} {cat}: {score}/100")
        return "\n".join(lines)

    def _format_recommendations(self) -> str:
        """Format recommendations for prompt."""
        if not self.report.narrative:
            return "Recommendations not available"

        lines = ["Quick Wins:"]
        for win in (self.report.narrative.quick_wins or [])[:3]:
            lines.append(f"  • {win}")

        lines.append("\nStrategic Priorities:")
        for priority in (self.report.narrative.strategic_priorities or [])[:3]:
            lines.append(f"  • {priority}")

        return "\n".join(lines)

    def _extract_client_name(self) -> str:
        """Extract client name from URL."""
        url = self.report.meta.url
        # Remove protocol and www
        name = url.replace("https://", "").replace("http://", "").replace("www.", "")
        # Get domain
        name = name.split("/")[0]
        # Capitalize
        return name.replace("-", " ").replace(".", " ").title()

    def _truncate(self, text: str, max_length: int) -> str:
        """Truncate text to max length."""
        if not text:
            return ""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."

    def save_prompts(self, output_dir: Path) -> Dict[str, Any]:
        """Save all prompts to files."""
        output_dir.mkdir(parents=True, exist_ok=True)

        # Full report prompt
        full_prompt = self.generate_full_report_prompt()
        (output_dir / "pencil_full_report.txt").write_text(full_prompt, encoding='utf-8')

        # Section prompts
        section_prompts = self.generate_section_prompts()
        for section, prompt in section_prompts.items():
            (output_dir / f"pencil_{section}.txt").write_text(prompt, encoding='utf-8')

        # Summary JSON
        summary = {
            "client": self._extract_client_name(),
            "url": self.report.meta.url,
            "scorecard": self.report.scorecard,
            "finding_count": len(self.report.findings),
            "sections_generated": list(section_prompts.keys()),
        }
        (output_dir / "pencil_summary.json").write_text(json.dumps(summary, indent=2), encoding='utf-8')

        return {
            "full_prompt_path": str(output_dir / "pencil_full_report.txt"),
            "section_prompts": list(section_prompts.keys()),
            "summary_path": str(output_dir / "pencil_summary.json"),
        }


def generate_pencil_report(report: Report, output_dir: Path) -> Dict[str, Any]:
    """Convenience function to generate Pencil report prompts."""
    generator = PencilReportGenerator(report)
    return generator.save_prompts(output_dir)
