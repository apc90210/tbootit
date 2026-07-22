from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, AsyncMock

client = TestClient(app)

def test_sale_reissue_form_get():
    mock_sale = {
        "id": 10,
        "total_amount": 1500.0,
        "payment_method": "cash",
        "status": "canceled",
        "items": [{"product_id": 1, "title": "Товар 1", "price": 1500.0, "quantity": 1}]
    }

    with patch("app.core_client.core_client.get_sale", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_sale
        response = client.get("/sales/10/reissue")
        assert response.status_code == 200
        assert "Повторное оформление продажи #10" in response.text

def test_sale_reissue_completed_blocked():
    mock_sale = {
        "id": 10,
        "total_amount": 1500.0,
        "payment_method": "cash",
        "status": "completed",
        "items": []
    }

    with patch("app.core_client.core_client.get_sale", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_sale
        response = client.get("/sales/10/reissue")
        assert response.status_code == 200
        assert "Повторно оформить можно только отменённую продажу" in response.text

def test_sale_reissue_post_success():
    form_data = {
        "reason": "Замена товара",
        "payment_method": "card",
        "item_product_id_1": "1",
        "item_title_1": "Товар 1",
        "item_price_1": "1500.0",
        "item_quantity_1": "1"
    }

    with patch("app.core_client.core_client.reissue_sale", new_callable=AsyncMock) as mock_reissue:
        mock_reissue.return_value = {"id": 20, "status": "reissued", "source_sale_id": 10}
        response = client.post("/sales/10/reissue", data=form_data, follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/sales/20"
        mock_reissue.assert_called_once()
