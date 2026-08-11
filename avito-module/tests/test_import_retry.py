import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.services import import_service
from app import storage, schemas

@pytest.mark.asyncio
async def test_import_retry_on_failed_item():
    """
    Test retrying failed items in a run without creating duplicate items on retry.
    """
    run_id = "run-test-retry-123"
    old_run = schemas.ImportRun(
        run_id=run_id,
        account_key="office",
        started_at="2026-08-11T10:00:00",
        status="completed",
        scope="all",
        listings_found=1,
        created_count=0,
        error_count=1,
        items=[
            schemas.ImportItemResult(
                external_item_id="3003",
                title="Принтер Brother",
                status="failed",
                error="HTTP 500 internal error"
            )
        ]
    )
    storage.save_import_run(old_run)

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": "created",
            "product_id": 105,
            "external_listing_id": 30,
            "photos_imported": 0
        }
        mock_post.return_value = mock_resp

        mock_discovery = [
            {
                "external_item_id": "3003",
                "external_url": "https://www.avito.ru/item/3003",
                "title": "Принтер Brother HL-1110",
                "price": 6000.0,
                "remote_status": "active"
            }
        ]

        new_run = await import_service.run_account_import(
            account_key="office",
            scope="all",
            item_id_filter="3003",
            mock_discovery=mock_discovery
        )

        assert new_run.status == "completed"
        assert new_run.created_count == 1
        assert new_run.error_count == 0
        assert new_run.items[0].product_id == 105
