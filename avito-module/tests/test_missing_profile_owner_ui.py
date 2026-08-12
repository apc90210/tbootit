from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_missing_profile_returns_404_not_found():
    """Verify requesting nonexistent profile returns 404."""
    res = client.get("/accounts/api/profiles/acc_nonexistent_xyz")
    assert res.status_code == 404
    assert res.json()["detail"] == "Profile not found"
