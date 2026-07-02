"""Tests for CoreClient sales methods."""
import pytest
from app.core_client import CoreClient
import httpx


@pytest.mark.asyncio
async def test_create_sale_success(respx_mock):
    client = CoreClient()
    mock_sale = {
        "id": 1,
        "customer_id": None,
        "total_amount": 25000.0,
        "payment_method": "cash",
        "comment": None,
        "status": "completed",
        "created_at": "2026-07-02T10:00:00",
    }
    respx_mock.post(f"{client.base_url}/api/sales/").mock(
        return_value=httpx.Response(200, json=mock_sale)
    )
    result = await client.create_sale(
        product_id=1, price=25000.0, payment_method="cash", notes=None
    )
    assert result["id"] == 1
    assert result["status"] == "completed"
    assert result["total_amount"] == 25000.0


@pytest.mark.asyncio
async def test_create_sale_error(respx_mock):
    client = CoreClient()
    respx_mock.post(f"{client.base_url}/api/sales/").mock(
        return_value=httpx.Response(
            400, json={"detail": "Cannot sell product 1 in status 'sold'"}
        )
    )
    result = await client.create_sale(
        product_id=1, price=25000.0, payment_method="cash"
    )
    assert result["error"] is True
    assert result["status_code"] == 400
    assert "Cannot sell" in result["detail"]


@pytest.mark.asyncio
async def test_get_sale_success(respx_mock):
    client = CoreClient()
    mock_sale = {
        "id": 1,
        "total_amount": 25000.0,
        "payment_method": "cash",
        "status": "completed",
    }
    respx_mock.get(f"{client.base_url}/api/sales/1").mock(
        return_value=httpx.Response(200, json=mock_sale)
    )
    result = await client.get_sale(1)
    assert result["id"] == 1


@pytest.mark.asyncio
async def test_get_sale_not_found(respx_mock):
    client = CoreClient()
    respx_mock.get(f"{client.base_url}/api/sales/999").mock(
        return_value=httpx.Response(404, json={"detail": "Sale not found"})
    )
    result = await client.get_sale(999)
    assert result["error"] == "Not Found"
    assert result["status_code"] == 404


@pytest.mark.asyncio
async def test_get_sales_success(respx_mock):
    client = CoreClient()
    mock_data = {
        "items": [
            {"id": 1, "total_amount": 25000.0, "payment_method": "cash", "status": "completed"}
        ],
        "total": 1,
        "limit": 50,
        "offset": 0,
    }
    respx_mock.get(f"{client.base_url}/api/sales/").mock(
        return_value=httpx.Response(200, json=mock_data)
    )
    result = await client.get_sales()
    assert result["total"] == 1
    assert len(result["items"]) == 1


@pytest.mark.asyncio
async def test_get_sales_today_success(respx_mock):
    client = CoreClient()
    mock_data = {
        "items": [],
        "total": 0,
        "limit": 1000,
        "offset": 0,
    }
    respx_mock.get(f"{client.base_url}/api/sales/today").mock(
        return_value=httpx.Response(200, json=mock_data)
    )
    result = await client.get_sales_today()
    assert result["total"] == 0
