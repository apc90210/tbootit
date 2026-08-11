import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.services import import_service

@pytest.mark.asyncio
async def test_photo_payload_generation():
    """
    Test that card photo URLs are correctly included in payload sent to Core API.
    """
    mock_discovery = [
        {
            "external_item_id": "2002",
            "external_url": "https://www.avito.ru/item/2002",
            "title": "Фотокамера Canon",
            "price": 30000.0,
            "remote_status": "active"
        }
    ]

    mock_cards = {
        "2002": {
            "title": "Фотокамера Canon EOS 80D",
            "price": 30000.0,
            "description": "Зеркальный фотоаппарат",
            "photos": [
                {"url": "https://img.avito.st/camera1.jpg"},
                {"url": "https://img.avito.st/camera2.jpg"}
            ]
        }
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": "created",
            "product_id": 99,
            "external_listing_id": 20,
            "photos_imported": 2
        }
        mock_post.return_value = mock_resp

        run = await import_service.run_account_import(
            account_key="main",
            scope="all",
            mock_discovery=mock_discovery,
            mock_cards=mock_cards
        )

        assert run.created_count == 1
        assert mock_post.called
        sent_payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1].get("json")
        assert len(sent_payload["photos"]) == 2
        assert sent_payload["photos"][0]["url"] == "https://img.avito.st/camera1.jpg"
