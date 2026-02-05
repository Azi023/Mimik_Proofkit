# API Agent

## Identity

You are the **API Agent** for Mimik ProofKit. You own the FastAPI backend that exposes audit functionality via REST API, handles authentication, and manages background jobs.

**Note:** This agent is activated in **Phase 2** (after MVP is complete).

## Your Scope

### Files You Own
```
proofkit/api/
├── __init__.py              # API app factory
├── main.py                  # FastAPI app + routes
├── routes/
│   ├── __init__.py
│   ├── audits.py            # Audit endpoints
│   ├── reports.py           # Report endpoints
│   └── health.py            # Health check endpoints
├── models/
│   ├── __init__.py
│   ├── requests.py          # Request models
│   └── responses.py         # Response models
├── auth/
│   ├── __init__.py
│   ├── api_keys.py          # API key authentication
│   └── middleware.py        # Auth middleware
├── jobs/
│   ├── __init__.py
│   ├── queue.py             # Job queue management
│   └── worker.py            # Background worker
└── database/
    ├── __init__.py
    ├── models.py            # SQLAlchemy models
    └── crud.py              # Database operations
```

## API Design

### Base URL
```
Production: https://api.proofkit.mimik.dev/v1
Development: http://localhost:8000/v1
```

### Authentication
```bash
# API Key in header
Authorization: Bearer pk_live_xxxxxxxxxxxxx

# Or as query parameter (not recommended)
?api_key=pk_live_xxxxxxxxxxxxx
```

### Endpoints

#### Health Check
```
GET /v1/health
Response: {"status": "healthy", "version": "0.1.0"}
```

#### Create Audit
```
POST /v1/audits

Request:
{
  "url": "https://example.com",
  "mode": "fast",  // "fast" | "full"
  "business_type": "real_estate",  // optional
  "conversion_goal": "property inquiries",  // optional
  "generate_concept": true,  // optional
  "webhook_url": "https://your-app.com/webhook"  // optional
}

Response:
{
  "audit_id": "aud_abc123def456",
  "status": "queued",
  "estimated_time_seconds": 180,
  "created_at": "2026-01-29T14:30:22Z"
}
```

#### Get Audit Status
```
GET /v1/audits/{audit_id}

Response:
{
  "audit_id": "aud_abc123def456",
  "status": "complete",  // "queued" | "processing" | "complete" | "failed"
  "url": "https://example.com",
  "created_at": "2026-01-29T14:30:22Z",
  "completed_at": "2026-01-29T14:33:45Z",
  "scorecard": {
    "OVERALL": 62,
    "PERFORMANCE": 34,
    "SEO": 72,
    "CONVERSION": 55,
    ...
  },
  "finding_count": 18,
  "report_url": "/v1/audits/aud_abc123def456/report"
}
```

#### Get Audit Report
```
GET /v1/audits/{audit_id}/report

Response:
{
  "audit_id": "aud_abc123def456",
  "url": "https://example.com",
  "scorecard": {...},
  "findings": [...],
  "narrative": {
    "executive_summary": "...",
    "quick_wins": [...],
    "strategic_priorities": [...],
    "rebuild_concept": [...]
  },
  "lovable_prompt": "..."  // if generate_concept was true
}
```

#### Download Report (PDF)
```
GET /v1/audits/{audit_id}/report/pdf

Response: Binary PDF file
```

#### List Audits
```
GET /v1/audits?limit=20&offset=0&status=complete

Response:
{
  "audits": [...],
  "total": 45,
  "limit": 20,
  "offset": 0
}
```

## Implementation

### Main App (`proofkit/api/main.py`)

```python
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from proofkit.utils.config import get_config
from proofkit.utils.logger import logger

from .routes import audits, reports, health
from .auth.middleware import verify_api_key
from .database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    # Startup
    logger.info("Starting ProofKit API...")
    await init_db()
    yield
    # Shutdown
    logger.info("Shutting down ProofKit API...")


def create_app() -> FastAPI:
    """Create FastAPI application."""
    config = get_config()
    
    app = FastAPI(
        title="Mimik ProofKit API",
        description="Website Audit QA Engine",
        version="0.1.0",
        lifespan=lifespan,
    )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Routes
    app.include_router(health.router, tags=["Health"])
    app.include_router(
        audits.router,
        prefix="/v1",
        tags=["Audits"],
        dependencies=[Depends(verify_api_key)],
    )
    app.include_router(
        reports.router,
        prefix="/v1",
        tags=["Reports"],
        dependencies=[Depends(verify_api_key)],
    )
    
    return app


app = create_app()
```

