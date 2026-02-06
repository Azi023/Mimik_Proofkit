"""CLI interface for ProofKit."""

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from pathlib import Path
from typing import Optional

from proofkit.schemas.audit import AuditConfig, AuditMode
from proofkit.schemas.business import BusinessType

app = typer.Typer(
    name="proofkit",
    help="Mimik ProofKit - Website Audit QA Engineer",
    add_completion=False,
)
console = Console()


@app.command()
def run(
    url: str = typer.Option(..., "--url", "-u", help="Target website URL"),
    mode: str = typer.Option("fast", "--mode", "-m", help="Audit mode: fast|full"),
    business_type: Optional[str] = typer.Option(
        None, "--business-type", "-b", help="Business type for context"
    ),
    conversion_goal: Optional[str] = typer.Option(
        None, "--goal", "-g", help="Primary conversion goal"
    ),
    output_dir: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output directory"
    ),
    concept: bool = typer.Option(
        False, "--concept", "-c", help="Generate Lovable concept prompts"
    ),
    competitors: Optional[str] = typer.Option(
        None, "--competitors", help="Comma-separated competitor URLs"
    ),
    auto_detect: bool = typer.Option(
        False, "--auto-detect", help="Auto-detect business type"
    ),
):
    """
    Run a full website audit.

    Example:
        proofkit run --url https://example.com --mode fast
        proofkit run -u https://example.com -b real_estate --concept
    """
    from proofkit.core.runner import AuditRunner

    # Parse business type if provided
    btype = None
    if business_type:
        try:
            btype = BusinessType(business_type)
        except ValueError:
            console.print(f"[red]Invalid business type: {business_type}[/red]")
            console.print(f"Valid types: {', '.join(bt.value for bt in BusinessType)}")
            raise typer.Exit(1)

    # Parse audit mode
    try:
        audit_mode = AuditMode(mode)
    except ValueError:
        console.print(f"[red]Invalid mode: {mode}[/red]")
        console.print("Valid modes: fast, full")
        raise typer.Exit(1)

    config = AuditConfig(
        url=url,
        mode=audit_mode,
        business_type=btype,
        conversion_goal=conversion_goal,
        output_dir=output_dir,
        generate_concept=concept,
        competitor_urls=competitors.split(",") if competitors else [],
        auto_detect_business=auto_detect,
    )

    runner = AuditRunner(config)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Running audit...", total=100)

        def update_progress(pct: int):
            progress.update(task, completed=pct)

        result = runner.run(progress_callback=update_progress)

    console.print()
    console.print(f"[green]Audit complete![/green]")
    console.print(f"[dim]Output:[/dim] {result.output_dir}")
    console.print(f"[dim]Findings:[/dim] {result.finding_count}")
    console.print(f"[dim]Score:[/dim] {result.scorecard}")


@app.command()
def collect(
    url: str = typer.Option(..., "--url", "-u", help="Target website URL"),
    collector: str = typer.Option(
        "all", "--collector", help="Collector: playwright|lighthouse|http|all"
    ),
    output_dir: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output directory"
    ),
):
    """
    Run collectors only (no analysis).

    Example:
        proofkit collect --url https://example.com --collector playwright
    """
    console.print(f"[cyan]Collecting data from {url}...[/cyan]")
    console.print(f"[dim]Collector: {collector}[/dim]")

    # TODO: Implement when collector module is ready
    console.print("[yellow]Collector module not yet implemented[/yellow]")


@app.command()
def analyze(
    run_dir: Path = typer.Option(
        ..., "--run-dir", "-r", help="Path to run directory with raw data"
    ),
):
    """
    Run analyzer on existing collected data.

    Example:
        proofkit analyze --run-dir ./runs/run_20260129_143022
    """
    if not run_dir.exists():
        console.print(f"[red]Run directory not found: {run_dir}[/red]")
        raise typer.Exit(1)

    console.print(f"[cyan]Analyzing data from {run_dir}...[/cyan]")

    # TODO: Implement when analyzer module is ready
    console.print("[yellow]Analyzer module not yet implemented[/yellow]")


