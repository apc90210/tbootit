import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.services import import_service
from app import storage, schemas

@pytest.mark.asyncio
async def test_one_item_probe_import_execution():
    """
    Test 1-item trial probe import execution with mock payload.
    """
    p = schemas.AvitoAccountProfile(account_key="probe_acc_1", display_name="Пробный Аккаунт")
    storage.save_profile(p)

    mock_discovery = [
        {
            "external_item_id": "7007",
            "external_url": "https://www.avito.ru/item/7007",
            "title": "Пробный Монитор Samsung",
            "price": 12000.0,
            "remote_status": "active"
        }
    ]

    mock_cards = {
        "7007": {
            "title": "Пробный Монитор Samsung 24",
            "price": 12000.0,
            "description": "Монитор в идеальном состоянии",
            "parameters": {"Диагональ": "24"},
            "photos": [{"url": "https://img.avito.st/7007.jpg"}]
        }
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": "created",
            "product_id": 88,
            "external_listing_id": 15,
            "photos_imported": 1
        }
        mock_post.return_value = mock_resp

        run = await import_service.run_account_import(
            account_key="probe_acc_1",
            scope="probe",
            item_id_filter="7007",
            mock_discovery=mock_discovery,
            mock_cards=mock_cards
        )

        assert run.status == "completed"
        assert run.listings_found == 1
        assert run.created_count == 1
        assert run.items[0].product_id == 88

    # Cleanup
    storage.delete_profile("probe_acc_1")
