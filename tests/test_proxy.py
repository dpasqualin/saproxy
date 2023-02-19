import pytest
from aiohttp.test_utils import TestClient

from app.main import init_app


@pytest.fixture
async def client(aiohttp_client) -> TestClient:
    """Return fixture to simplify client calls."""
    app = await init_app()
    return await aiohttp_client(app)


async def test_proxy_handler(client: TestClient) -> None:
    """Test proxy handler."""
    resp = await client.post("/anything")
    assert resp.status == 200
    data = await resp.json()
    assert "x-my-jwt" in data["headers"]

    # Call with parameters work
    resp = await client.post("/anything?a=1&b=2")
    assert resp.status == 200
    data = await resp.json()
    assert data["args"] == {"a": "1", "b": "2"}


async def test_status_handler(client: TestClient, mocker) -> None:
    """Test status endpoint handler."""
    resp = await client.get("/status")
    assert resp.status == 200
    data = await resp.json()
    assert data["request_count"] == 0

    # Statistics should reflect the call to the proxy. We don't need to actual call
    # upstream here so we are mocking it.
    mocker.patch("app.main.call_upstream", return_value=(200, "application/json", b""))
    resp = await client.post("/anything?a=1&b=2")
    assert resp.status == 200

    resp = await client.get("/status")
    assert resp.status == 200
    data = await resp.json()
    assert data["request_count"] == 1
    assert data["uptime"] > 0
