from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app

client = TestClient(app)

@patch("app.routers.sales.core_client", new_callable=AsyncMock)
def test_sales_list_page(mock_core):
    mock_core.get_sales.return_value = {
        "total": 1,
        "items": [
            {
                "id": 1,
                "created_at": "2026-07-02T10:00:00Z",
                "total_amount": 500,
                "payment_method": "cash",
                "status": "completed",
                "items": [{"id": 1}]
            }
        ]
    }
    
    response = client.get("/sales")
    assert response.status_code == 200
    assert "500" in response.text
    assert "Товарный чек" in response.text
    assert "Открыть" in response.text
