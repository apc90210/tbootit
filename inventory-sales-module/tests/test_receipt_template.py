from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app

client = TestClient(app)

@patch("app.routers.sales.core_client", new_callable=AsyncMock)
def test_sale_receipt_page(mock_core):
    mock_core.get_sale.return_value = {
        "id": 99,
        "total_amount": 1000,
        "payment_method": "cash",
        "warranty_enabled": True,
        "warranty_days": 30,
        "items": [
            {"title": "Prod", "quantity": 1, "price": 1000, "product_id": 1}
        ]
    }
    mock_core.get_organization_settings.return_value = {
        "organization_name": "Test Org"
    }
    
    response = client.get("/sales/99/receipt")
    assert response.status_code == 200
    html = response.text
    assert "Товарный чек № 99" in html
    assert "Test Org" in html
    assert "Гарантийные условия" in html
    assert "30 дней" in html
    assert "window.print()" in html
