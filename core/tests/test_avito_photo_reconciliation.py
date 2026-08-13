"""
Tests for Avito photo set reconciliation during reimport.
Covers: stale low variant removal, manual photo safety, repeat import idempotency,
sort order normalization after reconciliation.
"""

import hashlib
import json
import os
import tempfile

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client with a fresh in-memory database."""
    os.environ["DATABASE_URL"] = "sqlite:///file::memory:?cache=shared"
    os.environ.setdefault("STORAGE_ROOT", tempfile.mkdtemp())

    import importlib
    from app import database, models, main as app_main

    importlib.reload(database)
    importlib.reload(app_main)

    models.Base.metadata.create_all(bind=database.engine)
    from app.main import app
    with TestClient(app) as c:
        yield c


def _make_photo_bytes(label: str) -> bytes:
    """Create unique photo-like bytes from a label."""
    return b"\xff\xd8\xff\xe0" + (label * 200).encode("utf-8")


def _avito_url(prefix: str, la: int) -> str:
    """Build a realistic Avito image CDN URL."""
    return f"https://10.img.avito.st/image/1/1.{prefix}La{la}Nzltest.hash"


def _import_payload(external_item_id: str, photos: list) -> dict:
    return {
        "account_key": "test_account",
        "external_item_id": external_item_id,
        "external_url": f"https://www.avito.ru/item/{external_item_id}",
        "remote_status": "active",
        "title": "Test Listing",
        "price": 1000.0,
        "description": "Test description",
        "category_path": ["Электроника"],
        "brand": "TestBrand",
        "model": "TestModel",
        "condition": "Б/у",
        "parameters": {},
        "photos": photos,
    }


def _photo_entry(url: str, position: int, content_base64: str = None) -> dict:
    entry = {"url": url, "position": position}
    if content_base64:
        entry["content_base64"] = content_base64
    return entry


def _get_db_photos(product_id: int):
    """Query DB directly to get all photo rows with source_url."""
    from app.database import SessionLocal
    from app import models
    db = SessionLocal()
    try:
        photos = db.query(models.ProductPhoto).filter(
            models.ProductPhoto.product_id == product_id
        ).order_by(models.ProductPhoto.sort_order, models.ProductPhoto.id).all()
        result = []
        for p in photos:
            result.append({
                "id": p.id,
                "source_url": p.source_url,
                "sort_order": p.sort_order,
                "content_hash": p.content_hash,
            })
        return result
    finally:
        db.close()


class TestStaleAvitoDuplicateReconciliation:
    """Owner regression: stale low-res Avito photo rows must be removed on reimport."""

    def test_reimport_removes_stale_low_variant(self, client):
        """
        Scenario: DB has La3 + La1 for same canonical identity.
        Reimport triggers reconciliation that removes La1, keeps La3.
        """
        import base64
        photo_a_mid_bytes = _make_photo_bytes("photo_a_mid")
        photo_a_mid_b64 = base64.b64encode(photo_a_mid_bytes).decode()

        # 1st import with mid variant
        url_a_mid = _avito_url("AAAAA", 3)
        payload1 = _import_payload("12345", [
            _photo_entry(url_a_mid, 0, photo_a_mid_b64),
        ])
        res1 = client.post("/api/integrations/avito/import-item", json=payload1)
        assert res1.status_code == 200
        product_id = res1.json()["product_id"]

        # Manually inject a stale low variant (simulating old import)
        from app.database import SessionLocal
        from app import models
        db = SessionLocal()
        try:
            low_bytes = _make_photo_bytes("photo_a_low")
            low_hash = hashlib.sha256(low_bytes).hexdigest()
            storage_dir = os.environ.get("STORAGE_ROOT", "/tmp")
            low_path = os.path.join(storage_dir, "product_photos", f"{product_id}_stale_low.jpg")
            os.makedirs(os.path.dirname(low_path), exist_ok=True)
            with open(low_path, "wb") as f:
                f.write(low_bytes)
            stale_row = models.ProductPhoto(
                product_id=product_id,
                filename=f"{product_id}_stale_low.jpg",
                storage_path=low_path,
                media_url=f"/media/product_photos/{product_id}_stale_low.jpg",
                source_url=_avito_url("AAAAA", 1),  # La1 = same canonical, low quality
                content_hash=low_hash,
                sort_order=1,
            )
            db.add(stale_row)
            db.commit()
        finally:
            db.close()

        # Verify 2 rows before reimport
        db_photos_before = _get_db_photos(product_id)
        assert len(db_photos_before) == 2

        # 2nd import (reimport) with same mid variant
        res2 = client.post("/api/integrations/avito/import-item", json=payload1)
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["photos_reconciled"] >= 1

        # After reimport: only 1 photo row should remain
        db_photos_after = _get_db_photos(product_id)
        assert len(db_photos_after) == 1

        # The remaining photo must be the mid (La3) variant, not the low (La1)
        remaining = db_photos_after[0]
        assert "La3" in (remaining["source_url"] or "")

    def test_manual_photo_preserved_during_avito_reconciliation(self, client):
        """Manual (non-Avito) photos must NOT be removed during Avito reconciliation."""
        import base64

        # Import with one Avito photo
        photo_bytes = _make_photo_bytes("avito_photo")
        photo_b64 = base64.b64encode(photo_bytes).decode()
        url_avito = _avito_url("BBBBB", 3)
        payload = _import_payload("67890", [
            _photo_entry(url_avito, 0, photo_b64),
        ])
        res = client.post("/api/integrations/avito/import-item", json=payload)
        assert res.status_code == 200
        product_id = res.json()["product_id"]

        # Add a manual photo (non-Avito source_url) and stale low variant
        from app.database import SessionLocal
        from app import models
        db = SessionLocal()
        try:
            storage_dir = os.environ.get("STORAGE_ROOT", "/tmp")

            manual_bytes = _make_photo_bytes("manual_photo")
            manual_hash = hashlib.sha256(manual_bytes).hexdigest()
            manual_path = os.path.join(storage_dir, "product_photos", f"{product_id}_manual.jpg")
            os.makedirs(os.path.dirname(manual_path), exist_ok=True)
            with open(manual_path, "wb") as f:
                f.write(manual_bytes)
            manual_row = models.ProductPhoto(
                product_id=product_id,
                filename=f"{product_id}_manual.jpg",
                storage_path=manual_path,
                media_url=f"/media/product_photos/{product_id}_manual.jpg",
                source_url=None,  # Manual photo, no Avito source
                content_hash=manual_hash,
                sort_order=1,
            )
            db.add(manual_row)

            low_bytes = _make_photo_bytes("avito_low")
            low_hash = hashlib.sha256(low_bytes).hexdigest()
            low_path = os.path.join(storage_dir, "product_photos", f"{product_id}_low.jpg")
            with open(low_path, "wb") as f:
                f.write(low_bytes)
            low_row = models.ProductPhoto(
                product_id=product_id,
                filename=f"{product_id}_low.jpg",
                storage_path=low_path,
                media_url=f"/media/product_photos/{product_id}_low.jpg",
                source_url=_avito_url("BBBBB", 1),
                content_hash=low_hash,
                sort_order=2,
            )
            db.add(low_row)
            db.commit()
        finally:
            db.close()

        # 3 rows before reimport
        assert len(_get_db_photos(product_id)) == 3

        # Reimport
        res2 = client.post("/api/integrations/avito/import-item", json=payload)
        assert res2.status_code == 200
        assert res2.json()["photos_reconciled"] >= 1

        # After: manual photo + avito mid = 2 (avito low removed)
        db_photos_after = _get_db_photos(product_id)
        assert len(db_photos_after) == 2

        source_urls = [p["source_url"] for p in db_photos_after]
        # Manual photo (source_url=None) must still exist
        assert any(s is None for s in source_urls)
        # Avito mid variant must still exist
        assert any(s and "La3" in s for s in source_urls)
        # Avito low variant must be gone
        assert not any(s and "La1" in s for s in source_urls)

    def test_repeat_import_idempotent_no_growth(self, client):
        """Repeated imports of the same listing must not grow photo count."""
        import base64
        photo_bytes = _make_photo_bytes("repeat_photo")
        photo_b64 = base64.b64encode(photo_bytes).decode()
        url = _avito_url("CCCCC", 3)
        payload = _import_payload("11111", [
            _photo_entry(url, 0, photo_b64),
        ])

        res1 = client.post("/api/integrations/avito/import-item", json=payload)
        assert res1.status_code == 200
        product_id = res1.json()["product_id"]

        for _ in range(3):
            res = client.post("/api/integrations/avito/import-item", json=payload)
            assert res.status_code == 200

        db_photos = _get_db_photos(product_id)
        assert len(db_photos) == 1

    def test_sort_order_contiguous_after_reconciliation(self, client):
        """After reconciliation removes stale variants, sort_order must be 0..N-1."""
        import base64

        photos_input = []
        for i, prefix in enumerate(["DDDDD", "EEEEE", "FFFFF"]):
            pb = _make_photo_bytes(f"photo_{prefix}")
            pb64 = base64.b64encode(pb).decode()
            photos_input.append(_photo_entry(_avito_url(prefix, 3), i, pb64))

        payload = _import_payload("22222", photos_input)
        res = client.post("/api/integrations/avito/import-item", json=payload)
        assert res.status_code == 200
        product_id = res.json()["product_id"]

        # Inject stale low variants for each
        from app.database import SessionLocal
        from app import models
        db = SessionLocal()
        try:
            storage_dir = os.environ.get("STORAGE_ROOT", "/tmp")
            for prefix in ["DDDDD", "EEEEE", "FFFFF"]:
                low_bytes = _make_photo_bytes(f"low_{prefix}")
                low_hash = hashlib.sha256(low_bytes).hexdigest()
                low_path = os.path.join(storage_dir, "product_photos", f"{product_id}_{prefix}_low.jpg")
                os.makedirs(os.path.dirname(low_path), exist_ok=True)
                with open(low_path, "wb") as f:
                    f.write(low_bytes)
                db.add(models.ProductPhoto(
                    product_id=product_id,
                    filename=f"{product_id}_{prefix}_low.jpg",
                    storage_path=low_path,
                    media_url=f"/media/product_photos/{product_id}_{prefix}_low.jpg",
                    source_url=_avito_url(prefix, 1),
                    content_hash=low_hash,
                    sort_order=10 + hash(prefix) % 100,
                ))
            db.commit()
        finally:
            db.close()

        # 6 rows before reimport
        assert len(_get_db_photos(product_id)) == 6

        # Reimport
        res2 = client.post("/api/integrations/avito/import-item", json=payload)
        assert res2.status_code == 200
        assert res2.json()["photos_reconciled"] == 3

        # After: 3 photos with contiguous sort_order 0,1,2
        db_photos_after = _get_db_photos(product_id)
        assert len(db_photos_after) == 3
        sort_orders = sorted([p["sort_order"] for p in db_photos_after])
        assert sort_orders == [0, 1, 2]
