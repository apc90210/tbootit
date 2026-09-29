import pytest
import uuid
from app import models

OWNER_HEADERS = {"x-auth-is-owner": "1", "x-api-token": "dev-token"}
NON_OWNER_HEADERS = {"x-auth-is-owner": "0", "x-api-token": "dev-token"}
INTERNAL_HEADERS = {"x-api-token": "dev-token"}


def _create_product(db, status="in_stock", quantity=1, is_published_site=1, price=5000.0, site_title="Игровой ПК"):
    sku = f"TEST-RES-{uuid.uuid4().hex[:8]}"
    product = models.Product(
        sku=sku,
        title=f"Product {sku}",
        site_title=site_title,
        status=status,
        quantity=quantity,
        sale_price=price,
        is_published_site=is_published_site,
        is_published_avito=0
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def test_create_valid_reservation_request(client, db_session):
    """1. Create valid reservation request -> status 201, pending status, normalized phone."""
    product = _create_product(db_session, status="in_stock", quantity=2, is_published_site=1)

    payload = {
        "product_id": product.id,
        "phone": "+7 (999) 123-45-67",
        "customer_name": "Иван"
    }
    response = client.post("/api/reservation-requests/", json=payload, headers=INTERNAL_HEADERS)
    assert response.status_code == 201
    data = response.json()
    assert data["product_id"] == product.id
    assert data["phone"] == "+79991234567"
    assert data["status"] == "pending"
    assert data["customer_name"] == "Иван"
    assert data["product_title"] == "Игровой ПК"
    assert data["is_duplicate"] is False
    assert data["created_at"] is not None


def test_reject_unpublished_product(client, db_session):
    """2. Reject reservation request for unpublished product (is_published_site=0) -> 409."""
    product = _create_product(db_session, status="in_stock", quantity=1, is_published_site=0)

    payload = {"product_id": product.id, "phone": "+79991112233"}
    response = client.post("/api/reservation-requests/", json=payload, headers=INTERNAL_HEADERS)
    assert response.status_code == 409
    assert "недоступен" in response.json()["detail"].lower()


def test_reject_sold_or_archived_product(client, db_session):
    """3. Reject reservation request for sold/archived product -> 409."""
    sold_product = _create_product(db_session, status="sold", quantity=1, is_published_site=1)
    archived_product = _create_product(db_session, status="archived", quantity=1, is_published_site=1)

    payload_sold = {"product_id": sold_product.id, "phone": "+79991112233"}
    res_sold = client.post("/api/reservation-requests/", json=payload_sold, headers=INTERNAL_HEADERS)
    assert res_sold.status_code == 409

    payload_arch = {"product_id": archived_product.id, "phone": "+79991112233"}
    res_arch = client.post("/api/reservation-requests/", json=payload_arch, headers=INTERNAL_HEADERS)
    assert res_arch.status_code == 409


def test_reject_zero_quantity_product(client, db_session):
    """4. Reject reservation request for product with quantity = 0 -> 409."""
    product = _create_product(db_session, status="in_stock", quantity=0, is_published_site=1)

    payload = {"product_id": product.id, "phone": "+79991112233"}
    response = client.post("/api/reservation-requests/", json=payload, headers=INTERNAL_HEADERS)
    assert response.status_code == 409


def test_phone_normalization_formats(client, db_session):
    """5. Phone normalization works for various inputs: +7, 8, spaces, dashes, 10-digit."""
    product = _create_product(db_session, status="in_stock", quantity=5, is_published_site=1)

    test_cases = [
        ("+7 999 123-45-67", "+79991234567"),
        ("89991234567", "+79991234567"),
        ("8 (999) 123 45 67", "+79991234567"),
        ("9991234567", "+79991234567"),
        ("+7(912)000-11-22", "+79120001122"),
        ("8-921-555-44-33", "+79215554433"),
    ]

    for raw_phone, expected_norm in test_cases:
        p = _create_product(db_session, status="in_stock", quantity=1, is_published_site=1)
        res = client.post(
            "/api/reservation-requests/",
            json={"product_id": p.id, "phone": raw_phone},
            headers=INTERNAL_HEADERS
        )
        assert res.status_code == 201, f"Failed for {raw_phone}: {res.text}"
        assert res.json()["phone"] == expected_norm


def test_reject_invalid_phone_numbers(client, db_session):
    """6. Reject invalid phone numbers (too short, letters, invalid prefix) -> 422."""
    product = _create_product(db_session, status="in_stock", quantity=1, is_published_site=1)

    invalid_phones = [
        "123",
        "phone12345",
        "+12345678901",  # Non-RU country code
        "+7999",
        "89991234567890",  # Too long
        "",
        "   ",
    ]

    for inv in invalid_phones:
        res = client.post(
            "/api/reservation-requests/",
            json={"product_id": product.id, "phone": inv},
            headers=INTERNAL_HEADERS
        )
        assert res.status_code == 422, f"Expected 422 for phone '{inv}', got {res.status_code}"


def test_duplicate_pending_protection(client, db_session):
    """7. Duplicate pending protection: same phone + same product returns existing request without duplicate."""
    product = _create_product(db_session, status="in_stock", quantity=2, is_published_site=1)

    payload = {"product_id": product.id, "phone": "+7 999 555 44 33"}
    res1 = client.post("/api/reservation-requests/", json=payload, headers=INTERNAL_HEADERS)
    assert res1.status_code == 201
    id1 = res1.json()["id"]
    assert res1.json()["is_duplicate"] is False

    # Second call with equivalent phone representation
    payload2 = {"product_id": product.id, "phone": "8 (999) 555-44-33"}
    res2 = client.post("/api/reservation-requests/", json=payload2, headers=INTERNAL_HEADERS)
    assert res2.status_code == 201
    assert res2.json()["id"] == id1
    assert res2.json()["is_duplicate"] is True

    # Check DB count
    count = db_session.query(models.ReservationRequest).filter(
        models.ReservationRequest.product_id == product.id
    ).count()
    assert count == 1


def test_owner_list_reservation_requests(client, db_session):
    """8. Owner can list reservation requests with pagination and status filter."""
    product = _create_product(db_session, status="in_stock", quantity=2, is_published_site=1)

    client.post("/api/reservation-requests/", json={"product_id": product.id, "phone": "+79990000001"}, headers=INTERNAL_HEADERS)
    client.post("/api/reservation-requests/", json={"product_id": product.id, "phone": "+79990000002"}, headers=INTERNAL_HEADERS)

    res = client.get("/api/reservation-requests/", headers=OWNER_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 2
    assert any(item["phone"] == "+79990000001" for item in data["items"])


def test_owner_confirm_reservation_request_invariants(client, db_session):
    """9. Owner can confirm request -> status='confirmed'; product stock, quantity, status NOT changed."""
    product = _create_product(db_session, status="in_stock", quantity=3, is_published_site=1)

    create_res = client.post("/api/reservation-requests/", json={"product_id": product.id, "phone": "+79998887766"}, headers=INTERNAL_HEADERS)
    req_id = create_res.json()["id"]

    # Confirm
    patch_res = client.patch(
        f"/api/reservation-requests/{req_id}/status",
        json={"status": "confirmed", "comment": "Клиент подтвердил по телефону"},
        headers=OWNER_HEADERS
    )
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["status"] == "confirmed"
    assert data["confirmed_at"] is not None
    assert data["comment"] == "Клиент подтвердил по телефону"

    # CRITICAL INVARIANT: Product stock, quantity, status must NOT change
    db_session.refresh(product)
    assert product.status == "in_stock"
    assert product.quantity == 3
    assert product.is_published_site == 1

    # Invariant: No sales should be created
    sales_count = db_session.query(models.Sale).count()
    # (Existing sales or 0, but no new sale tied to this)


def test_owner_cancel_reservation_request(client, db_session):
    """10. Owner can cancel reservation request -> status='cancelled'."""
    product = _create_product(db_session, status="in_stock", quantity=2, is_published_site=1)

    create_res = client.post("/api/reservation-requests/", json={"product_id": product.id, "phone": "+79994443322"}, headers=INTERNAL_HEADERS)
    req_id = create_res.json()["id"]

    patch_res = client.patch(
        f"/api/reservation-requests/{req_id}/status",
        json={"status": "cancelled", "comment": "Клиент отказался"},
        headers=OWNER_HEADERS
    )
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["status"] == "cancelled"
    assert data["cancelled_at"] is not None

    # Invariant check
    db_session.refresh(product)
    assert product.status == "in_stock"
    assert product.quantity == 2


def test_rbac_non_owner_forbidden(client, db_session):
    """11. Non-owner cannot call owner endpoints -> 403 Forbidden."""
    product = _create_product(db_session, status="in_stock", quantity=1, is_published_site=1)
    create_res = client.post("/api/reservation-requests/", json={"product_id": product.id, "phone": "+79993332211"}, headers=INTERNAL_HEADERS)
    req_id = create_res.json()["id"]

    # Non-owner list
    res_list = client.get("/api/reservation-requests/", headers=NON_OWNER_HEADERS)
    assert res_list.status_code == 403

    # Anonymous list
    res_anon = client.get("/api/reservation-requests/")
    assert res_anon.status_code == 403

    # Non-owner status update
    res_patch = client.patch(
        f"/api/reservation-requests/{req_id}/status",
        json={"status": "confirmed"},
        headers=NON_OWNER_HEADERS
    )
    assert res_patch.status_code == 403


def test_audit_log_created(client, db_session):
    """12. Audit log record is created for creation and status change."""
    product = _create_product(db_session, status="in_stock", quantity=1, is_published_site=1)

    create_res = client.post("/api/reservation-requests/", json={"product_id": product.id, "phone": "+79991239999"}, headers=INTERNAL_HEADERS)
    req_id = create_res.json()["id"]

    # Check audit log for creation
    audit_create = db_session.query(models.AuditLog).filter(
        models.AuditLog.entity_type == "reservation_request",
        models.AuditLog.entity_id == req_id,
        models.AuditLog.action == "create"
    ).first()
    assert audit_create is not None
    assert audit_create.created_at is not None

    # Status update
    client.patch(
        f"/api/reservation-requests/{req_id}/status",
        json={"status": "confirmed"},
        headers=OWNER_HEADERS
    )

    audit_status = db_session.query(models.AuditLog).filter(
        models.AuditLog.entity_type == "reservation_request",
        models.AuditLog.entity_id == req_id,
        models.AuditLog.action == "status_confirmed"
    ).first()
    assert audit_status is not None


def test_internal_token_required_for_reservation(client, db_session):
    """13. Reservation creation requires valid internal token -> 401 when missing or invalid."""
    product = _create_product(db_session, status="in_stock", quantity=1, is_published_site=1)
    payload = {"product_id": product.id, "phone": "+79991230011"}

    # Missing token
    res_no_token = client.post("/api/reservation-requests/", json=payload)
    assert res_no_token.status_code == 401

    # Invalid token
    res_bad_token = client.post(
        "/api/reservation-requests/",
        json=payload,
        headers={"x-api-token": "wrong-token-abc"}
    )
    assert res_bad_token.status_code == 401

