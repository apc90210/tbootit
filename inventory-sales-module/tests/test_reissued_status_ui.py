import pytest
import respx
from httpx import Response
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@respx.mock
def test_sales_list_reissued_filter_and_badges():
    respx.get("http://core:8000/api/sales/").mock(return_value=Response(200, json={
        "total": 2,
        "items": [
            {
                "id": 1,
                "created_at": "2026-08-03T09:00:00",
                "total_amount": 1000.0,
                "payment_method": "cash",
                "status": "completed",
                "items": []
            },
            {
                "id": 2,
                "created_at": "2026-08-03T09:05:00",
                "total_amount": 1000.0,
                "payment_method": "card",
                "status": "reissued",
                "source_sale_id": 1,
                "items": []
            }
        ]
    }))

    resp = client.get("/sales")
    assert resp.status_code == 200
    assert "Повторно оформлена" in resp.text
    assert "Завершена" in resp.text

@respx.mock
def test_sales_detail_reissued_and_superseded_badges():
    respx.get("http://core:8000/api/sales/2").mock(return_value=Response(200, json={
        "id": 2,
        "created_at": "2026-08-03T09:05:00",
        "total_amount": 1000.0,
        "payment_method": "card",
        "status": "reissued",
        "source_sale_id": 1,
        "items": []
    }))

    resp = client.get("/sales/2")
    assert resp.status_code == 200
    assert "Повторно оформленная продажа" in resp.text
    assert "№1" in resp.text

@respx.mock
def test_sale_receipt_reissued_marker():
    respx.get("http://core:8000/api/sales/2/receipt/data").mock(return_value=Response(200, json={
        "id": 2,
        "sale_id": 2,
        "receipt_number": "REC-000002",
        "receipt_title": "Товарный чек № 2 от 2026-08-03",
        "date_formatted": "2026-08-03",
        "created_at": "2026-08-03T09:05:00",
        "total_amount": 1000.0,
        "total_amount_formatted": "1000.00",
        "prepayment_formatted": "0.00",
        "to_pay_formatted": "1000.00",
        "payment_method": "card",
        "payment_method_label": "Банковская карта",
        "status": "reissued",
        "status_banner_text": "ПОВТОРНО ОФОРМЛЕННАЯ ПРОДАЖА (НА ОСНОВЕ ПРОДАЖИ №1)",
        "status_banner_bg_color": "#007bff",
        "source_sale_id": 1,
        "organization_name": "ИП Тест",
        "inn": "1234567890",
        "address": "Тестовый адрес",
        "phone": "+70000000000",
        "items": [],
        "total_items_count": 0,
        "warranty_title": "Гарантийные условия",
        "warranty_enabled": True,
        "warranty_days": 30,
        "warranty_headline": "Гарантия",
        "warranty_body_text": "Условия",
    }))

    resp = client.get("/sales/2/receipt")
    assert resp.status_code == 200
    assert "ПОВТОРНО ОФОРМЛЕННАЯ ПРОДАЖА" in resp.text
    assert "№1" in resp.text

