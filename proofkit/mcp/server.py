"""
MCP Server for ProofKit

Provides tools for Claude Code to interact with ProofKit:
- Run audits
- Discover features
- Generate reports
- Analyze websites
"""

import json
import asyncio
from typing import Any, Dict, List
from pathlib import Path

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    Server = None

from proofkit.utils.logger import logger


def create_mcp_server():
    """Create and configure the MCP server."""
    if not MCP_AVAILABLE:
        raise ImportError(
            "MCP package not installed. Install with: pip install mcp"
        )

    server = Server("proofkit")

    @server.list_tools()
    async def list_tools() -> List[Tool]:
        """List available ProofKit tools."""
        return [
            Tool(
                name="proofkit_audit",
                description="Run a website audit and get findings",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL to audit"
                        },
                        "mode": {
                            "type": "string",
                            "enum": ["fast", "full"],
                            "description": "Audit mode (fast=homepage, full=crawl)",
                            "default": "fast"
                        },
                        "business_type": {
                            "type": "string",
                            "description": "Business type for context (optional)"
                        }
                    },
                    "required": ["url"]
                }
            ),
            Tool(
                name="proofkit_discover_features",
                description="Discover interactive features on a webpage",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL to analyze"
                        }
                    },
                    "required": ["url"]
                }
            ),
            Tool(
                name="proofkit_analyze",
                description="Analyze collected data and return findings",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "run_dir": {
                            "type": "string",
                            "description": "Path to run directory with raw data"
                        }
                    },
                    "required": ["run_dir"]
                }
            ),
            Tool(
                name="proofkit_generate_report",
                description="Generate a formatted report from audit results",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "run_dir": {
                            "type": "string",
                            "description": "Path to run directory"
                        },
                        "format": {
                            "type": "string",
                            "enum": ["json", "markdown", "pencil"],
                            "description": "Report format",
                            "default": "markdown"
                        }
                    },
                    "required": ["run_dir"]
                }
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute a ProofKit tool."""
        try:
            if name == "proofkit_audit":
                result = await run_audit(arguments)
            elif name == "proofkit_discover_features":
                result = await discover_features(arguments)
            elif name == "proofkit_analyze":
                result = await analyze_data(arguments)
            elif name == "proofkit_generate_report":
                result = await generate_report(arguments)
            else:
                result = {"error": f"Unknown tool: {name}"}

            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, default=str)
            )]
        except Exception as e:
            logger.error(f"Tool {name} failed: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({"error": str(e)})
            )]

    return server


async def run_audit(args: Dict[str, Any]) -> Dict[str, Any]:
    """Run a website audit."""
    from proofkit.core.runner import AuditRunner
    from proofkit.schemas.audit import AuditConfig, AuditMode
    from proofkit.schemas.business import BusinessType

    url = args["url"]
    mode = AuditMode(args.get("mode", "fast"))
    business_type = None

    if args.get("business_type"):
        try:
            business_type = BusinessType(args["business_type"])
        except ValueError:
            pass

    config = AuditConfig(
        url=url,
        mode=mode,
        business_type=business_type,
    )

    # Run in executor to avoid blocking
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: AuditRunner(config).run()
    )

    return {
        "audit_id": result.audit_id,
        "status": result.status.value if hasattr(result.status, "value") else str(result.status),
        "finding_count": result.finding_count,
        "scorecard": result.scorecard,
        "output_dir": str(result.output_dir),
    }


async def discover_features(args: Dict[str, Any]) -> Dict[str, Any]:
    """Discover features on a webpage."""
    from proofkit.intelligent_qa.feature_discovery import discover_features as discover

    url = args["url"]
    features = await discover(url)

    # Summarize by type
    by_type = {}
    for f in features:
        type_key = f.type.value
        by_type[type_key] = by_type.get(type_key, 0) + 1

    return {
        "url": url,
        "total_features": len(features),
        "by_type": by_type,
        "features": [
            {
                "id": f.id,
                "type": f.type.value,
                "text": f.text[:50] if f.text else "",
                "location": f.location,
                "expected_behavior": f.expected_behavior,
            }
            for f in features[:20]  # Limit to first 20
        ]
    }


async def analyze_data(args: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze collected raw data."""
    import json as json_module
    from proofkit.collector.models import RawData
    from proofkit.analyzer.engine import RuleEngine

    run_dir = Path(args["run_dir"])
    raw_data_path = run_dir / "raw" / "raw_data.json"

    if not raw_data_path.exists():
        return {"error": f"Raw data not found at {raw_data_path}"}

    data_dict = json_module.loads(raw_data_path.read_text())
    raw_data = RawData(**data_dict)

    engine = RuleEngine()
    findings, scores = engine.analyze(raw_data)

    return {
        "finding_count": len(findings),
        "scores": scores,
        "findings": [
            {
                "id": f.id,
                "severity": f.severity.value if hasattr(f.severity, "value") else str(f.severity),
                "category": f.category.value if hasattr(f.category, "value") else str(f.category),
                "title": f.title,
                "summary": f.summary,
            }
            for f in findings[:15]  # Limit
        ]
    }


async def generate_report(args: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a formatted report."""
    import json as json_module
    from proofkit.schemas.report import Report

    run_dir = Path(args["run_dir"])
    report_format = args.get("format", "markdown")

    report_path = run_dir / "out" / "report.json"
    if not report_path.exists():
        return {"error": f"Report not found at {report_path}"}

    report_data = json_module.loads(report_path.read_text())
    report = Report(**report_data)

    if report_format == "json":
        return report_data

    elif report_format == "markdown":
        md = f"# Audit Report: {report.meta.url}\n\n"
        md += f"**Score:** {report.overall_score}/100\n\n"
        md += "## Scorecard\n\n"
        for cat, score in report.scorecard.items():
            md += f"- {cat}: {score}/100\n"
        md += f"\n## Findings ({len(report.findings)} total)\n\n"
        for f in report.findings[:10]:
            sev = f.severity.value if hasattr(f.severity, "value") else str(f.severity)
            md += f"### [{sev}] {f.title}\n\n{f.summary}\n\n"
        return {"format": "markdown", "content": md}

    elif report_format == "pencil":
        from proofkit.report_builder.pencil_export import generate_pencil_report
        output_dir = run_dir / "pencil"
        result = generate_pencil_report(report, output_dir)
        return {
            "format": "pencil",
            "output_dir": str(output_dir),
            "files": result
        }

    return {"error": f"Unknown format: {report_format}"}


async def main():
    """Run the MCP server."""
    if not MCP_AVAILABLE:
        print("MCP package not installed. Install with: pip install mcp")
        return

    server = create_mcp_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)


if __name__ == "__main__":
    asyncio.run(main())
