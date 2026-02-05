"""Tests for audit endpoints."""

import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock


class TestCreateAudit:
    @pytest.mark.asyncio
    async def test_create_audit_minimal(self, client: AsyncClient, auth_headers):
        """Test creating audit with minimal parameters."""
        with patch("proofkit.api.routes.audits.enqueue_audit", new_callable=AsyncMock):
            response = await client.post(
                "/v1/audits",
                headers=auth_headers,
                json={"url": "https://example.com"},
            )

        assert response.status_code == 201
        data = response.json()
        assert "audit_id" in data
        assert data["status"] == "queued"
        assert data["url"] == "https://example.com/"
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_audit_full(self, client: AsyncClient, auth_headers):
        """Test creating audit with all parameters."""
        with patch("proofkit.api.routes.audits.enqueue_audit", new_callable=AsyncMock):
            response = await client.post(
                "/v1/audits",
                headers=auth_headers,
                json={
                    "url": "https://example.com",
                    "mode": "full",
                    "business_type": "real_estate",
                    "conversion_goal": "property inquiries",
                    "generate_concept": True,
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "queued"
        assert data["estimated_time_seconds"] == 180  # Full mode

    @pytest.mark.asyncio
    async def test_create_audit_invalid_url(self, client: AsyncClient, auth_headers):
        """Test creating audit with invalid URL."""
        response = await client.post(
            "/v1/audits",
            headers=auth_headers,
            json={"url": "not-a-valid-url"},
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_create_audit_fast_mode_estimate(self, client: AsyncClient, auth_headers):
        """Test that fast mode returns correct time estimate."""
        with patch("proofkit.api.routes.audits.enqueue_audit", new_callable=AsyncMock):
            response = await client.post(
                "/v1/audits",
                headers=auth_headers,
                json={"url": "https://example.com", "mode": "fast"},
            )

        assert response.status_code == 201
        assert response.json()["estimated_time_seconds"] == 60


class TestGetAudit:
    @pytest.mark.asyncio
    async def test_get_audit_exists(self, client: AsyncClient, auth_headers, test_audit):
        """Test getting an existing audit."""
        response = await client.get(
            f"/v1/audits/{test_audit.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["audit_id"] == test_audit.id
        assert data["status"] == "complete"
        assert "scorecard" in data

    @pytest.mark.asyncio
    async def test_get_audit_not_found(self, client: AsyncClient, auth_headers):
        """Test getting a non-existent audit."""
        response = await client.get(
            "/v1/audits/aud_nonexistent",
            headers=auth_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_audit_wrong_user(self, client: AsyncClient, test_audit):
        """Test that users can't access other users' audits."""
        from proofkit.api.auth.api_keys import generate_api_key
        from proofkit.api.database.crud import create_user

        # Create another user
        other_user = await create_user(
            email="other@example.com",
            api_key=generate_api_key("pk_test"),
        )

        response = await client.get(
            f"/v1/audits/{test_audit.id}",
            headers={"Authorization": f"Bearer {other_user.api_key}"},
        )

        assert response.status_code == 404  # Not found (not accessible)


class TestListAudits:
    @pytest.mark.asyncio
    async def test_list_audits_empty(self, client: AsyncClient, auth_headers):
        """Test listing audits when none exist."""
        response = await client.get("/v1/audits", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["audits"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_audits_with_data(self, client: AsyncClient, auth_headers, test_audit):
        """Test listing audits with existing data."""
        response = await client.get("/v1/audits", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["audits"]) == 1
        assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_list_audits_pagination(self, client: AsyncClient, auth_headers):
        """Test audit listing pagination."""
        response = await client.get(
            "/v1/audits",
            headers=auth_headers,
            params={"limit": 10, "offset": 0},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 10
        assert data["offset"] == 0

    @pytest.mark.asyncio
    async def test_list_audits_filter_by_status(self, client: AsyncClient, auth_headers, test_audit):
        """Test filtering audits by status."""
        response = await client.get(
            "/v1/audits",
            headers=auth_headers,
            params={"status": "complete"},
        )

        assert response.status_code == 200
        data = response.json()
        assert all(a["status"] == "complete" for a in data["audits"])


class TestDeleteAudit:
    @pytest.mark.asyncio
    async def test_delete_audit(self, client: AsyncClient, auth_headers, test_audit):
        """Test deleting an audit."""
        response = await client.delete(
            f"/v1/audits/{test_audit.id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        # Verify it's deleted
        response = await client.get(
            f"/v1/audits/{test_audit.id}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_audit_not_found(self, client: AsyncClient, auth_headers):
        """Test deleting a non-existent audit."""
        response = await client.delete(
            "/v1/audits/aud_nonexistent",
            headers=auth_headers,
        )

        assert response.status_code == 404
