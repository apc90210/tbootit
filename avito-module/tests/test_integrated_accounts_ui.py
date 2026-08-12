import os
import shutil
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import storage
from app.config import settings

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_profiles():
    profiles_dir = os.path.join(settings.AVITO_STORAGE_DIR, "profiles")
    if os.path.exists(profiles_dir):
        for folder in os.listdir(profiles_dir):
            if folder.startswith("acc_"):
                shutil.rmtree(os.path.join(profiles_dir, folder), ignore_errors=True)
    profiles_file = os.path.join(settings.AVITO_STORAGE_DIR, "profiles.json")
    if os.path.exists(profiles_file):
        os.remove(profiles_file)
    yield
    if os.path.exists(profiles_dir):
        for folder in os.listdir(profiles_dir):
            if folder.startswith("acc_"):
                shutil.rmtree(os.path.join(profiles_dir, folder), ignore_errors=True)
    if os.path.exists(profiles_file):
        os.remove(profiles_file)

def test_profile_creation_and_limit():
    # Create 3 profiles
    res1 = client.post("/accounts/api/profiles", json={"display_name": "Профиль 1"})
    assert res1.status_code == 200
    assert res1.json()["display_name"] == "Профиль 1"

    res2 = client.post("/accounts/api/profiles", json={"display_name": "Профиль 2"})
    assert res2.status_code == 200

    res3 = client.post("/accounts/api/profiles", json={"display_name": "Профиль 3"})
    assert res3.status_code == 200

    # 4th profile should fail with limit error
    res4 = client.post("/accounts/api/profiles", json={"display_name": "Профиль 4"})
    assert res4.status_code == 400
    assert "Превышен лимит профилей" in res4.json()["detail"]

def test_profile_deletion():
    res = client.post("/accounts/api/profiles", json={"display_name": "Для удаления"})
    key = res.json()["account_key"]

    del_res = client.delete(f"/accounts/api/profiles/{key}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"

    profiles = client.get("/accounts/api/profiles").json()
    assert len(profiles) == 0
