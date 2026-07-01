import pytest
from app.core_client import CoreClient
import httpx

@pytest.mark.asyncio
async def test_core_client_health_ok(respx_mock):
    client = CoreClient()
    respx_mock.get(f"{client.base_url}/health").mock(return_value=httpx.Response(200, json={"status": "ok"}))
    
    result = await client.health()
    assert result["core_available"] is True
    assert result["core_response"]["status"] == "ok"

@pytest.mark.asyncio
async def test_core_client_health_fail(respx_mock):
    client = CoreClient()
    respx_mock.get(f"{client.base_url}/health").mock(return_value=httpx.Response(500))
    
    result = await client.health()
    assert result["core_available"] is False
    assert result["status_code"] == 500
