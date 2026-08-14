import re
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_nav_crawl_templates_no_raw_ports():
    """Verify that templates rendered by admin-shell contain 0 raw owner-facing module ports (8000, 8020, 8030, 8040, 8061)."""
    raw_port_pattern = re.compile(r'href=["\']http://(localhost|127\.0\.0\.1):(8000|8020|8030|8040|8061)')
    
    pages = ["/", "/avito/extension"]
    for p in pages:
        res = client.get(p)
        assert res.status_code == 200
        assert not raw_port_pattern.findall(res.text), f"Raw owner port found on page {p}"
