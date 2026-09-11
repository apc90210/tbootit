import pytest
from app import models

def test_batch_update_products(client, db_session):
    # Create 3 test products
    p1 = models.Product(title="Batch Item 1", status="in_stock", storage_location="store", sale_price=1000.0)
    p2 = models.Product(title="Batch Item 2", status="in_stock", storage_location="store", sale_price=2000.0)
    p3 = models.Product(title="Batch Item 3", status="draft", storage_location="workshop", sale_price=3000.0)
    db_session.add_all([p1, p2, p3])
    db_session.commit()
    db_session.refresh(p1)
    db_session.refresh(p2)
    db_session.refresh(p3)

    # 1. Update status for p1 and p2
    res = client.post("/api/products/batch", json={
        "product_ids": [p1.id, p2.id],
        "status": "draft",
        "comment": "Test batch status change"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["updated_count"] == 2
    assert set(data["product_ids"]) == {p1.id, p2.id}

    db_session.refresh(p1)
    db_session.refresh(p2)
    assert p1.status == "draft"
    assert p2.status == "draft"

    # 2. Update storage location for p1, p2, p3
    res2 = client.post("/api/products/batch", json={
        "product_ids": [p1.id, p2.id, p3.id],
        "storage_location": "archive",
        "comment": "Move to archive"
    })
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["success"] is True
    assert data2["updated_count"] == 3

    db_session.refresh(p1)
    db_session.refresh(p2)
    db_session.refresh(p3)
    assert p1.storage_location == "archive"
    assert p2.storage_location == "archive"
    assert p3.storage_location == "archive"

    # 3. Empty product_ids handled gracefully
    res_empty = client.post("/api/products/batch", json={"product_ids": []})
    assert res_empty.status_code == 200
    assert res_empty.json()["updated_count"] == 0
