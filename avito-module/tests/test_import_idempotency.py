import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.services import import_service
from app import storage

@pytest.mark.asyncio
async def test_account_import_orchestration():
    """
    Test end-to-end import orchestration:
    - Runs account import with mock discovery and cards
    - Posts payloads to Core API
    - Saves ImportRun record and updates profile statistics
    """
    mock_discovery = [
        {
            "external_item_id": "1001",
            "external_url": "https://www.avito.ru/item/1001",
            "title": "Монитор LG 27",
            "price": 15000.0,
            "remote_status": "active"
        }
    ]

    mock_cards = {
        "1001": {
            "title": "Монитор LG 27 UltraFine",
            "price": 15000.0,
            "description": "4K IPS монитор",
            "parameters": {"Диагональ": "27"},
            "photos": [{"url": "https://img.avito.st/1001.jpg"}]
        }
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": "created",
            "product_id": 42,
            "external_listing_id": 10,
            "photos_imported": 1
        }
        mock_post.return_value = mock_resp

        run = await import_service.run_account_import(
            account_key="main",
            scope="all",
            mock_discovery=mock_discovery,
            mock_cards=mock_cards
        )

        assert run.status == "completed"
        assert run.listings_found == 1
        assert run.created_count == 1
        assert len(run.items) == 1
        assert run.items[0].product_id == 42

        # Verify saved run
        saved_run = storage.get_import_run(run.run_id)
        assert saved_run is not None
        assert saved_run.created_count == 1
