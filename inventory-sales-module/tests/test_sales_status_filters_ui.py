from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, AsyncMock

client = TestClient(app)

def test_sales_list_status_filter():
    mock_sales = {
        "items": [
            {"id": 1, "total_amount": 1000.0, "payment_method": "cash", "status": "canceled", "created_at": "2026-07-22T10:00:00"}
        ],
        "total": 1,
        "limit": 50,
        "offset": 0
    }

    with patch("app.core_client.core_client.get_sales", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_sales
        response = client.get("/sales?status=canceled")
        assert response.status_code == 200
        assert "Отмененные" in response.text or "Отменена" in response.text
        mock_get.assert_called_once_with({"limit": 50, "offset": 0, "status": "canceled"})
