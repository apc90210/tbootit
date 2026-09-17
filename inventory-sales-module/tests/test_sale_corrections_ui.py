from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, AsyncMock

client = TestClient(app)

def test_sale_edit_form_get():
    mock_sale = {
        "id": 15,
        "total_amount": 5000.0,
        "payment_method": "cash",
        "status": "completed",
        "revision_count": 0,
        "items": [{"product_id": 1, "title": "Клавиатура", "price": 5000.0, "quantity": 1}]
    }

    with patch("app.core_client.core_client.get_sale", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_sale
        response = client.get("/sales/15/edit")
        assert response.status_code == 200
        assert "Редактирование продажи #15" in response.text
        assert "Клавиатура" in response.text
        assert "Способ оплаты" in response.text


def test_sale_edit_canceled_blocked():
    mock_sale = {
        "id": 15,
        "total_amount": 5000.0,
        "payment_method": "cash",
        "status": "canceled",
        "revision_count": 0,
        "items": []
    }

    with patch("app.core_client.core_client.get_sale", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_sale
        response = client.get("/sales/15/edit")
        assert response.status_code == 200
        assert "не может быть изменена" in response.text


def test_sale_edit_post_success():
    form_data = {
        "payment_method": "transfer",
        "changed_by": "Оператор 1",
        "comment": "Замена товара",
        "item_product_id_1": "2",
        "item_title_1": "Мышь игровая",
        "item_price_1": "3500.0",
        "item_quantity_1": "1"
    }

    with patch("app.core_client.core_client.correct_sale", new_callable=AsyncMock) as mock_correct:
        mock_correct.return_value = {"id": 15, "status": "completed", "total_amount": 3500.0, "revision_count": 1}
        response = client.post("/sales/15/edit", data=form_data, follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/sales/15"
        mock_correct.assert_called_once()
        called_args = mock_correct.call_args[0]
        assert called_args[0] == 15
        assert called_args[1]["payment_method"] == "transfer"
        assert called_args[1]["comment"] == "Замена товара"
        assert len(called_args[1]["items"]) == 1


def test_sale_detail_renders_revision_badge_and_history():
    mock_sale = {
        "id": 15,
        "total_amount": 3500.0,
        "payment_method": "transfer",
        "status": "completed",
        "revision_count": 1,
        "items": [{"product_id": 2, "title": "Мышь игровая", "price": 3500.0, "quantity": 1}]
    }

    mock_revisions = {
        "total": 1,
        "items": [
            {
                "id": 1,
                "sale_id": 15,
                "revision_no": 1,
                "changed_at": "2026-09-17 07:15:00",
                "changed_by": "Оператор 1",
                "comment": "Замена товара",
                "structured_diff": '{"human_bullets": ["• Способ оплаты: Наличные -> Перевод", "• Удалён товар: Клавиатура", "• Добавлен товар: Мышь игровая"]}'
            }
        ]
    }

    with patch("app.core_client.core_client.get_sale", new_callable=AsyncMock) as mock_get_sale, \
         patch("app.core_client.core_client.get_sale_revisions", new_callable=AsyncMock) as mock_get_revs, \
         patch("app.core_client.core_client.get_sale_avito_tasks", new_callable=AsyncMock) as mock_get_avito:
        mock_get_sale.return_value = mock_sale
        mock_get_revs.return_value = mock_revisions
        mock_get_avito.return_value = {"sale_id": 15, "count": 0, "tasks": []}

        response = client.get("/sales/15")
        assert response.status_code == 200
        assert "✎ Изменена (ревизия №1)" in response.text
        assert "История изменений (1)" in response.text
        assert "Способ оплаты: Наличные" in response.text
        assert "Удалён товар: Клавиатура" in response.text
        assert "Добавлен товар: Мышь игровая" in response.text
        assert "Изменить продажу" in response.text


def test_sales_list_renders_edited_marker():
    mock_sales = {
        "total": 1,
        "items": [
            {
                "id": 15,
                "created_at": "2026-09-17 07:00:00",
                "total_amount": 3500.0,
                "payment_method": "transfer",
                "status": "completed",
                "revision_count": 2,
                "items": [{"title": "Мышь", "price": 3500.0, "quantity": 1}]
            }
        ]
    }

    with patch("app.core_client.core_client.get_sales", new_callable=AsyncMock) as mock_get_sales:
        mock_get_sales.return_value = mock_sales
        response = client.get("/sales")
        assert response.status_code == 200
        assert "✎ Изменена ×2" in response.text


def test_sale_receipt_renders_revision_note():
    mock_sale = {
        "id": 15,
        "created_at": "2026-09-17 07:00:00",
        "total_amount": 3500.0,
        "payment_method": "transfer",
        "status": "completed",
        "revision_count": 1,
        "items": [{"title": "Мышь игровая", "price": 3500.0, "quantity": 1, "product_id": 2}]
    }

    with patch("app.core_client.core_client.get_sale", new_callable=AsyncMock) as mock_get_sale, \
         patch("app.core_client.core_client.get_organization_settings", new_callable=AsyncMock) as mock_get_org:
        mock_get_sale.return_value = mock_sale
        mock_get_org.return_value = {"organization_name": "ТехноРебут"}

        response = client.get("/sales/15/receipt")
        assert response.status_code == 200
        assert "Продажа скорректирована — ревизия №1" in response.text
