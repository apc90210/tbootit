import json
import hashlib
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import update, case
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from app import models, schemas
from app.routers.customers import log_audit
from app.routers.products import log_product_event
from app.routers.reports import PAYMENT_METHODS_LABELS

VALID_PAYMENT_METHODS = ["cash", "card", "transfer", "sbp", "legal_entity_account", "mixed", "other"]


def compute_checkout_hash(items: List[Dict[str, Any]], payment_method: str, customer_id: Optional[int] = None) -> str:
    """
    Computes a deterministic SHA-256 hash of the checkout request payload.
    Items are sorted by product_id to ensure order-independence.
    """
    norm_items = sorted(
        [
            {
                "product_id": int(it["product_id"]),
                "quantity": int(it["quantity"]),
                "price": round(float(it["price"]), 2)
            }
            for it in items
        ],
        key=lambda x: x["product_id"]
    )
    payload = {
        "items": norm_items,
        "payment_method": str(payment_method).strip().lower(),
        "customer_id": customer_id
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def execute_canonical_sale(
    db: Session,
    items_data: List[Dict[str, Any]],
    payment_method: str = "cash",
    customer_id: Optional[int] = None,
    comment: Optional[str] = None,
    source_type: Optional[str] = None,
    source_id: Optional[int] = None,
    warranty_days: Optional[int] = 30,
    warranty_enabled: Optional[bool] = True,
    client_checkout_id: Optional[str] = None,
    cashier_name: Optional[str] = None
) -> Tuple[models.Sale, bool]:
    """
    Executes a canonical sale inside a single atomic database transaction.
    Enforces identical business rules across desktop and mobile POS:
      - Valid payment method
      - Valid non-empty items
      - Product existence, status in ('in_stock', 'reserved'), storage_location == 'store'
      - Available stock >= requested quantity
      - Quantity > 0, Price >= 0.0
      - Durable SQLite-backed idempotency for mobile checkouts (client_checkout_id)
      - Exact stock decrement and stock movement creation
      - Audit and product event logging
      - Full rollback on ANY failure: no partial sales, no partial stock decrements

    Returns:
      (sale_model, was_replayed_idempotently: bool)
    """
    # 1. Validate payment method
    clean_pm = (payment_method or "").strip().lower()
    if clean_pm not in VALID_PAYMENT_METHODS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid payment method. Allowed: {', '.join(VALID_PAYMENT_METHODS)}"
        )

    # 2. Validate items presence
    if not items_data:
        raise HTTPException(status_code=400, detail="Sale must contain at least one item")

    # 3. Check durable idempotency if client_checkout_id is supplied
    clean_checkout_id = client_checkout_id.strip() if client_checkout_id else None
    req_hash = None
    if clean_checkout_id:
        if not clean_checkout_id:
            raise HTTPException(status_code=400, detail="client_checkout_id cannot be blank")
        req_hash = compute_checkout_hash(items_data, clean_pm, customer_id)

        existing_idem = db.query(models.CheckoutIdempotency).filter(
            models.CheckoutIdempotency.client_checkout_id == clean_checkout_id
        ).first()

        if existing_idem:
            if existing_idem.request_hash != req_hash:
                raise HTTPException(
                    status_code=409,
                    detail="Idempotency key reused with different request payload"
                )
            existing_sale = db.query(models.Sale).filter(models.Sale.id == existing_idem.sale_id).first()
            if existing_sale:
                return existing_sale, True

    # 4. Validate items integrity and stock limits before mutating
    product_ids = set()
    for item in items_data:
        p_id = item.get("product_id")
        if p_id is None:
            raise HTTPException(status_code=400, detail="Missing product_id in sale item")
        qty = item.get("quantity")
        if qty is None or qty <= 0:
            raise HTTPException(status_code=400, detail="Item quantity must be > 0")
        price = item.get("price")
        if price is None or price < 0:
            raise HTTPException(status_code=400, detail="Item price must be >= 0")
        if p_id in product_ids:
            raise HTTPException(status_code=400, detail=f"Duplicate product_id {p_id} in sale")
        product_ids.add(p_id)

        db_product = db.query(models.Product).filter(models.Product.id == p_id).first()
        if not db_product:
            raise HTTPException(status_code=404, detail=f"Product {p_id} not found")
        if db_product.status not in ["in_stock", "reserved"]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot sell product {p_id} in status '{db_product.status}'"
            )
        if db_product.storage_location != "store":
            raise HTTPException(
                status_code=400,
                detail=f"Product {p_id} must be in 'store' location to be sold"
            )
        avail = db_product.quantity or 0
        if avail < qty:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient quantity for product {p_id}. Available: {avail}"
            )

    # 5. Execute single atomic transaction
    calculated_total = round(sum(float(item["price"]) * int(item["quantity"]) for item in items_data), 2)

    try:
        db_sale = models.Sale(
            customer_id=customer_id,
            total_amount=calculated_total,
            payment_method=clean_pm,
            comment=comment,
            status="completed",
            source_type=source_type,
            source_id=source_id,
            warranty_days=warranty_days,
            warranty_enabled=1 if warranty_enabled else 0,
            client_checkout_id=clean_checkout_id
        )
        db.add(db_sale)
        db.flush()  # allocate db_sale.id within the active transaction

        for item in items_data:
            p_id = int(item["product_id"])
            qty = int(item["quantity"])
            unit_price = round(float(item["price"]), 2)

            db_product = db.query(models.Product).filter(models.Product.id == p_id).first()
            if not db_product:
                raise HTTPException(status_code=404, detail=f"Product {p_id} not found")

            # Atomic check-and-decrement at SQL level to prevent concurrency oversell
            res = db.execute(
                update(models.Product)
                .where(models.Product.id == p_id)
                .where(models.Product.quantity >= qty)
                .values(quantity=models.Product.quantity - qty)
            )
            if res.rowcount == 0:
                cur_prod = db.query(models.Product).filter(models.Product.id == p_id).first()
                avail_now = cur_prod.quantity if cur_prod else 0
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient quantity for product {p_id}. Available: {avail_now}"
                )

            db.expire(db_product)
            new_quantity = db_product.quantity
            old_quantity = new_quantity + qty

            # Resolve immutable Avito item ID and URL snapshot at checkout time
            snap_item_id = None
            snap_listing_url = None

            if item.get("avito_item_id"):
                snap_item_id = str(item["avito_item_id"]).strip()
                from app.routers.avito_post_sale import _canonical_avito_url
                snap_listing_url = _canonical_avito_url(item.get("avito_listing_url"), snap_item_id)
            else:
                ext_listing = db.query(models.ProductExternalListing).filter(
                    models.ProductExternalListing.product_id == p_id,
                    models.ProductExternalListing.marketplace == "avito"
                ).order_by(
                    case((models.ProductExternalListing.remote_status.in_(["active", "published"]), 1), else_=0).desc(),
                    models.ProductExternalListing.updated_at.desc().nullslast(),
                    models.ProductExternalListing.id.desc()
                ).first()

                if ext_listing and ext_listing.external_item_id:
                    snap_item_id = str(ext_listing.external_item_id).strip()
                    from app.routers.avito_post_sale import _canonical_avito_url
                    snap_listing_url = _canonical_avito_url(ext_listing.external_url, snap_item_id)
                elif db_product.sku and str(db_product.sku).startswith("AVITO-"):
                    candidate_id = str(db_product.sku)[len("AVITO-"):].strip()
                    if candidate_id:
                        snap_item_id = candidate_id
                        from app.routers.avito_post_sale import _canonical_avito_url
                        snap_listing_url = _canonical_avito_url(None, snap_item_id)

            item_title = item.get("title") or db_product.title or f"Товар #{p_id}"
            db_item = models.SaleItem(
                product_id=p_id,
                title=item_title,
                price=unit_price,
                quantity=qty,
                sale_id=db_sale.id,
                avito_item_id=snap_item_id,
                avito_listing_url=snap_listing_url
            )
            db.add(db_item)

            old_status = db_product.status
            old_location = db_product.storage_location

            mov = models.StockMovement(
                product_id=p_id,
                movement_type="sale",
                quantity_delta=-qty,
                old_quantity=old_quantity,
                new_quantity=new_quantity,
                reason="sale",
                comment=f"Sale {db_sale.id}"
            )
            db.add(mov)

            if new_quantity == 0:
                db_product.status = "sold"
                db_product.storage_location = "archive"

            log_product_event(
                db,
                p_id,
                "sale_completed",
                old_value={"status": old_status, "quantity": old_quantity, "storage_location": old_location},
                new_value={"status": db_product.status, "quantity": db_product.quantity, "storage_location": db_product.storage_location},
                comment=f"Sold {qty} items in sale {db_sale.id}. Price: {unit_price}"
            )

        if clean_checkout_id and req_hash:
            idem_record = models.CheckoutIdempotency(
                client_checkout_id=clean_checkout_id,
                sale_id=db_sale.id,
                request_hash=req_hash,
                cashier_name=cashier_name
            )
            db.add(idem_record)

        log_audit(
            db,
            "sale",
            db_sale.id,
            "create",
            new_value={
                "total_amount": calculated_total,
                "payment_method": clean_pm,
                "client_checkout_id": clean_checkout_id
            },
            comment=f"Sale created by {cashier_name or 'Cashier'}"
        )

        db.commit()
        db.refresh(db_sale)
        return db_sale, False

    except IntegrityError as e:
        db.rollback()
        # Handle concurrent submission with the exact same checkout_id
        if clean_checkout_id:
            existing_idem = db.query(models.CheckoutIdempotency).filter(
                models.CheckoutIdempotency.client_checkout_id == clean_checkout_id
            ).first()
            if existing_idem:
                if existing_idem.request_hash == req_hash:
                    existing_sale = db.query(models.Sale).filter(models.Sale.id == existing_idem.sale_id).first()
                    if existing_sale:
                        return existing_sale, True
                else:
                    raise HTTPException(status_code=409, detail="Idempotency key reused with different request payload")
        raise HTTPException(status_code=400, detail=f"Database integrity constraint violated: {str(e)}")
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Sale execution error: {str(e)}")


