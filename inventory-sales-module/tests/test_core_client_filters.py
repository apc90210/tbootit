import pytest
from app.core_client import CoreClient
import httpx

@pytest.mark.asyncio
async def test_get_product_filter_options(respx_mock):
    client = CoreClient()
    mock_response = {
        "brands": [{"value": "Lenovo", "count": 1}],
        "models": [{"value": "T480", "count": 1}],
        "statuses": [{"value": "in_stock", "label": "В наличии", "count": 1}],
        "storage_locations": [],
        "categories": [],
        "avito_ready": [],
        "site_ready": []
    }
    mock_route = respx_mock.get(f"{client.base_url}/api/products/filter-options").mock(
        return_value=httpx.Response(200, json=mock_response)
    )
    
    result = await client.get_product_filter_options()
    
    assert mock_route.called
    assert "error" not in result
    assert result["brands"][0]["value"] == "Lenovo"