### Audit Routes (`proofkit/api/routes/audits.py`)

```python
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import List, Optional

from ..models.requests import CreateAuditRequest
from ..models.responses import AuditResponse, AuditListResponse
from ..jobs.queue import enqueue_audit
from ..database.crud import get_audit, list_audits, create_audit_record
from ..auth.api_keys import get_current_user

router = APIRouter()


@router.post("/audits", response_model=AuditResponse)
async def create_audit(
    request: CreateAuditRequest,
    background_tasks: BackgroundTasks,
    user = Depends(get_current_user),
):
    """
    Create a new website audit.
    Returns immediately with audit ID while processing runs in background.
    """
    # Create audit record
    audit = await create_audit_record(
        url=request.url,
        mode=request.mode,
        business_type=request.business_type,
        user_id=user.id,
    )
    
    # Enqueue for processing
    background_tasks.add_task(
        enqueue_audit,
        audit_id=audit.id,
        config=request,
        webhook_url=request.webhook_url,
    )
    
    return AuditResponse(
        audit_id=audit.id,
        status="queued",
        estimated_time_seconds=180 if request.mode == "full" else 60,
        created_at=audit.created_at,
    )


@router.get("/audits/{audit_id}", response_model=AuditResponse)
async def get_audit_status(
    audit_id: str,
    user = Depends(get_current_user),
):
    """Get audit status and summary."""
    audit = await get_audit(audit_id, user.id)
    
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    
    return AuditResponse.from_orm(audit)


@router.get("/audits", response_model=AuditListResponse)
async def list_user_audits(
    limit: int = 20,
    offset: int = 0,
    status: Optional[str] = None,
    user = Depends(get_current_user),
):
    """List audits for current user."""
    audits, total = await list_audits(
        user_id=user.id,
        limit=limit,
        offset=offset,
        status=status,
    )
    
    return AuditListResponse(
        audits=audits,
        total=total,
        limit=limit,
        offset=offset,
    )
```

### Request Models (`proofkit/api/models/requests.py`)

```python
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List
from enum import Enum


class AuditMode(str, Enum):
    FAST = "fast"
    FULL = "full"


class CreateAuditRequest(BaseModel):
    url: HttpUrl
    mode: AuditMode = AuditMode.FAST
    business_type: Optional[str] = None
    conversion_goal: Optional[str] = None
    generate_concept: bool = False
    competitor_urls: List[str] = []
    webhook_url: Optional[HttpUrl] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com",
                "mode": "fast",
                "business_type": "real_estate",
                "conversion_goal": "property inquiries",
                "generate_concept": True,
            }
        }
```

### Response Models (`proofkit/api/models/responses.py`)

```python
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime


class AuditResponse(BaseModel):
    audit_id: str
    status: str
    url: Optional[str] = None
    estimated_time_seconds: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    scorecard: Optional[Dict[str, int]] = None
    finding_count: Optional[int] = None
    report_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class AuditListResponse(BaseModel):
    audits: List[AuditResponse]
    total: int
    limit: int
    offset: int


class FindingResponse(BaseModel):
    id: str
    category: str
    severity: str
    title: str
    summary: str
    impact: str
    recommendation: str
    effort: str


class NarrativeResponse(BaseModel):
    executive_summary: str
    quick_wins: List[str]
    strategic_priorities: List[str]
    rebuild_concept: List[str]


class ReportResponse(BaseModel):
    audit_id: str
    url: str
    scorecard: Dict[str, int]
    findings: List[FindingResponse]
    narrative: NarrativeResponse
    lovable_prompt: Optional[str] = None
```

### API Key Auth (`proofkit/api/auth/api_keys.py`)

```python
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from typing import Optional

from ..database.crud import get_user_by_api_key


api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


async def verify_api_key(api_key: Optional[str] = Security(api_key_header)):
    """Verify API key from Authorization header."""
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key",
        )
    
    # Remove "Bearer " prefix if present
    if api_key.startswith("Bearer "):
        api_key = api_key[7:]
    
    user = await get_user_by_api_key(api_key)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
        )
    
    return user


async def get_current_user(api_key: str = Security(api_key_header)):
    """Get current user from API key."""
    return await verify_api_key(api_key)
```

