"""Tests for authentication."""

import pytest
from httpx import AsyncClient


class TestAuthentication:
    @pytest.mark.asyncio
    async def test_missing_api_key(self, client: AsyncClient):
        """Test request without API key."""
        response = await client.get("/v1/audits")

        assert response.status_code == 401
        assert "Missing API key" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_invalid_api_key(self, client: AsyncClient):
        """Test request with invalid API key."""
        response = await client.get(
            "/v1/audits",
            headers={"Authorization": "Bearer invalid_key"},
        )

        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_valid_api_key_header(self, client: AsyncClient, auth_headers):
        """Test request with valid API key in header."""
        response = await client.get("/v1/audits", headers=auth_headers)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_valid_api_key_query(self, client: AsyncClient, test_user):
        """Test request with valid API key as query parameter."""
        response = await client.get(
            "/v1/audits",
            params={"api_key": test_user.api_key},
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_bearer_prefix_optional(self, client: AsyncClient, test_user):
        """Test that Bearer prefix is optional."""
        response = await client.get(
            "/v1/audits",
            headers={"Authorization": test_user.api_key},
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_x_api_key_header(self, client: AsyncClient, test_user):
        """Test request with valid API key in X-API-Key header."""
        response = await client.get(
            "/v1/audits",
            headers={"X-API-Key": test_user.api_key},
        )

        assert response.status_code == 200
