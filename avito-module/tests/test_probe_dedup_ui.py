import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app import storage, schemas

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_profile():
    p = schemas.AvitoAccountProfile(account_key="acc_dedup", display_name="Профиль дедупликации", auth_status="authorized")
    storage.save_profile(p)
    yield
    storage.delete_profile("acc_dedup")

@patch("app.services.import_service.run_account_import")
def test_repeat_import_dedup_contract(mock_import):
    # First import creates 1 item
    mock_run1 = schemas.ImportRun(
        run_id="run1",
        account_key="acc_dedup",
        started_at="2026-08-11T10:00:00",
        status="completed",
        created_count=1,
        updated_count=0,
        skipped_count=0,
        items=[schemas.ImportItemResult(external_item_id="8888", title="Товар 1", status="created", product_id=101, photos_imported=2)]
    )

    # Second import updates/unchanged 1 item (created=0)
    mock_run2 = schemas.ImportRun(
        run_id="run2",
        account_key="acc_dedup",
        started_at="2026-08-11T10:05:00",
        status="completed",
        created_count=0,
        updated_count=1,
        skipped_count=0,
        items=[schemas.ImportItemResult(external_item_id="8888", title="Товар 1", status="updated", product_id=101, photos_imported=0)]
    )

    mock_import.side_effect = [mock_run1, mock_run2]

    # Run 1
    res1 = client.post("/accounts/api/profiles/acc_dedup/probe-import", json={"external_item_id": "8888"})
    assert res1.status_code == 200
    r1_data = res1.json()
    assert r1_data["items"][0]["product_id"] == 101
    assert r1_data["created_count"] == 1

    # Run 2
    res2 = client.post("/accounts/api/profiles/acc_dedup/probe-import", json={"external_item_id": "8888"})
    assert res2.status_code == 200
    r2_data = res2.json()
    assert r2_data["items"][0]["product_id"] == 101  # Same product ID!
    assert r2_data["created_count"] == 0  # No new products created!
