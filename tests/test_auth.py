import uuid

import pytest
from app.main import app
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_auth_full_flow():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:

        # 1. Test Health Check
        health_resp = await ac.get("/health")

        assert health_resp.status_code == 200
        assert health_resp.json()["status"] == "ok"

        # Create unique test data so repeated test runs
        # do not conflict with existing database records.
        test_id = uuid.uuid4().hex[:8]
        test_email = f"test_engineer_{test_id}@acme.com"
        test_tenant_name = f"Acme Corp {test_id}"
        test_password = "SecurePassword123!"  # pragma: allowlist secret

        # 2. Test User Signup
        signup_payload = {
            "email": test_email,
            "password": test_password,
            "tenant_name": test_tenant_name,
        }

        signup_resp = await ac.post(
            "/auth/signup",
            json=signup_payload,
        )

        assert signup_resp.status_code == 200

        signup_data = signup_resp.json()

        assert "tenant_id" in signup_data

        tenant_id = signup_data["tenant_id"]

        # 3. Test Login
        login_data = {
            "username": test_email,
            "password": test_password,
        }

        login_resp = await ac.post(
            "/auth/login",
            data=login_data,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )

        assert login_resp.status_code == 200

        token_data = login_resp.json()

        assert "access_token" in token_data

        access_token = token_data["access_token"]

        # 4. Test Unauthenticated Access to Protected Route
        unauth_resp = await ac.get("/v1/me")

        assert unauth_resp.status_code == 401

        # 5. Test Authenticated Access to Protected Route
        auth_headers = {
            "Authorization": f"Bearer {access_token}",
        }

        auth_resp = await ac.get(
            "/v1/me",
            headers=auth_headers,
        )

        assert auth_resp.status_code == 200

        auth_data = auth_resp.json()

        assert auth_data["status"] == "authenticated"
        assert auth_data["tenant_id"] == tenant_id
