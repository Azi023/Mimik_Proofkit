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


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
