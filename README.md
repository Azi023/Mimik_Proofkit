# Mimik ProofKit

**AI-Powered Website Audit & QA Engineering Tool**

ProofKit is a comprehensive website auditing tool that analyzes websites for UX, SEO, performance, security, and conversion optimization issues. It generates detailed reports with AI-powered narratives and actionable recommendations.

## Features

- **Website Auditing** - Automated analysis of UX, SEO, performance, security, and conversion
- **AI-Powered Narratives** - Executive summaries, quick wins, and strategic priorities using OpenAI/Anthropic
- **Multi-Model Support** - Choose from GPT-4o, GPT-4-turbo, Claude, o1, and more
- **Intelligent QA** - Automatic feature discovery and Playwright test generation
- **Codebase Analysis** - Scan codebases to understand structure and generate tests
- **Report Generation** - Auto-generate Pencil.dev and Figma-compatible reports
- **REST API** - Full API with authentication for integrations
- **Web Dashboard** - Next.js frontend for running audits visually

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/your-repo/Mimik_Proofkit.git
cd Mimik_Proofkit

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or: .venv\Scripts\activate  # Windows

# Install dependencies
pip install -e .

# Install Playwright browsers
playwright install chromium
```

### Configuration

Create a `.env` file (or copy from `.env.example`):

```bash
# AI Provider (openai or anthropic)
AI_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o  # Options: gpt-4o-mini, gpt-4o, gpt-4-turbo, o1-mini

# Or use Anthropic
# AI_PROVIDER=anthropic
# ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### Run Your First Audit

```bash
# CLI audit
proofkit run --url https://example.com --mode fast

# Or using Python module
python -m proofkit run --url https://example.com
```

## CLI Commands

### Website Auditing

```bash
# Fast audit (homepage only)
proofkit run --url https://example.com --mode fast

# Full audit (crawl entire site)
proofkit run --url https://example.com --mode full

# With business type context
proofkit run --url https://example.com --mode fast --business-type real_estate

# Generate Lovable.dev concept prompts
proofkit run --url https://example.com --concept
```

### AI Configuration

```bash
# Test AI connection
proofkit test-ai

# List available AI models
proofkit models

# Check Lighthouse requirements
proofkit check-lighthouse
```

### Feature Discovery & Test Generation

```bash
# Discover interactive features and generate Playwright tests
proofkit discover-features https://example.com

# With custom output directory
proofkit discover-features https://example.com --output ./my-tests
```

### Codebase Analysis

```bash
# Analyze a codebase
proofkit analyze-codebase ./my-project

# With test generation
proofkit analyze-codebase ./my-project --tests

# Filter by file type
proofkit analyze-codebase ./my-project --include "*.py,*.ts"
```

### Report Export

```bash
# Export to Pencil.dev format
proofkit export-pencil --run-dir ./runs/run_20260206_123456

# Reports are also auto-generated after each audit in:
# - runs/{run_id}/pencil/  (Pencil.dev prompts)
# - runs/{run_id}/figma/   (Figma export files)
```

### API Server

```bash
# Start the API server
proofkit serve

# With custom port
proofkit serve --port 8080 --reload
```

## Available AI Models

### OpenAI Models

| Model | Use Case | Cost |
|-------|----------|------|
| `gpt-4o-mini` | Fast, simple tasks | $0.15/1M input |
| `gpt-4o` | Balanced (default) | $2.50/1M input |
| `gpt-4-turbo` | Complex analysis | $10/1M input |
| `o1-mini` | Deep reasoning | $3/1M input |
| `o1-preview` | Advanced reasoning | $15/1M input |

### Anthropic Models

| Model | Use Case | Cost |
|-------|----------|------|
| `claude-3-haiku` | Fast, simple tasks | $0.25/1M input |
| `claude-sonnet-4` | Balanced (default) | $3/1M input |
| `claude-opus-4` | Complex analysis | $15/1M input |

## Output Structure

After running an audit, you'll find:

```
runs/run_YYYYMMDD_HHMMSS/
├── raw/                    # Collected data
│   ├── screenshots/        # Desktop & mobile screenshots
│   ├── raw_data.json       # All collected data
│   ├── snapshot.json       # Page snapshots
│   └── http_probe.json     # HTTP analysis
├── out/                    # Analysis results
│   ├── report.json         # Full JSON report
│   ├── findings.json       # All findings
│   └── narrative.md        # AI-generated narrative
├── pencil/                 # Pencil.dev prompts
│   ├── pencil_full_report.txt
│   └── pencil_*.txt        # Section prompts
└── figma/                  # Figma exports
    ├── figma_report_data.json
    ├── figma_variables.json
    └── FIGMA_INSTRUCTIONS.md
```

## API Usage

### Start the Server

```bash
proofkit serve --port 8000
```

### API Endpoints

```bash
# Health check
curl http://localhost:8000/v1/health

# Create audit (requires API key)
curl -X POST http://localhost:8000/v1/audits \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "mode": "fast"}'

# Get audit status
curl http://localhost:8000/v1/audits/{audit_id} \
  -H "X-API-Key: your-api-key"
```

### API Documentation

Interactive API docs available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## MCP Integration (Claude Code)

ProofKit can be used as an MCP server for Claude Code:

```json
// mcp_config.json
{
  "mcpServers": {
    "proofkit": {
      "command": "python",
      "args": ["-m", "proofkit.mcp.server"],
      "cwd": "/path/to/Mimik_Proofkit",
      "env": {
        "PYTHONPATH": "/path/to/Mimik_Proofkit"
      }
    }
  }
}
```

Available MCP tools:
- `proofkit_audit` - Run a website audit
- `proofkit_discover_features` - Discover interactive features
- `proofkit_analyze` - Analyze collected data
- `proofkit_generate_report` - Generate formatted reports

## Frontend Dashboard

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Open http://localhost:3000
```

## Business Types

Supported business types for contextual analysis:

- `real_estate` - Property listings, virtual tours, inquiry forms
- `ecommerce` - Product catalogs, cart, checkout
- `saas` - Pricing pages, signup, demo requests
- `hospitality` - Booking, amenities, location
- `restaurant` - Menu, reservations, ordering
- `healthcare` - Appointments, provider profiles
- `agency` - Portfolio, services, contact

## Architecture

```
proofkit/
├── cli/              # Command-line interface
├── core/             # Audit orchestration
├── collector/        # Data collection (Playwright, Lighthouse, HTTP)
├── analyzer/         # Rule engine & scoring
├── narrator/         # AI narrative generation
├── intelligent_qa/   # Feature discovery & test generation
├── codebase_qa/      # Codebase analysis
├── report_builder/   # Pencil & Figma export
├── api/              # FastAPI REST API
├── mcp/              # MCP server for Claude Code
└── schemas/          # Pydantic data models
```

## Requirements

- Python 3.10+
- Node.js 18+ (for frontend)
- Chrome/Chromium (for Lighthouse)
- OpenAI or Anthropic API key

### Optional

- Lighthouse CLI: `npm install -g lighthouse`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

---

**Built by Mimik Creations**
