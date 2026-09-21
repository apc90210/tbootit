import os
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath("scripts"))
from app.main import app

client = TestClient(app)

def test_extension_page_renders_cleanly():
    """Verify /avito/extension page loads with 200 OK and includes version link."""
    res = client.get("/avito/extension")
    assert res.status_code == 200
    assert any(v in res.text for v in ("0.2.53", "0.2.54", "0.2.55", "0.2.56", "0.2.57", "0.2.58", "0.2.59", "0.2.60", "0.2.61", "0.2.62", "0.2.63", "0.2.64", "0.2.65"))

