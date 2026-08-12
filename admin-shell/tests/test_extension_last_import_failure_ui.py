import os
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath("scripts"))
from app.main import app

client = TestClient(app)

def test_extension_page_renders_cleanly():
    """Verify /avito/extension page loads with 200 OK and includes version 0.1.3 link."""
    res = client.get("/avito/extension")
    assert res.status_code == 200
    assert "0.1.3" in res.text