@app.command()
def narrate(
    run_dir: Path = typer.Option(
        ..., "--run-dir", "-r", help="Path to run directory with findings"
    ),
):
    """
    Generate AI narrative from findings.

    Example:
        proofkit narrate --run-dir ./runs/run_20260129_143022
    """
    if not run_dir.exists():
        console.print(f"[red]Run directory not found: {run_dir}[/red]")
        raise typer.Exit(1)

    console.print(f"[cyan]Generating narrative for {run_dir}...[/cyan]")

    # TODO: Implement when narrator module is ready
    console.print("[yellow]Narrator module not yet implemented[/yellow]")


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to listen on"),
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable auto-reload"),
):
    """
    Start the API server.

    Example:
        proofkit serve
        proofkit serve --port 8080 --reload
    """
    import uvicorn

    console.print(f"[cyan]Starting ProofKit API server...[/cyan]")
    console.print(f"[dim]Host:[/dim] {host}")
    console.print(f"[dim]Port:[/dim] {port}")
    console.print(f"[dim]Docs:[/dim] http://{host if host != '0.0.0.0' else 'localhost'}:{port}/docs")
    console.print()

    uvicorn.run(
        "proofkit.api.main:app",
        host=host,
        port=port,
        reload=reload,
    )


@app.command()
def version():
    """Show version information."""
    from proofkit import __version__

    console.print(f"Mimik ProofKit v{__version__}")


@app.command()
def export_pencil(
    run_dir: Path = typer.Option(
        ..., "--run-dir", "-r", help="Path to completed audit run"
    ),
    output_dir: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output directory for Pencil prompts"
    ),
):
    """
    Export audit report as Pencil.dev prompts.

    Pencil (pencil.dev) is a free AI-powered design tool that can
    generate professional reports from text prompts.

    Example:
        proofkit export-pencil --run-dir ./runs/run_20260129_143022
    """
    import json
    from proofkit.report_builder.pencil_export import generate_pencil_report
    from proofkit.schemas.report import Report

    # Load report
    report_path = run_dir / "out" / "report.json"
    if not report_path.exists():
        # Try alternate location
        report_path = run_dir / "report.json"

    if not report_path.exists():
        console.print(f"[red]Report not found at {report_path}[/red]")
        console.print("[dim]Make sure to run a complete audit first.[/dim]")
        raise typer.Exit(1)

    try:
        report_data = json.loads(report_path.read_text())
        report = Report(**report_data)
    except Exception as e:
        console.print(f"[red]Failed to load report: {e}[/red]")
        raise typer.Exit(1)

    # Generate Pencil prompts
    output = output_dir or (run_dir / "pencil")
    result = generate_pencil_report(report, output)

    console.print(f"[green]✓ Pencil prompts generated![/green]")
    console.print(f"[dim]Full report prompt:[/dim] {result['full_prompt_path']}")
    console.print(f"[dim]Sections:[/dim] {', '.join(result['section_prompts'])}")
    console.print()
    console.print("[cyan]To use:[/cyan]")
    console.print("1. Open Pencil (VS Code extension or ~/Applications/pencil)")
    console.print("2. Copy the content from pencil_full_report.txt")
    console.print("3. Paste into Pencil and generate")


@app.command()
def discover_features(
    url: str = typer.Argument(..., help="URL to analyze"),
    output_dir: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output directory for generated tests"
    ),
    generate_tests: bool = typer.Option(
        True, "--tests/--no-tests", help="Generate Playwright test files"
    ),
):
    """
    Discover interactive features on a webpage and generate tests.

    This tool automatically finds all interactive elements (forms, buttons,
    navigation, etc.) and generates Playwright test scripts for them.

    Example:
        proofkit discover-features https://example.com
        proofkit discover-features https://example.com --output ./qa_tests
    """
    import asyncio
    from proofkit.intelligent_qa.feature_discovery import FeatureDiscovery, discover_features as discover
    from proofkit.intelligent_qa.test_generator import TestGenerator

    console.print(f"[cyan]Discovering features on {url}...[/cyan]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Scanning page...", total=None)

        try:
            features = asyncio.run(discover(url))
        except Exception as e:
            console.print(f"[red]Discovery failed: {e}[/red]")
            raise typer.Exit(1)

    console.print(f"[green]Found {len(features)} interactive features[/green]")
    console.print()

    # Display summary by type
    by_type = {}
    for f in features:
        type_key = f.type.value
        by_type[type_key] = by_type.get(type_key, 0) + 1

    console.print("[bold]Features by type:[/bold]")
    for ftype, count in sorted(by_type.items(), key=lambda x: -x[1]):
        console.print(f"  {ftype}: {count}")

    # Generate tests if requested
    if generate_tests:
        console.print()
        generator = TestGenerator(features, url)
        output = output_dir or Path("./qa_tests")

        files = generator.save_tests(output)

        console.print(f"[green]Test files generated![/green]")
        console.print(f"[dim]Tests:[/dim] {files['tests']}")
        console.print(f"[dim]Config:[/dim] {files['conftest']}")
        console.print(f"[dim]Summary:[/dim] {files['summary']}")
        console.print()
        console.print("[cyan]To run tests:[/cyan]")
        console.print(f"  cd {output}")
        console.print(f"  pytest test_generated_qa.py -v")


