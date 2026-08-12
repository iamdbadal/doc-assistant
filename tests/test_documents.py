from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.api.auth import get_current_tenant
from app.db.models import get_db
from app.main import app
from httpx import ASGITransport, AsyncClient


# --- Mock Dependencies ---
async def override_get_current_tenant():
    """Bypasses JWT auth and returns a fake tenant ID for testing."""
    return "test_tenant_123"


async def override_get_db():
    """Mocks the DB session safely for both sync (add) and async (commit) methods."""
    mock_session = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.execute = AsyncMock()
    yield mock_session


# --- Local Fixtures ---
@pytest.fixture(autouse=True)
def manage_dependency_overrides():
    """Applies overrides for these tests and clears them so they don't leak to test_auth.py."""
    app.dependency_overrides[get_current_tenant] = override_get_current_tenant
    app.dependency_overrides[get_db] = override_get_db

    yield  # Run the test

    app.dependency_overrides.clear()  # Clean up afterward


@pytest.fixture
async def client():
    """Provides an async test client for the FastAPI app."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# --- Tests ---
@pytest.mark.asyncio
async def test_upload_init_validation(client: AsyncClient):
    # Test invalid file extension
    response = await client.post(
        "/v1/documents/upload",
        json={
            "filename": "malicious.exe",
            "content_type": "application/x-msdownload",
            "file_size": 1024,
        },
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


@pytest.mark.asyncio
@patch("app.services.storage.storage_service.generate_presigned_upload_url")
async def test_upload_init_success(mock_presigned, client: AsyncClient):
    # Mock the MinIO URL generation
    mock_presigned.return_value = "http://localhost:9000/documents/test_presigned_url"

    response = await client.post(
        "/v1/documents/upload",
        json={
            "filename": "test_doc.pdf",
            "content_type": "application/pdf",
            "file_size": 2048,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert "doc_id" in data
    assert data["upload_url"] == "http://localhost:9000/documents/test_presigned_url"
