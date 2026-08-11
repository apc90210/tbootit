import re
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_no_raw_owner_ports_runtime():
    """Verify runtime HTML from admin shell contains 0 raw module ports (8000, 8020, 8030, 8040, 8061)."""
    port_regex = re.compile(r':(8000|8020|8030|8040|8061)\b')
    for route in ["/", "/avito", "/avito/accounts"]:
        res = client.get(route)
        assert res.status_code == 200
        matches = port_regex.findall(res.text)
        assert len(matches) == 0, f"Port leak detected on {route}: {matches}"