@app.command()
def api_key(
    action: str = typer.Argument(
        "show",
        help="Action: show|regenerate",
    ),
):
    """
    Manage API keys for the local development server.

    Example:
        proofkit api-key show
        proofkit api-key regenerate
    """
    import asyncio
    from proofkit.api.database import init_db, get_db
    from proofkit.api.database.crud import get_user_by_email, update_user_api_key
    from proofkit.api.auth.api_keys import generate_api_key

    async def manage_key():
        await init_db()

        async for session in get_db():
            user = await get_user_by_email("admin@proofkit.local")

            if not user:
                console.print("[red]No default user found. Start the server first.[/red]")
                return

            if action == "show":
                console.print(f"[green]API Key:[/green] {user.api_key}")
            elif action == "regenerate":
                new_key = generate_api_key("pk_dev")
                await update_user_api_key(user.id, new_key)
                console.print(f"[green]New API Key:[/green] {new_key}")
            else:
                console.print(f"[red]Unknown action: {action}[/red]")
                console.print("Valid actions: show, regenerate")
            break

    asyncio.run(manage_key())


@app.command()
def check_lighthouse():
    """
    Check Lighthouse requirements and show setup instructions.

    Example:
        proofkit check-lighthouse
    """
    from proofkit.collector.lighthouse import LighthouseCollector

    console.print("[cyan]Checking Lighthouse Requirements...[/cyan]")
    console.print()

    collector = LighthouseCollector()
    status = collector.check_requirements()

    # Lighthouse CLI
    if status["lighthouse_cli"]:
        console.print("[green]Lighthouse CLI:[/green] Installed")
    else:
        console.print("[red]Lighthouse CLI:[/red] Not installed")

    # Chrome/Chromium
    if status["chrome_available"]:
        console.print(f"[green]Chrome/Chromium:[/green] Found at {status['chrome_path']}")
    else:
        console.print("[red]Chrome/Chromium:[/red] Not found")

    console.print()

    if status["ready"]:
        console.print("[green]Lighthouse is ready to use![/green]")
    else:
        console.print("[yellow]Setup Required:[/yellow]")
        console.print()
        console.print(status["setup_instructions"])


@app.command()
def models():
    """
    List available AI models and their capabilities.

    Example:
        proofkit models
    """
    from proofkit.narrator.ai_client import list_available_models, TASK_MODEL_MAPPING, ModelTier
    import os

    console.print("[cyan]Available AI Models[/cyan]")
    console.print()

    all_models = list_available_models()

    # OpenAI Models
    console.print("[bold]OpenAI Models:[/bold]")
    for model, desc in all_models["openai"].items():
        console.print(f"  [green]{model}[/green]")
        console.print(f"    {desc}")
    console.print()

    # Anthropic Models
    console.print("[bold]Anthropic Models:[/bold]")
    for model, desc in all_models["anthropic"].items():
        console.print(f"  [green]{model}[/green]")
        console.print(f"    {desc}")
    console.print()

    # Task-based model selection
    console.print("[bold]Automatic Model Selection by Task:[/bold]")
    for task, tier in TASK_MODEL_MAPPING.items():
        console.print(f"  {task}: {tier.value}")
    console.print()

    # Current configuration
    provider = os.getenv("AI_PROVIDER", "anthropic")
    model = os.getenv("OPENAI_MODEL" if provider == "openai" else "ANTHROPIC_MODEL", "default")
    console.print(f"[bold]Current Config:[/bold]")
    console.print(f"  Provider: {provider}")
    console.print(f"  Default Model: {model}")
    console.print()

    console.print("[dim]To change model, edit OPENAI_MODEL or ANTHROPIC_MODEL in .env[/dim]")


