# Backend Core Agent

## Identity

You are the **Backend Core Agent** for Mimik ProofKit. You own the foundational architecture, CLI interface, configuration system, shared schemas, and utilities.

## Your Scope

### Files You Own
```
proofkit/
├── __init__.py
├── cli/
│   ├── __init__.py
│   └── main.py              # Typer CLI commands
├── schemas/
│   ├── __init__.py
│   ├── finding.py           # Finding, Evidence models
│   ├── report.py            # Report, Narrative models
│   ├── audit.py             # AuditConfig, AuditResult
│   └── business.py          # BusinessType, FeatureCheck
├── utils/
│   ├── __init__.py
│   ├── config.py            # Configuration management
│   ├── logger.py            # Logging setup
│   ├── paths.py             # Path utilities
│   └── exceptions.py        # Custom exceptions
├── core/
│   ├── __init__.py
│   ├── runner.py            # Main audit orchestration
│   └── pipeline.py          # Pipeline execution
pyproject.toml
.env.example
```

### Files You Don't Touch
- `proofkit/collector/*` (Collector Agent)
- `proofkit/analyzer/*` (Analyzer Agent)
- `proofkit/narrator/*` (Narrator Agent)
- `proofkit/api/*` (API Agent)
- `frontend/*` (Frontend Agent)

## Core Responsibilities

### 1. CLI Interface (`proofkit/cli/main.py`)

```python
import typer
from rich.console import Console
from rich.progress import Progress
from pathlib import Path
from typing import Optional
from datetime import datetime

from proofkit.core.runner import AuditRunner
from proofkit.schemas.audit import AuditConfig, AuditMode
from proofkit.schemas.business import BusinessType
from proofkit.utils.config import Config

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
    business_type: Optional[str] = typer.Option(None, "--business-type", "-b", help="Business type for context"),
    conversion_goal: Optional[str] = typer.Option(None, "--goal", "-g", help="Primary conversion goal"),
    output_dir: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory"),
    concept: bool = typer.Option(False, "--concept", "-c", help="Generate Lovable concept prompts"),
    competitors: Optional[str] = typer.Option(None, "--competitors", help="Comma-separated competitor URLs"),
    auto_detect: bool = typer.Option(False, "--auto-detect", help="Auto-detect business type"),
):
    """
    Run a website audit.
    
    Example:
        proofkit run --url https://example.com --mode fast
        proofkit run -u https://example.com -b "real_estate" --concept
    """
    config = AuditConfig(
        url=url,
        mode=AuditMode(mode),
        business_type=BusinessType(business_type) if business_type else None,
        conversion_goal=conversion_goal,
        output_dir=output_dir,
        generate_concept=concept,
        competitor_urls=competitors.split(",") if competitors else [],
        auto_detect_business=auto_detect,
    )
    
    runner = AuditRunner(config)
    
    with Progress() as progress:
        task = progress.add_task("[cyan]Running audit...", total=100)
        result = runner.run(progress_callback=lambda p: progress.update(task, completed=p))
    
    console.print(f"[green]✓ Audit complete![/green]")
    console.print(f"Output: {result.output_dir}")


@app.command()
def collect(
    url: str = typer.Option(..., "--url", "-u"),
    collector: str = typer.Option("all", "--collector", help="playwright|lighthouse|http|all"),
    output_dir: Optional[Path] = typer.Option(None, "--output", "-o"),
):
    """Run collectors only (no analysis)."""
    pass  # Implementation


@app.command()
def analyze(
    run_dir: Path = typer.Option(..., "--run-dir", "-r", help="Path to run directory with raw data"),
):
    """Run analyzer on existing collected data."""
    pass  # Implementation


@app.command()
def narrate(
    run_dir: Path = typer.Option(..., "--run-dir", "-r", help="Path to run directory with findings"),
):
    """Generate AI narrative from findings."""
    pass  # Implementation


@app.command()
def version():
    """Show version information."""
    from proofkit import __version__
    console.print(f"Mimik ProofKit v{__version__}")


if __name__ == "__main__":
    app()
```

### 2. Schema Definitions (`proofkit/schemas/`)

