import pytest
from app.core_client import CoreClient
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_get_product_filter_options_passes_params():
    client = CoreClient()
    
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"categories": [], "brands": []}
    
    with patch("httpx.AsyncClient.get", return_value=mock_response) as mock_get:
        # Test without params
        await client.get_product_filter_options()
        mock_get.assert_called_with(f"{client.base_url}/api/products/filter-options", params={}, timeout=10.0)
        
        # Test with params
        params = {"category_id": 1, "brand": "Apple"}
        await client.get_product_filter_options(params)
        mock_get.assert_called_with(f"{client.base_url}/api/products/filter-options", params=params, timeout=10.0)
