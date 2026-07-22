from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, AsyncMock

client = TestClient(app)

def test_sale_cancel_form_get():
    mock_sale = {
        "id": 10,
        "total_amount": 1500.0,
        "payment_method": "cash",
        "status": "completed",
        "items": [{"product_id": 1, "title": "Товар 1", "price": 1500.0, "quantity": 1}]
    }

    with patch("app.core_client.core_client.get_sale", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_sale
        response = client.get("/sales/10/cancel")
        assert response.status_code == 200
        assert "Отмена продажи #10" in response.text
        assert "Подтверждение отмены продажи" in response.text

def test_sale_cancel_post_success():
    with patch("app.core_client.core_client.cancel_sale", new_callable=AsyncMock) as mock_cancel:
        mock_cancel.return_value = {"id": 10, "status": "canceled", "cancel_reason": "Ошибка в чеке"}
        response = client.post("/sales/10/cancel", data={"reason": "Ошибка в чеке", "canceled_by": "Администратор"}, follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/sales/10"
        mock_cancel.assert_called_once_with(10, "Ошибка в чеке", "Администратор")

def test_sale_cancel_already_canceled_blocked():
    mock_sale = {
        "id": 10,
        "total_amount": 1500.0,
        "payment_method": "cash",
        "status": "canceled",
        "items": []
    }

    with patch("app.core_client.core_client.get_sale", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_sale
        response = client.get("/sales/10/cancel")
        assert response.status_code == 200
        assert "не может быть отменена" in response.text
