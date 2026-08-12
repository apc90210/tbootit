from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_avito_extension_route_not_shadowed_by_generic_proxy():
    """Verify /avito/extension is handled directly by admin shell and not forwarded to generic proxy."""
    with patch("app.main._proxy_request", new_callable=AsyncMock) as mock_proxy:
        res = client.get("/avito/extension")
        assert res.status_code == 200
        # Generic proxy should NOT be invoked for /avito/extension
        mock_proxy.assert_not_called()