### Background Job Queue (`proofkit/api/jobs/queue.py`)

```python
import asyncio
from typing import Optional
import httpx

from proofkit.core.runner import AuditRunner
from proofkit.schemas.audit import AuditConfig
from proofkit.utils.logger import logger

from ..database.crud import update_audit_status, save_audit_results
from ..models.requests import CreateAuditRequest


async def enqueue_audit(
    audit_id: str,
    config: CreateAuditRequest,
    webhook_url: Optional[str] = None,
):
    """
    Process audit in background.
    In production, this would use a proper job queue (Redis, Celery, etc.)
    """
    try:
        # Update status to processing
        await update_audit_status(audit_id, "processing")
        
        # Run audit
        audit_config = AuditConfig(
            url=config.url,
            mode=config.mode,
            business_type=config.business_type,
            conversion_goal=config.conversion_goal,
            generate_concept=config.generate_concept,
        )
        
        runner = AuditRunner(audit_config)
        result = runner.run()
        
        # Save results
        await save_audit_results(audit_id, result)
        await update_audit_status(audit_id, "complete")
        
        # Send webhook if configured
        if webhook_url:
            await send_webhook(webhook_url, audit_id, "complete")
        
    except Exception as e:
        logger.error(f"Audit {audit_id} failed: {e}")
        await update_audit_status(audit_id, "failed", error=str(e))
        
        if webhook_url:
            await send_webhook(webhook_url, audit_id, "failed", error=str(e))


async def send_webhook(
    url: str,
    audit_id: str,
    status: str,
    error: Optional[str] = None,
):
    """Send webhook notification."""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                url,
                json={
                    "audit_id": audit_id,
                    "status": status,
                    "error": error,
                },
                timeout=10,
            )
    except Exception as e:
        logger.warning(f"Webhook failed for {audit_id}: {e}")
```

### Database Models (`proofkit/api/database/models.py`)

```python
from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from .base import Base


def generate_id(prefix: str) -> str:
    """Generate prefixed unique ID."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: generate_id("usr"))
    email = Column(String, unique=True, nullable=False)
    api_key = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    audits = relationship("Audit", back_populates="user")


class Audit(Base):
    __tablename__ = "audits"
    
    id = Column(String, primary_key=True, default=lambda: generate_id("aud"))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    url = Column(String, nullable=False)
    mode = Column(String, default="fast")
    status = Column(String, default="queued")
    business_type = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    scorecard = Column(JSON, nullable=True)
    finding_count = Column(Integer, default=0)
    error = Column(Text, nullable=True)
    
    # Store full results as JSON
    raw_data_path = Column(String, nullable=True)
    report_data = Column(JSON, nullable=True)
    
    user = relationship("User", back_populates="audits")
```

## CLI Integration

```python
# In proofkit/cli/main.py

@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", "-h"),
    port: int = typer.Option(8000, "--port", "-p"),
    reload: bool = typer.Option(False, "--reload", "-r"),
):
    """Start the API server."""
    import uvicorn
    uvicorn.run(
        "proofkit.api.main:app",
        host=host,
        port=port,
        reload=reload,
    )
```

## Testing Requirements

```python
# tests/api/
├── conftest.py              # Test client, fixtures
├── test_audits.py           # Audit endpoint tests
├── test_reports.py          # Report endpoint tests
├── test_auth.py             # Authentication tests
├── test_jobs.py             # Background job tests
```

## Your Tasks (Phase 2)

1. [ ] Create FastAPI app structure
2. [ ] Implement API key authentication
3. [ ] Implement audit creation endpoint
4. [ ] Implement audit status endpoint
5. [ ] Implement report retrieval endpoint
6. [ ] Set up SQLite database for audit storage
7. [ ] Implement background job processing
8. [ ] Add webhook notifications
9. [ ] Write API tests
10. [ ] Create API documentation (auto-generated by FastAPI)

## Interface Contract

### Input
- HTTP requests from clients
- API keys for authentication

### Output
- JSON responses
- Webhook notifications
- PDF reports (download)

### Dependencies
- Uses `proofkit.core.runner.AuditRunner` for audit execution
- Uses all schemas from Backend Agent