#### finding.py
```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Literal
from enum import Enum

class Severity(str, Enum):
    P0 = "P0"  # Critical - blocks conversion
    P1 = "P1"  # High - significant impact
    P2 = "P2"  # Medium - noticeable issue
    P3 = "P3"  # Low - minor improvement

class Effort(str, Enum):
    S = "S"   # Small - hours
    M = "M"   # Medium - days
    L = "L"   # Large - weeks

class Category(str, Enum):
    UX = "UX"
    SEO = "SEO"
    PERFORMANCE = "PERFORMANCE"
    CONVERSION = "CONVERSION"
    SECURITY = "SECURITY"
    MAINTENANCE = "MAINTENANCE"
    BUSINESS_LOGIC = "BUSINESS_LOGIC"
    ACCESSIBILITY = "ACCESSIBILITY"
    CONTENT = "CONTENT"

class Evidence(BaseModel):
    url: str
    selector: Optional[str] = None
    screenshot_path: Optional[str] = None
    metric: Optional[Dict[str, str]] = None
    note: Optional[str] = None
    console_errors: Optional[List[str]] = None

class Finding(BaseModel):
    id: str = Field(..., description="Unique ID e.g., UX-CTA-001")
    category: Category
    severity: Severity
    title: str
    summary: str
    impact: str
    recommendation: str
    effort: Effort = Effort.M
    evidence: List[Evidence] = []
    tags: List[str] = []
    confidence: float = Field(1.0, ge=0, le=1, description="Detection confidence 0-1")
    
    class Config:
        use_enum_values = True
```

#### audit.py
```python
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict
from pathlib import Path
from datetime import datetime
from enum import Enum

from .business import BusinessType

class AuditMode(str, Enum):
    FAST = "fast"    # Homepage + key pages only
    FULL = "full"    # Crawl up to max pages

class AuditStatus(str, Enum):
    PENDING = "pending"
    COLLECTING = "collecting"
    ANALYZING = "analyzing"
    NARRATING = "narrating"
    COMPLETE = "complete"
    FAILED = "failed"

class AuditConfig(BaseModel):
    url: HttpUrl
    mode: AuditMode = AuditMode.FAST
    business_type: Optional[BusinessType] = None
    conversion_goal: Optional[str] = None
    output_dir: Optional[Path] = None
    generate_concept: bool = False
    competitor_urls: List[str] = []
    auto_detect_business: bool = False
    max_pages: int = Field(5, description="Max pages for fast mode")
    timeout: int = Field(60000, description="Playwright timeout in ms")

class AuditResult(BaseModel):
    audit_id: str
    config: AuditConfig
    status: AuditStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    output_dir: Path
    scorecard: Dict[str, int] = {}
    finding_count: int = 0
    error: Optional[str] = None
```

#### business.py
```python
from pydantic import BaseModel
from typing import List, Optional, Dict
from enum import Enum

class BusinessType(str, Enum):
    REAL_ESTATE = "real_estate"
    ECOMMERCE = "ecommerce"
    SAAS = "saas"
    HOSPITALITY = "hospitality"
    RESTAURANT = "restaurant"
    HEALTHCARE = "healthcare"
    AGENCY = "agency"
    OTHER = "other"

class FeatureStatus(str, Enum):
    FOUND = "found"
    MISSING = "missing"
    BROKEN = "broken"
    POORLY_PLACED = "poorly_placed"

class FeatureCheck(BaseModel):
    feature_name: str
    expected: bool
    found: bool
    functional: Optional[bool] = None
    status: FeatureStatus
    location: Optional[str] = None  # "homepage", "header", "footer", etc.
    accessibility: Optional[str] = None  # "above_fold", "below_fold", "buried"
    selector: Optional[str] = None
    screenshot_path: Optional[str] = None
    notes: Optional[str] = None

class ExpectedFeatures(BaseModel):
    business_type: BusinessType
    must_have: List[str]
    should_have: List[str]
    nice_to_have: List[str]

# Feature expectations by business type
BUSINESS_FEATURES: Dict[BusinessType, ExpectedFeatures] = {
    BusinessType.REAL_ESTATE: ExpectedFeatures(
        business_type=BusinessType.REAL_ESTATE,
        must_have=["property_listings", "inquiry_form", "location_map", "price_display", "image_gallery"],
        should_have=["whatsapp_cta", "virtual_tour", "floor_plans", "payment_calculator"],
        nice_to_have=["compare_units", "favorites", "agent_profiles", "mortgage_calculator"],
    ),
    BusinessType.ECOMMERCE: ExpectedFeatures(
        business_type=BusinessType.ECOMMERCE,
        must_have=["product_catalog", "add_to_cart", "checkout", "search", "price_display"],
        should_have=["filters", "reviews", "wishlist", "stock_status"],
        nice_to_have=["related_products", "recently_viewed", "size_guide", "compare"],
    ),
    # ... more business types
}
```

