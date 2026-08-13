import pytest
from unittest.mock import patch, MagicMock
from app.routers.integrations import fetch_remote_image_bytes

@patch("httpx.Client.get")
def test_remote_photo_content_type_validation(mock_get):
    """Verify fetch_remote_image_bytes rejects non-image Content-Types (e.g. text/html, application/json)."""
    # Non-image content type
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"content-type": "text/html"}
    mock_resp.content = b"<html>Not an image</html>"
    mock_get.return_value = mock_resp

    res = fetch_remote_image_bytes("https://example.com/notimage.html")
    assert res is None

    # Valid image content type
    mock_resp_img = MagicMock()
    mock_resp_img.status_code = 200
    mock_resp_img.headers = {"content-type": "image/jpeg"}
    mock_resp_img.content = b"\xFF\xD8\xFF\xE0"
    mock_get.return_value = mock_resp_img

    res_img = fetch_remote_image_bytes("https://example.com/real.jpg")
    assert res_img == b"\xFF\xD8\xFF\xE0"
