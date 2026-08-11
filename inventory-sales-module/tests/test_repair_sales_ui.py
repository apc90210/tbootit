import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

MOCK_SALES_RESPONSE = {
    "items": [
        {
            "id": 101,
            "total_amount": 2800.0,
            "payment_method": "other",
            "comment": "Ремонт R-20260806-0012 - ноутбук Lenovo IdeaPad. Неисправность: не включается.",
            "status": "completed",
            "source_type": "repair",
            "source_id": 15,
            "created_at": "2026-08-06T14:00:00",
            "items": [
                {
                    "id": 1,
                    "sale_id": 101,
                    "product_id": None,
                    "title": "Ремонт R-20260806-0012",
                    "price": 2800.0,
                    "quantity": 1
                }
            ]
        }
    ],
    "total": 1,
    "limit": 50,
    "offset": 0
}

def test_repair_sales_ui_rendering():
    """
    Test rendering of repair sales in inventory-sales-module UI:
    - Displays 'Ремонт' badge
    - Displays repair description
    - Displays link to repair http://localhost:8040/repairs/15
    """
    with patch("app.routers.sales.core_client.get_sales", new_callable=AsyncMock) as mock_get_sales:
        mock_get_sales.return_value = MOCK_SALES_RESPONSE

        response = client.get("/sales")
        assert response.status_code == 200
        html = response.text

        # Verify Repair badge
        assert "Ремонт" in html
        assert "Ремонт R-20260806-0012" in html
        assert "2800" in html

        # Verify link to repair
        assert 'href="/repairs/repairs/15"' in html
        assert "Открыть ремонт" in html

def test_no_direct_db_imports_in_inventory_sales_module():
    """
    Verify that inventory-sales-module contains zero direct DB imports or connections.
    """
    import glob
    files = glob.glob("app/**/*.py", recursive=True)
    forbidden_terms = ["create_engine", "SessionLocal", "sqlite", "technoreboot.db", "sqlalchemy"]
    for filePath in files:
        with open(filePath, "r", encoding="utf-8") as f:
            content = f.read()
            for term in forbidden_terms:
                assert term not in content, f"Forbidden direct DB term '{term}' found in {filePath}"