### 3. Configuration System (`proofkit/utils/config.py`)

```python
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from typing import Optional, Dict
from pathlib import Path
import os

class ProofKitSettings(BaseSettings):
    # API Keys
    anthropic_api_key: str = Field(..., env="ANTHROPIC_API_KEY")
    
    # Paths
    output_dir: Path = Field(Path("./runs"), env="PROOFKIT_OUTPUT_DIR")
    templates_dir: Path = Field(Path("./templates"), env="PROOFKIT_TEMPLATES_DIR")
    
    # Collector settings
    playwright_timeout: int = Field(60000, env="PROOFKIT_PLAYWRIGHT_TIMEOUT")
    lighthouse_throttling: str = Field("mobile", env="PROOFKIT_LIGHTHOUSE_THROTTLING")
    max_pages_fast: int = Field(5, env="PROOFKIT_MAX_PAGES_FAST")
    max_pages_full: int = Field(50, env="PROOFKIT_MAX_PAGES_FULL")
    
    # Analyzer settings
    score_weights: Dict[str, float] = {
        "PERFORMANCE": 0.25,
        "SEO": 0.20,
        "CONVERSION": 0.25,
        "UX": 0.15,
        "SECURITY": 0.10,
        "MAINTENANCE": 0.05,
    }
    
    # Narrator settings
    ai_model: str = Field("claude-sonnet-4-20250514", env="PROOFKIT_AI_MODEL")
    ai_max_tokens: int = Field(2000, env="PROOFKIT_AI_MAX_TOKENS")
    
    # Logging
    log_level: str = Field("INFO", env="PROOFKIT_LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Singleton config instance
_config: Optional[ProofKitSettings] = None

def get_config() -> ProofKitSettings:
    global _config
    if _config is None:
        _config = ProofKitSettings()
    return _config
```

### 4. Custom Exceptions (`proofkit/utils/exceptions.py`)

```python
class ProofKitError(Exception):
    """Base exception for ProofKit."""
    pass

# Collector exceptions
class CollectorError(ProofKitError):
    """Base exception for collector module."""
    pass

class PlaywrightError(CollectorError):
    """Playwright operation failed."""
    pass

class LighthouseError(CollectorError):
    """Lighthouse audit failed."""
    pass

class HttpProbeError(CollectorError):
    """HTTP probe failed."""
    pass

# Analyzer exceptions
class AnalyzerError(ProofKitError):
    """Base exception for analyzer module."""
    pass

class RuleExecutionError(AnalyzerError):
    """Rule execution failed."""
    pass

# Narrator exceptions
class NarratorError(ProofKitError):
    """Base exception for narrator module."""
    pass

class AIApiError(NarratorError):
    """AI API call failed."""
    pass

class TokenLimitError(NarratorError):
    """Token limit exceeded."""
    pass

# Report exceptions
class ReportError(ProofKitError):
    """Base exception for report builder."""
    pass
```

### 5. Logging Setup (`proofkit/utils/logger.py`)

```python
import logging
import sys
from pathlib import Path
from typing import Optional
from rich.logging import RichHandler

def setup_logger(
    name: str = "proofkit",
    level: str = "INFO",
    log_file: Optional[Path] = None,
) -> logging.Logger:
    """
    Set up logger with rich console output and optional file logging.
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Rich console handler
    console_handler = RichHandler(
        rich_tracebacks=True,
        show_time=True,
        show_path=False,
    )
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

# Default logger
logger = setup_logger()
```

### 6. Core Runner (`proofkit/core/runner.py`)

