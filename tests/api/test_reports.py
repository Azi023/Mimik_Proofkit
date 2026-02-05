"""Tests for report endpoints."""

import pytest
from httpx import AsyncClient


class TestGetReport:
    @pytest.mark.asyncio
    async def test_get_report_complete_audit(self, client: AsyncClient, auth_headers, test_audit):
        """Test getting report for completed audit."""
        # First, add report data to the audit
        from proofkit.api.database.crud import get_audit
        from proofkit.api.database import get_db

        async for session in get_db():
            audit = await session.get(type(test_audit), test_audit.id)
            audit.report_data = {
                "scorecard": {"OVERALL": 75, "SEO": 80},
                "findings": [
                    {
                        "id": "SEO-001",
                        "category": "SEO",
                        "severity": "P1",
                        "title": "Test Finding",
                        "summary": "Test summary",
                        "impact": "Test impact",
                        "recommendation": "Test fix",
                        "effort": "S",
                    }
                ],
                "narrative": {
                    "executive_summary": "Test summary",
                    "quick_wins": ["Fix 1"],
                    "strategic_priorities": ["Priority 1"],
                    "category_insights": {"SEO": "Good"},
                },
            }
            await session.commit()
            break

        response = await client.get(
            f"/v1/audits/{test_audit.id}/report",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["audit_id"] == test_audit.id
        assert "scorecard" in data
        assert "findings" in data
        assert "narrative" in data

    @pytest.mark.asyncio
    async def test_get_report_incomplete_audit(self, client: AsyncClient, auth_headers, test_user):
        """Test getting report for incomplete audit."""
        from proofkit.api.database.crud import create_audit_record

        # Create a queued audit
        audit = await create_audit_record(
            url="https://example.com",
            mode="fast",
            user_id=test_user.id,
        )

        response = await client.get(
            f"/v1/audits/{audit.id}/report",
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "not complete" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_report_not_found(self, client: AsyncClient, auth_headers):
        """Test getting report for non-existent audit."""
        response = await client.get(
            "/v1/audits/aud_nonexistent/report",
            headers=auth_headers,
        )

        assert response.status_code == 404


class TestGetFindings:
    @pytest.mark.asyncio
    async def test_get_findings(self, client: AsyncClient, auth_headers, test_audit):
        """Test getting findings from audit."""
        # Add report data with findings
        from proofkit.api.database import get_db

        async for session in get_db():
            audit = await session.get(type(test_audit), test_audit.id)
            audit.report_data = {
                "findings": [
                    {"id": "SEO-001", "category": "SEO", "severity": "P1",
                     "title": "SEO Issue", "summary": "...", "impact": "...",
                     "recommendation": "...", "effort": "S"},
                    {"id": "PERF-001", "category": "PERFORMANCE", "severity": "P0",
                     "title": "Perf Issue", "summary": "...", "impact": "...",
                     "recommendation": "...", "effort": "M"},
                ],
            }
            await session.commit()
            break

        response = await client.get(
            f"/v1/audits/{test_audit.id}/findings",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["findings"]) == 2

    @pytest.mark.asyncio
    async def test_get_findings_filter_category(self, client: AsyncClient, auth_headers, test_audit):
        """Test filtering findings by category."""
        from proofkit.api.database import get_db

        async for session in get_db():
            audit = await session.get(type(test_audit), test_audit.id)
            audit.report_data = {
                "findings": [
                    {"id": "SEO-001", "category": "SEO", "severity": "P1",
                     "title": "SEO Issue", "summary": "...", "impact": "...",
                     "recommendation": "...", "effort": "S"},
                    {"id": "PERF-001", "category": "PERFORMANCE", "severity": "P0",
                     "title": "Perf Issue", "summary": "...", "impact": "...",
                     "recommendation": "...", "effort": "M"},
                ],
            }
            await session.commit()
            break

        response = await client.get(
            f"/v1/audits/{test_audit.id}/findings",
            headers=auth_headers,
            params={"category": "SEO"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["findings"][0]["category"] == "SEO"

    @pytest.mark.asyncio
    async def test_get_findings_filter_severity(self, client: AsyncClient, auth_headers, test_audit):
        """Test filtering findings by severity."""
        from proofkit.api.database import get_db

        async for session in get_db():
            audit = await session.get(type(test_audit), test_audit.id)
            audit.report_data = {
                "findings": [
                    {"id": "SEO-001", "category": "SEO", "severity": "P1",
                     "title": "SEO Issue", "summary": "...", "impact": "...",
                     "recommendation": "...", "effort": "S"},
                    {"id": "PERF-001", "category": "PERFORMANCE", "severity": "P0",
                     "title": "Perf Issue", "summary": "...", "impact": "...",
                     "recommendation": "...", "effort": "M"},
                ],
            }
            await session.commit()
            break

        response = await client.get(
            f"/v1/audits/{test_audit.id}/findings",
            headers=auth_headers,
            params={"severity": "P0"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["findings"][0]["severity"] == "P0"


class TestDownloadReport:
    @pytest.mark.asyncio
    async def test_download_json(self, client: AsyncClient, auth_headers, test_audit):
        """Test downloading report as JSON."""
        from proofkit.api.database import get_db

        async for session in get_db():
            audit = await session.get(type(test_audit), test_audit.id)
            audit.report_data = {"scorecard": {"OVERALL": 75}}
            await session.commit()
            break

        response = await client.get(
            f"/v1/audits/{test_audit.id}/report/json",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert "attachment" in response.headers.get("content-disposition", "")

    @pytest.mark.asyncio
    async def test_download_pdf_not_available(self, client: AsyncClient, auth_headers, test_audit):
        """Test that PDF returns 404 when not generated."""
        response = await client.get(
            f"/v1/audits/{test_audit.id}/report/pdf",
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert "PDF report not available" in response.json()["detail"]
