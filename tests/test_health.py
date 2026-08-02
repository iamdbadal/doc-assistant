import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.api.app.main import health_check


@pytest.mark.anyio
async def test_health_check_returns_expected_payload() -> None:
    response = await health_check()

    assert response["status"] == "ok"
    assert "project" in response
    assert response["project"]