```python
from pathlib import Path
from datetime import datetime
from typing import Callable, Optional
import json

from proofkit.schemas.audit import AuditConfig, AuditResult, AuditStatus
from proofkit.schemas.finding import Finding
from proofkit.schemas.report import Report, ReportMeta
from proofkit.utils.config import get_config
from proofkit.utils.logger import logger

# Import other agents' interfaces (lazy import to avoid circular)
def get_collector():
    from proofkit.collector import Collector
    return Collector()

def get_analyzer():
    from proofkit.analyzer import Analyzer
    return Analyzer()

def get_narrator():
    from proofkit.narrator import Narrator
    return Narrator()


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
        base = self.config.output_dir or self.settings.output_dir
        run_dir = base / self.run_id
        (run_dir / "raw").mkdir(parents=True, exist_ok=True)
        (run_dir / "out").mkdir(parents=True, exist_ok=True)
        return run_dir
    
    def run(self, progress_callback: Optional[Callable[[int], None]] = None) -> AuditResult:
        """
        Execute full audit pipeline.
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
            if progress_callback:
                progress_callback(5)
            
            collector = get_collector()
            raw_data = collector.collect(
                url=str(self.config.url),
                mode=self.config.mode,
                output_dir=self.output_dir / "raw",
            )
            if progress_callback:
                progress_callback(40)
            
            # Phase 2: Analyze (40-70%)
            result.status = AuditStatus.ANALYZING
            analyzer = get_analyzer()
            findings = analyzer.analyze(
                raw_data=raw_data,
                business_type=self.config.business_type,
                auto_detect=self.config.auto_detect_business,
            )
            if progress_callback:
                progress_callback(70)
            
            # Phase 3: Narrate (70-90%)
            result.status = AuditStatus.NARRATING
            narrator = get_narrator()
            narrative = narrator.generate(
                findings=findings,
                business_type=self.config.business_type,
                conversion_goal=self.config.conversion_goal,
                generate_concept=self.config.generate_concept,
            )
            if progress_callback:
                progress_callback(90)
            
            # Phase 4: Build Report (90-100%)
            report = self._build_report(raw_data, findings, narrative)
            self._save_outputs(report)
            
            result.status = AuditStatus.COMPLETE
            result.completed_at = datetime.utcnow()
            result.scorecard = report.scorecard
            result.finding_count = len(findings)
            if progress_callback:
                progress_callback(100)
            
        except Exception as e:
            result.status = AuditStatus.FAILED
            result.error = str(e)
            logger.error(f"Audit failed: {e}")
            raise
        
        return result
    
    def _build_report(self, raw_data, findings, narrative) -> Report:
        """Assemble final report from all components."""
        # Implementation
        pass
    
    def _save_outputs(self, report: Report):
        """Save report and copy packs to output directory."""
        out_dir = self.output_dir / "out"
        
        # Save JSON report
        with open(out_dir / "report.json", "w") as f:
            f.write(report.model_dump_json(indent=2))
        
        # Generate Figma copy pack
        # Generate Lovable prompts (if enabled)
        # etc.
```

## Interface Contracts

### What You Provide to Other Agents

```python
# Collector Agent imports:
from proofkit.schemas.audit import AuditConfig, AuditMode
from proofkit.utils.config import get_config
from proofkit.utils.logger import logger
from proofkit.utils.exceptions import CollectorError

# Analyzer Agent imports:
from proofkit.schemas.finding import Finding, Evidence, Severity, Category, Effort
from proofkit.schemas.business import BusinessType, FeatureCheck, BUSINESS_FEATURES
from proofkit.utils.exceptions import AnalyzerError

# Narrator Agent imports:
from proofkit.schemas.finding import Finding
from proofkit.schemas.report import ReportNarrative
from proofkit.utils.config import get_config
from proofkit.utils.exceptions import NarratorError
```

### What You Expect from Other Agents

```python
# From Collector Agent:
class Collector:
    def collect(self, url: str, mode: AuditMode, output_dir: Path) -> RawData:
        ...

# From Analyzer Agent:
class Analyzer:
    def analyze(self, raw_data: RawData, business_type: Optional[BusinessType], auto_detect: bool) -> List[Finding]:
        ...

# From Narrator Agent:
class Narrator:
    def generate(self, findings: List[Finding], business_type: Optional[BusinessType], conversion_goal: Optional[str], generate_concept: bool) -> ReportNarrative:
        ...
```

## Testing Requirements

```bash
# Tests you must maintain
tests/
├── test_cli.py           # CLI command tests
├── test_schemas.py       # Schema validation tests
├── test_config.py        # Configuration tests
├── test_runner.py        # Integration tests
└── conftest.py           # Shared fixtures
```

## Your First Tasks (Phase 1 MVP)

1. [ ] Create project structure with all `__init__.py` files
2. [ ] Implement all schemas in `proofkit/schemas/`
3. [ ] Implement config system in `proofkit/utils/config.py`
4. [ ] Implement logger in `proofkit/utils/logger.py`
5. [ ] Implement exceptions in `proofkit/utils/exceptions.py`
6. [ ] Implement basic CLI in `proofkit/cli/main.py`
7. [ ] Implement runner skeleton in `proofkit/core/runner.py`
8. [ ] Create `pyproject.toml` with all dependencies
9. [ ] Create `.env.example`
10. [ ] Write tests for schemas and config
