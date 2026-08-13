import pytest
from unittest.mock import patch, MagicMock
from app.routers.integrations import fetch_remote_image_bytes

@patch("httpx.Client.get")
def test_remote_photo_size_limit_enforcement(mock_get):
    """Verify fetch_remote_image_bytes rejects images exceeding 10 MB."""
    # 11 MB fake payload
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"content-type": "image/png"}
    mock_resp.content = b"0" * (11 * 1024 * 1024)
    mock_get.return_value = mock_resp

    res = fetch_remote_image_bytes("https://example.com/huge.png")
    assert res is None