def build_sale_checkout_response(
    db: Session,
    db_sale: models.Sale,
    client_checkout_id: str
) -> schemas.SaleCheckoutResponse:
    """
    Constructs a SaleCheckoutResponse reusing canonical receipt formatting.
    """
    org_settings = db.query(models.OrganizationSettings).first()
    cashier = org_settings.default_cashier_name if org_settings else None

    if client_checkout_id:
        idem = db.query(models.CheckoutIdempotency).filter(
            models.CheckoutIdempotency.client_checkout_id == client_checkout_id
        ).first()
        if idem and idem.cashier_name:
            cashier = idem.cashier_name

    raw_pm = db_sale.payment_method if db_sale.payment_method else "unspecified"
    raw_pm = raw_pm.strip() if raw_pm else "unspecified"
    pm_label = PAYMENT_METHODS_LABELS.get(raw_pm, PAYMENT_METHODS_LABELS.get("other", raw_pm))

    items = []
    for item in db_sale.items:
        sku = None
        barcode = None
        if item.product_id:
            prod = db.query(models.Product).filter(models.Product.id == item.product_id).first()
            if prod:
                sku = prod.sku
                barcode = prod.barcode
        unit_price = float(item.price) if item.price is not None else 0.0
        qty = int(item.quantity) if item.quantity is not None else 0
        line_total = round(unit_price * qty, 2)
        items.append(
            schemas.SaleReceiptItem(
                id=item.id,
                product_id=item.product_id,
                title=item.title or (f"Товар #{item.product_id}" if item.product_id else "Товар"),
                sku=sku,
                barcode=barcode,
                quantity=qty,
                unit_price=unit_price,
                line_total=line_total,
            )
        )

    receipt_number = f"REC-{db_sale.id:06d}"
    return schemas.SaleCheckoutResponse(
        sale_id=db_sale.id,
        receipt_number=receipt_number,
        status=db_sale.status,
        created_at=db_sale.created_at or datetime.utcnow(),
        total_amount=float(db_sale.total_amount) if db_sale.total_amount is not None else 0.0,
        payment_method=raw_pm,
        payment_label=pm_label,
        cashier_name=cashier,
        client_checkout_id=client_checkout_id,
        items=items,
    )
