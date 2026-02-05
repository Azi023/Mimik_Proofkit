"""Path utilities for ProofKit."""

from pathlib import Path
from datetime import datetime
from typing import Optional


def get_run_dir(base_dir: Path, run_id: Optional[str] = None) -> Path:
    """
    Get or create a run directory.

    Args:
        base_dir: Base output directory
        run_id: Optional run ID. If not provided, generates one.

    Returns:
        Path to the run directory
    """
    if run_id is None:
        run_id = f"run_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    run_dir = base_dir / run_id
    return run_dir


def setup_run_directories(run_dir: Path) -> dict:
    """
    Create the standard directory structure for an audit run.

    Args:
        run_dir: Root directory for the run

    Returns:
        Dict with paths to created directories
    """
    dirs = {
        "root": run_dir,
        "raw": run_dir / "raw",
        "out": run_dir / "out",
        "screenshots": run_dir / "raw" / "screenshots",
    }

    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)

    return dirs


def get_screenshot_path(run_dir: Path, page_name: str, suffix: str = "") -> Path:
    """
    Generate a path for a screenshot file.

    Args:
        run_dir: Root directory for the run
        page_name: Name of the page (sanitized)
        suffix: Optional suffix (e.g., "mobile", "desktop")

    Returns:
        Path for the screenshot file
    """
    screenshots_dir = run_dir / "raw" / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in page_name)
    if suffix:
        safe_name = f"{safe_name}_{suffix}"

    return screenshots_dir / f"{safe_name}.png"


def get_output_path(run_dir: Path, filename: str) -> Path:
    """
    Get path for an output file.

    Args:
        run_dir: Root directory for the run
        filename: Output filename

    Returns:
        Path for the output file
    """
    out_dir = run_dir / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / filename


def get_raw_data_path(run_dir: Path, collector_name: str) -> Path:
    """
    Get path for raw collector data.

    Args:
        run_dir: Root directory for the run
        collector_name: Name of the collector

    Returns:
        Path for the raw data JSON file
    """
    raw_dir = run_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    return raw_dir / f"{collector_name}.json"