@app.command()
def test_ai():
    """
    Test AI connection and show configuration.

    Example:
        proofkit test-ai
    """
    import os
    from proofkit.narrator.ai_client import get_ai_client, AIClientFactory

    console.print("[cyan]Testing AI Connection...[/cyan]")
    console.print()

    # Show current config
    provider = os.getenv("AI_PROVIDER", "anthropic")
    console.print(f"[dim]AI Provider:[/dim] {provider}")

    if provider == "openai":
        key = os.getenv("OPENAI_API_KEY", "")
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        console.print(f"[dim]Model:[/dim] {model}")
        console.print(f"[dim]API Key:[/dim] {'*' * 20}...{key[-8:] if len(key) > 8 else 'NOT SET'}")
    else:
        key = os.getenv("ANTHROPIC_API_KEY", "")
        model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
        console.print(f"[dim]Model:[/dim] {model}")
        console.print(f"[dim]API Key:[/dim] {'*' * 20}...{key[-8:] if len(key) > 8 else 'NOT SET'}")

    console.print()

    try:
        # Reset factory to pick up new env vars
        AIClientFactory.reset()
        client = get_ai_client()

        console.print("[cyan]Sending test request...[/cyan]")

        response = client.generate(
            system_prompt="You are a helpful assistant. Respond in exactly one sentence.",
            user_prompt="Say 'ProofKit AI is working!' and nothing else.",
            max_tokens=50,
        )

        console.print(f"[green]Response:[/green] {response}")

        usage = client.get_last_usage()
        console.print(f"[dim]Tokens used:[/dim] {usage.get('input_tokens', 0)} in, {usage.get('output_tokens', 0)} out")
        console.print()
        console.print("[green]AI connection successful![/green]")

    except Exception as e:
        console.print(f"[red]AI connection failed: {e}[/red]")
        console.print()
        console.print("[yellow]Troubleshooting:[/yellow]")
        console.print("1. Check your .env file has the correct API key")
        console.print("2. Verify AI_PROVIDER is set to 'openai' or 'anthropic'")
        console.print("3. Make sure the API key is valid")
        raise typer.Exit(1)


