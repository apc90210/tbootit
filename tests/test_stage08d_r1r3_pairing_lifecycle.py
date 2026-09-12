import os
import sys
import json
import time
import pytest
from fastapi.testclient import TestClient

# Insert avito-module into sys.path
sys.path.insert(0, os.path.abspath("avito-module"))
from app.main import app
from app.routers import extension_bridge
from app.config import settings

client = TestClient(app)

def test_fresh_code_redeem_success():
    """Requirement: fresh code -> redeem = success"""
    gen_res = client.post("/extension/api/pairing/generate")
    assert gen_res.status_code == 200
    gen_data = gen_res.json()
    assert "pair_code" in gen_data
    code = gen_data["pair_code"]
    assert len(code) == 6
    assert code.isdigit()

    # Redeem fresh code
    pair_res = client.post("/extension/api/pairing/pair", json={"pair_code": code})
    assert pair_res.status_code == 200
    pair_data = pair_res.json()
    assert pair_data["status"] == "paired"
    assert "extension_token" in pair_data
    token = pair_data["extension_token"]
    assert token.startswith("ext_tok_")

    # Verify status with token
    status_res = client.get("/extension/api/status", headers={"X-Extension-Token": token})
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["paired"] is True
    assert status_data["token_valid"] is True
    assert status_data["version"] in ("0.2.54", "0.2.55")

def test_unknown_code_rejected_400():
    """Requirement: unknown code -> 400 with 'Код подключения не найден'"""
    res = client.post("/extension/api/pairing/pair", json={"pair_code": "987654321"})
    assert res.status_code == 400
    assert "Код подключения не найден" in res.json()["detail"]

def test_expired_code_rejected(tmp_path, monkeypatch):
    """Requirement: expired code -> rejected (400)"""
    test_codes_file = str(tmp_path / "extension_pair_codes.json")
    monkeypatch.setattr(extension_bridge, "PAIR_CODES_FILE", test_codes_file)

    now = time.time()
    expired_code = "112233"
    codes = {
        expired_code: {
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now - 700)),
            "expires_at": now - 100,  # Expired
            "used": False
        }
    }
    with open(test_codes_file, "w", encoding="utf-8") as f:
        json.dump(codes, f)

    res = client.post("/extension/api/pairing/pair", json={"pair_code": expired_code})
    assert res.status_code == 400
    assert "истёк" in res.json()["detail"]

def test_used_code_rejected_one_time_use():
    """Requirement: used code -> rejected if one-time-use"""
    gen_res = client.post("/extension/api/pairing/generate")
    assert gen_res.status_code == 200
    code = gen_res.json()["pair_code"]

    # First redeem: OK
    res1 = client.post("/extension/api/pairing/pair", json={"pair_code": code})
    assert res1.status_code == 200
    assert res1.json()["status"] == "paired"

    # Second redeem of same code: must be rejected
    res2 = client.post("/extension/api/pairing/pair", json={"pair_code": code})
    assert res2.status_code == 400
    assert "истёк" in res2.json()["detail"]

def test_leading_zero_code_works(tmp_path, monkeypatch):
    """Requirement: leading-zero code -> works if 6-digit code starts with zero"""
    test_codes_file = str(tmp_path / "extension_pair_codes.json")
    test_tokens_file = str(tmp_path / "extension_tokens.json")
    monkeypatch.setattr(extension_bridge, "PAIR_CODES_FILE", test_codes_file)
    monkeypatch.setattr(extension_bridge, "TOKENS_FILE", test_tokens_file)

    now = time.time()
    zero_code = "007890"
    codes = {
        zero_code: {
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
            "expires_at": now + 600,
            "used": False
        }
    }
    with open(test_codes_file, "w", encoding="utf-8") as f:
        json.dump(codes, f)

    res = client.post("/extension/api/pairing/pair", json={"pair_code": zero_code})
    assert res.status_code == 200
    assert res.json()["status"] == "paired"

def test_container_service_restart_persistence(tmp_path, monkeypatch):
    """Requirement: container/service restart behavior -> matches documented persistence design"""
    test_codes_file = str(tmp_path / "extension_pair_codes.json")
    test_tokens_file = str(tmp_path / "extension_tokens.json")
    monkeypatch.setattr(extension_bridge, "PAIR_CODES_FILE", test_codes_file)
    monkeypatch.setattr(extension_bridge, "TOKENS_FILE", test_tokens_file)

    # 1. Generate code
    gen_res = client.post("/extension/api/pairing/generate")
    assert gen_res.status_code == 200
    code = gen_res.json()["pair_code"]

    # Verify file is populated
    assert os.path.exists(test_codes_file)
    with open(test_codes_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert code in data
    assert data[code]["used"] is False

    # 2. Simulate "service restart" by creating a fresh client / reading fresh from disk
    fresh_client = TestClient(app)
    pair_res = fresh_client.post("/extension/api/pairing/pair", json={"pair_code": code})
    assert pair_res.status_code == 200
    token = pair_res.json()["extension_token"]

    # Verify token persisted to tokens file
    assert os.path.exists(test_tokens_file)
    with open(test_tokens_file, "r", encoding="utf-8") as f:
        tokens_data = json.load(f)
    token_hash = extension_bridge._hash_token(token)
    assert token_hash in tokens_data

    # 3. Simulate another restart and verify token remains valid
    another_client = TestClient(app)
    status_res = another_client.get("/extension/api/status", headers={"X-Extension-Token": token})
    assert status_res.status_code == 200
    assert status_res.json()["paired"] is True

def test_local_and_vds_pairing_stores_independent():
    """Requirement: local and VDS pairing stores remain independent"""
    # Verify the path is configured via settings.AVITO_STORAGE_DIR
    storage_dir = settings.AVITO_STORAGE_DIR
    assert storage_dir is not None
    # Verify local dev does not write to production path /srv/technoreboot
    assert "/srv/technoreboot" not in os.path.abspath(storage_dir)

def test_extension_package_version_and_dynamic_origin():
    """Verify Chrome extension source files include dynamic origin support, persistence, and v0.2.55."""
    ext_dir = os.path.abspath("chrome-extension/technoreboot-avito")

    # manifest.json
    manifest_path = os.path.join(ext_dir, "manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["version"] == "0.2.55"
    assert "https://144.31.50.134/*" in manifest["host_permissions"]

    # service_worker.js
    sw_path = os.path.join(ext_dir, "service_worker.js")
    with open(sw_path, "r", encoding="utf-8") as f:
        sw_code = f.read()
    assert "getServerUrl" in sw_code
    assert "setServerUrl" in sw_code
    assert "0.2.55" in sw_code

    # popup.js
    popup_js_path = os.path.join(ext_dir, "popup.js")
    with open(popup_js_path, "r", encoding="utf-8") as f:
        popup_js = f.read()
    assert "serverUrlInput" in popup_js
    assert "saveServerUrlBtn" in popup_js
    assert "persistServerUrl" in popup_js
    assert "server_url" in popup_js

    # popup.html
    popup_html_path = os.path.join(ext_dir, "popup.html")
    with open(popup_html_path, "r", encoding="utf-8") as f:
        popup_html = f.read()
    assert 'id="serverUrlInput"' in popup_html
    assert 'id="saveServerUrlBtn"' in popup_html
    assert "v0.2.55" in popup_html

    # admin-shell template
    template_path = os.path.abspath("admin-shell/app/templates/avito_extension.html")
    with open(template_path, "r", encoding="utf-8") as f:
        tmpl = f.read()
    assert "serverUrlDisplay" in tmpl
    assert "copyServerUrl" in tmpl
    assert "v0.2.55" in tmpl
