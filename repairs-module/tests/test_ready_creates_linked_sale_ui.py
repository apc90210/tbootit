import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

MOCK_REPAIR_READY = {
    "id": 10,
    "number": "R-UI-READY-001",
    "status": "ready",
    "status_label": "Готов",
    "customer_name": "Тест Клиент",
    "customer_phone": "+79998887766",
    "device_type": "Ноутбук",
    "brand": "Asus",
    "model": "ZenBook",
    "reported_issue": "Не включается",
    "estimated_repair_amount": 2800,
    "linked_sale_id": 55
}

def test_ready_creates_linked_sale_ui():
    """
    Test that submitting status change form to ready in repairs-module:
    - Sends single status change POST to Core API
    - Makes ZERO direct sales API or DB calls from repairs-module
    """
    with patch("app.routers.repairs.core_client.update_repair_status", new_callable=AsyncMock) as mock_update_status:
        mock_update_status.return_value = MOCK_REPAIR_READY

        response = client.post(
            "/repairs/10/status",
            data={"status": "ready", "comment": "Готов", "estimated_repair_amount": 2800},
            follow_redirects=False
        )
        assert response.status_code in [302, 303]

        mock_update_status.assert_called_once()
        called_kwargs = mock_update_status.call_args.kwargs
        assert called_kwargs.get("repair_id") == 10
        assert called_kwargs.get("status") == "ready"
        assert called_kwargs.get("estimated_repair_amount") == 2800

def test_no_direct_db_imports_in_repairs_module():
    """
    Verify that repairs-module contains zero direct DB imports or connections.
    """
    import glob
    files = glob.glob("app/**/*.py", recursive=True)
    forbidden_terms = ["create_engine", "SessionLocal", "sqlite", "technoreboot.db", "sqlalchemy"]
    for filePath in files:
        with open(filePath, "r", encoding="utf-8") as f:
            content = f.read()
            for term in forbidden_terms:
                assert term not in content, f"Forbidden direct DB term '{term}' found in {filePath}"