@app.command()
def analyze_codebase(
    path: Path = typer.Argument(..., help="Path to codebase directory"),
    output_dir: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output directory for analysis"
    ),
    include: Optional[str] = typer.Option(
        None, "--include", "-i", help="File patterns to include (e.g., '*.py,*.ts')"
    ),
    exclude: Optional[str] = typer.Option(
        None, "--exclude", "-e", help="Patterns to exclude (e.g., 'node_modules,__pycache__')"
    ),
    generate_tests: bool = typer.Option(
        False, "--tests", "-t", help="Generate test scripts for discovered components"
    ),
):
    """
    Analyze a codebase and generate QA documentation.

    This command scans a codebase to understand its structure, identify
    components, and optionally generate test scripts.

    Example:
        proofkit analyze-codebase ./my-project
        proofkit analyze-codebase ./my-project --include "*.py" --tests
    """
    from proofkit.codebase_qa.analyzer import CodebaseAnalyzer

    if not path.exists():
        console.print(f"[red]Path not found: {path}[/red]")
        raise typer.Exit(1)

    console.print(f"[cyan]Analyzing codebase at {path}...[/cyan]")

    include_patterns = include.split(",") if include else None
    exclude_patterns = exclude.split(",") if exclude else None

    try:
        analyzer = CodebaseAnalyzer(
            path,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Scanning files...", total=None)
            result = analyzer.analyze()

        console.print()
        console.print(f"[green]Analysis complete![/green]")
        console.print(f"[dim]Files analyzed:[/dim] {result.file_count}")
        console.print(f"[dim]Components found:[/dim] {result.component_count}")
        console.print(f"[dim]Functions found:[/dim] {result.function_count}")

        # Save output
        output = output_dir or (path / "proofkit_analysis")
        result.save(output)
        console.print(f"[dim]Output saved to:[/dim] {output}")

        if generate_tests:
            console.print()
            console.print("[cyan]Generating test scripts...[/cyan]")
            test_result = analyzer.generate_tests(output / "tests")
            console.print(f"[green]Tests generated:[/green] {test_result['test_count']} test cases")

    except Exception as e:
        console.print(f"[red]Analysis failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def deduplicate(
    run_dir: Path = typer.Option(
        ..., "--run-dir", "-r", help="Path to run directory with findings"
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output file for deduplicated findings"
    ),
    top_n: int = typer.Option(
        50, "--top", "-n", help="Number of top findings to show by business impact"
    ),
    business_type: Optional[str] = typer.Option(
        None, "--business-type", "-b", help="Business type for impact scoring"
    ),
):
    """
    Deduplicate findings from an existing audit run.

    This command reads the raw findings from an audit run, removes duplicates,
    and scores them by business impact. Useful for reducing 400+ findings
    down to 50-80 actionable items.

    Example:
        proofkit deduplicate --run-dir ./runs/run_20260206_123456
        proofkit deduplicate -r ./runs/run_20260206_123456 --top 30 -b real_estate
    """
    import json
    from proofkit.analyzer.deduplication import deduplicate_with_stats
    from proofkit.analyzer.impact_scorer import score_by_business_impact
    from proofkit.schemas.finding import Finding

    # Find findings file
    findings_path = run_dir / "out" / "findings.json"
    if not findings_path.exists():
        findings_path = run_dir / "findings.json"

    if not findings_path.exists():
        console.print(f"[red]Findings not found at {findings_path}[/red]")
        console.print("[dim]Make sure to run a complete audit first.[/dim]")
        raise typer.Exit(1)

    console.print(f"[cyan]Loading findings from {findings_path}...[/cyan]")

    try:
        findings_data = json.loads(findings_path.read_text())
        findings = [Finding(**f) for f in findings_data]
    except Exception as e:
        console.print(f"[red]Failed to load findings: {e}[/red]")
        raise typer.Exit(1)

    console.print(f"[dim]Loaded {len(findings)} raw findings[/dim]")
    console.print()

    # Deduplicate
    console.print("[cyan]Deduplicating findings...[/cyan]")
    deduplicated, stats = deduplicate_with_stats(findings)

    console.print(f"[green]Deduplication complete![/green]")
    console.print(f"  Original: {stats['original_count']} findings")
    console.print(f"  After rule ID dedup: {stats['after_rule_id_dedup']} findings")
    console.print(f"  After similarity dedup: {stats['after_similarity_dedup']} findings")
    console.print(f"  Duplicates merged: {stats['duplicates_merged']}")
    console.print()

    # Score by business impact
    console.print("[cyan]Scoring by business impact...[/cyan]")
    scored = score_by_business_impact(deduplicated, business_type)

    console.print()
    console.print(f"[bold]Top {min(top_n, len(scored))} Findings by Business Impact:[/bold]")
    console.print()

    for i, sf in enumerate(scored[:top_n], 1):
        severity = sf.finding.severity
        sev_val = severity.value if hasattr(severity, 'value') else severity

        # Color code by impact score
        if sf.impact_score >= 80:
            score_color = "red"
        elif sf.impact_score >= 60:
            score_color = "yellow"
        else:
            score_color = "green"

        console.print(f"[bold]{i:2d}.[/bold] [{score_color}]{sf.impact_score:.0f}[/{score_color}] "
                      f"[{sev_val}] {sf.finding.title[:60]}")
        console.print(f"     [dim]{sf.impact_category.value}: {sf.revenue_impact}[/dim]")

    # Save output if requested
    if output:
        output_data = {
            "stats": stats,
            "findings": [
                {
                    "rank": sf.priority_rank,
                    "impact_score": sf.impact_score,
                    "impact_category": sf.impact_category.value,
                    "revenue_impact": sf.revenue_impact,
                    **sf.finding.model_dump(),
                }
                for sf in scored
            ]
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(output_data, indent=2))
        console.print()
        console.print(f"[green]Saved to {output}[/green]")

    # Summary by category
    console.print()
    console.print("[bold]Summary by Impact Category:[/bold]")
    by_category = {}
    for sf in scored:
        cat = sf.impact_category.value
        by_category[cat] = by_category.get(cat, 0) + 1

    for cat, count in sorted(by_category.items(), key=lambda x: -x[1]):
        console.print(f"  {cat}: {count}")

    console.print()
    console.print(f"[green]Reduced {len(findings)} raw findings to {len(deduplicated)} unique findings![/green]")


@app.command()
def experience_test(
    url: str = typer.Argument(..., help="URL to test"),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output JSON file for results"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed metrics"
    ),
):
    """
    Run Experience Agent to detect human-like UX friction.

    This simulates a human user experiencing the website and detects
    issues that automated scans miss, such as:
    - Laggy custom cursors
    - Layout shifts (CLS)
    - Slow-loading hero images
    - Scroll jank
    - Confusing navigation
    - Form friction

    Example:
        proofkit experience-test https://www.seventides.com
        proofkit experience-test https://example.com -o results.json -v
    """
    import asyncio
    import json
    from proofkit.agents.experience_agent import run_experience_test

    console.print(f"[cyan]Running Experience Agent on {url}...[/cyan]")
    console.print("[dim]This simulates a human user to detect UX friction[/dim]")
    console.print()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Experiencing page...", total=None)

        try:
            result = asyncio.run(run_experience_test(url))
        except Exception as e:
            console.print(f"[red]Experience test failed: {e}[/red]")
            raise typer.Exit(1)

    # Display results
    frictions = result.get('frictions', [])
    summary = result.get('summary', {})

    console.print(f"[green]Experience test complete![/green]")
    console.print()

    if not frictions:
        console.print("[green]No significant UX friction detected.[/green]")
    else:
        console.print(f"[bold]Found {len(frictions)} UX Friction Points:[/bold]")
        console.print()

        # Group by severity
        by_severity = summary.get('by_severity', {})
        if by_severity.get('critical', 0) > 0:
            console.print(f"  [red]Critical: {by_severity['critical']}[/red]")
        if by_severity.get('high', 0) > 0:
            console.print(f"  [yellow]High: {by_severity['high']}[/yellow]")
        if by_severity.get('medium', 0) > 0:
            console.print(f"  [blue]Medium: {by_severity['medium']}[/blue]")
        if by_severity.get('low', 0) > 0:
            console.print(f"  [dim]Low: {by_severity['low']}[/dim]")

        console.print()

        # Display each friction
        for i, friction in enumerate(frictions, 1):
            sev = friction['severity']
            if sev == 'critical':
                sev_color = 'red'
            elif sev == 'high':
                sev_color = 'yellow'
            elif sev == 'medium':
                sev_color = 'blue'
            else:
                sev_color = 'dim'

            console.print(f"[bold]{i}. [{sev_color}]{sev.upper()}[/{sev_color}] {friction['type']}[/bold]")
            console.print(f"   [dim]Location:[/dim] {friction['location']}")
            console.print(f"   {friction['description'][:200]}...")
            console.print(f"   [cyan]Recommendation:[/cyan] {friction['recommendation'][:150]}...")
            console.print()

    # Show metrics if verbose
    if verbose:
        metrics = result.get('metrics', {})
        console.print("[bold]Detailed Metrics:[/bold]")
        console.print()

        if metrics.get('cursor'):
            cursor = metrics['cursor']
            console.print("[dim]Cursor Analysis:[/dim]")
            console.print(f"  Custom cursor elements: {cursor.get('cursorElementCount', 0)}")
            console.print(f"  Has GSAP: {cursor.get('hasGSAP', False)}")

        if metrics.get('cls'):
            cls = metrics['cls']
            console.print(f"[dim]Layout Shift (CLS):[/dim] {cls.get('score', 0):.3f}")

        if metrics.get('scroll'):
            scroll = metrics['scroll']
            console.print(f"[dim]Scroll Jank Events:[/dim] {scroll.get('jankCount', 0)}")

        if metrics.get('navigation'):
            nav = metrics['navigation']
            console.print(f"[dim]Navigation Items:[/dim] {nav.get('topLevelItems', 0)}")

    # Save output if requested
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2))
        console.print()
        console.print(f"[green]Results saved to {output}[/green]")


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
