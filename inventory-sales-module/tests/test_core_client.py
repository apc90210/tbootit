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

@pytest.mark.asyncio
async def test_owner_reported_core_api_error_reproduced_and_fixed(respx_mock):
    """
    Test that get_products requests /api/products/ (with trailing slash)
    to prevent 307 Temporary Redirects from FastAPI which httpx does not follow,
    resulting in the 'Ошибка Core API' on the products page.
    """
    client = CoreClient()
    # Mock exactly with trailing slash
    mock_route = respx_mock.get(f"{client.base_url}/api/products/").mock(
        return_value=httpx.Response(200, json={"items": [], "total": 0, "limit": 50, "offset": 0})
    )
    
    result = await client.get_products({"limit": 50, "offset": 0})
    
    assert mock_route.called
    assert "error" not in result
    assert result["total"] == 0
