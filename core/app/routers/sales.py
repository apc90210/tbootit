from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from datetime import datetime, date
import json
from app.database import get_db
from app import models, schemas
from app.routers.customers import log_audit
from app.routers.products import log_product_event
from app.routers.reports import PAYMENT_METHODS_LABELS

router = APIRouter()

VALID_PAYMENT_METHODS = ["cash", "card", "transfer", "sbp", "legal_entity_account", "mixed", "other"]

@router.get("/", response_model=schemas.SaleListResponse)
def get_sales(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    payment_method: Optional[str] = None,
    customer_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Sale)
    
    if status:
        query = query.filter(models.Sale.status == status)
    if date_from:
        query = query.filter(models.Sale.created_at >= date_from)
    if date_to:
        query = query.filter(models.Sale.created_at <= date_to)
    if payment_method:
        query = query.filter(models.Sale.payment_method == payment_method)
    if customer_id:
        query = query.filter(models.Sale.customer_id == customer_id)
        
    query = query.order_by(models.Sale.created_at.desc())
    total = query.count()
    items = query.offset(offset).limit(limit).all()
    
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@router.get("/today", response_model=schemas.SaleListResponse)
def get_sales_today(db: Session = Depends(get_db)):
    today = date.today()
    query = db.query(models.Sale).filter(models.Sale.created_at >= today).order_by(models.Sale.created_at.desc())
    total = query.count()
    items = query.all()
    
    return {
        "items": items,
        "total": total,
        "limit": 1000,
        "offset": 0
    }

@router.post("/", response_model=schemas.Sale)
def create_sale(sale: schemas.SaleCreate, db: Session = Depends(get_db)):
    if sale.payment_method not in VALID_PAYMENT_METHODS:
        raise HTTPException(status_code=400, detail=f"Invalid payment method. Allowed: {', '.join(VALID_PAYMENT_METHODS)}")
        
    if not sale.items:
        raise HTTPException(status_code=400, detail="Sale must contain at least one item")

    # Validate items before processing
    product_ids = set()
    for item in sale.items:
        if item.quantity <= 0:
            raise HTTPException(status_code=400, detail="Item quantity must be > 0")
        if item.price < 0:
            raise HTTPException(status_code=400, detail="Item price must be >= 0")
        if item.product_id in product_ids:
            raise HTTPException(status_code=400, detail=f"Duplicate product_id {item.product_id} in sale")
        product_ids.add(item.product_id)
        
        db_product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not db_product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        if db_product.status not in ["in_stock", "reserved"]:
            raise HTTPException(status_code=400, detail=f"Cannot sell product {item.product_id} in status '{db_product.status}'")
        if db_product.storage_location != "store":
            raise HTTPException(status_code=400, detail=f"Product {item.product_id} must be in 'store' location to be sold")
        if (db_product.quantity or 0) < item.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient quantity for product {item.product_id}. Available: {db_product.quantity or 0}")

    calculated_total = sum(item.price * item.quantity for item in sale.items)

    sale_data = sale.model_dump()
    items_data = sale_data.pop("items")
    
    sale_data["total_amount"] = calculated_total
    sale_data["warranty_enabled"] = 1 if sale_data.get("warranty_enabled") else 0
    sale_data["status"] = "completed"
    
    db_sale = models.Sale(**sale_data)
    db.add(db_sale)
    db.commit()
    db.refresh(db_sale)
    
    for item in items_data:
        db_item = models.SaleItem(**item, sale_id=db_sale.id)
        db.add(db_item)
        
        db_product = db.query(models.Product).filter(models.Product.id == item["product_id"]).first()
        old_status = db_product.status
        old_location = db_product.storage_location
        old_quantity = db_product.quantity or 0
        db_product.quantity = old_quantity - item["quantity"]
        
        mov = models.StockMovement(
            product_id=db_product.id,
            movement_type="sale",
            quantity_delta=-item["quantity"],
            old_quantity=old_quantity,
            new_quantity=db_product.quantity,
            reason="sale",
            comment=f"Sale {db_sale.id}"
        )
        db.add(mov)

        if db_product.quantity == 0:
            db_product.status = "sold"
            db_product.storage_location = "archive"
        
        log_product_event(db, db_product.id, "sale_completed", old_value={"status": old_status, "quantity": old_quantity, "storage_location": old_location}, new_value={"status": db_product.status, "quantity": db_product.quantity, "storage_location": db_product.storage_location}, comment=f"Sold {item['quantity']} items in sale {db_sale.id}. Price: {item['price']}")

    db.commit()
    db.refresh(db_sale)
    
    log_audit(db, "sale", db_sale.id, "create", new_value={"total_amount": sale.total_amount, "payment_method": sale.payment_method})
    db.commit()
    
    return db_sale

@router.get("/{sale_id}", response_model=schemas.Sale)
def get_sale(sale_id: int, db: Session = Depends(get_db)):
    db_sale = db.query(models.Sale).filter(models.Sale.id == sale_id).first()
    if not db_sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    return db_sale

@router.post("/{sale_id}/cancel", response_model=schemas.Sale)
def cancel_sale(sale_id: int, cancel_data: schemas.SaleCancel, db: Session = Depends(get_db)):
    db_sale = db.query(models.Sale).filter(models.Sale.id == sale_id).first()
    if not db_sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    if db_sale.status in ["canceled", "cancelled", "superseded"]:
        raise HTTPException(status_code=409, detail=f"Sale cannot be canceled (status: {db_sale.status})")
        
    db_sale.status = "canceled"
    db_sale.cancelled_at = datetime.utcnow()
    db_sale.cancel_reason = cancel_data.reason
    db_sale.canceled_by = cancel_data.canceled_by or "Администратор"
    
    sale_items = db.query(models.SaleItem).filter(models.SaleItem.sale_id == sale_id).all()
    for item in sale_items:
        db_product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if db_product:
            old_quantity = db_product.quantity or 0
            db_product.quantity = old_quantity + item.quantity
            
            mov = models.StockMovement(
                product_id=db_product.id,
                movement_type="sale_cancel",
                quantity_delta=item.quantity,
                old_quantity=old_quantity,
                new_quantity=db_product.quantity,
                reason="sale_cancel",
                comment=f"Sale {db_sale.id} canceled"
            )
            db.add(mov)

            old_status = db_product.status
            old_location = db_product.storage_location
            if db_product.status == "sold" and db_product.quantity > 0:
                db_product.status = "in_stock"
                if db_product.storage_location == "archive":
                    db_product.storage_location = "store"
                
            log_product_event(db, db_product.id, "sale_canceled", old_value={"status": old_status, "quantity": old_quantity, "storage_location": old_location}, new_value={"status": db_product.status, "quantity": db_product.quantity, "storage_location": db_product.storage_location}, comment=f"Sale {sale_id} canceled: {cancel_data.reason}")
            
    log_audit(db, "sale", db_sale.id, "cancel", new_value={"status": "canceled", "reason": cancel_data.reason, "canceled_by": db_sale.canceled_by})
    db.commit()
    db.refresh(db_sale)
    return db_sale

@router.post("/{sale_id}/reissue", response_model=schemas.Sale)
def reissue_sale(sale_id: int, reissue_data: schemas.SaleReissue, db: Session = Depends(get_db)):
    db_old_sale = db.query(models.Sale).filter(models.Sale.id == sale_id).first()
    if not db_old_sale:
        raise HTTPException(status_code=404, detail="Sale not found")
        
    if db_old_sale.status == "superseded" or db_old_sale.superseded_by_sale_id is not None or db_old_sale.replaced_by_sale_id is not None:
        raise HTTPException(status_code=409, detail="Original sale was already superseded")
        
    if db_old_sale.status not in ["canceled", "cancelled"]:
        raise HTTPException(status_code=400, detail="Only canceled sales can be reissued")
        
    if reissue_data.payment_method not in VALID_PAYMENT_METHODS:
        raise HTTPException(status_code=400, detail=f"Invalid payment method. Allowed: {', '.join(VALID_PAYMENT_METHODS)}")
        
    if not reissue_data.items:
        raise HTTPException(status_code=400, detail="Sale must contain at least one item")

    # Validate items before processing
    product_ids = set()
    for item in reissue_data.items:
        if item.quantity <= 0:
            raise HTTPException(status_code=400, detail="Item quantity must be > 0")
        if item.price < 0:
            raise HTTPException(status_code=400, detail="Item price must be >= 0")
        if item.product_id in product_ids:
            raise HTTPException(status_code=400, detail=f"Duplicate product_id {item.product_id} in sale")
        product_ids.add(item.product_id)
        
        db_product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not db_product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        if db_product.status not in ["in_stock", "reserved"]:
            raise HTTPException(status_code=400, detail=f"Cannot sell product {item.product_id} in status '{db_product.status}'")
        if db_product.storage_location != "store":
            raise HTTPException(status_code=400, detail=f"Product {item.product_id} must be in 'store' location to be sold")
        if (db_product.quantity or 0) < item.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient quantity for product {item.product_id}. Available: {db_product.quantity or 0}")

    total_amount = sum(item.price * item.quantity for item in reissue_data.items)

    new_sale = models.Sale(
        customer_id=db_old_sale.customer_id,
        total_amount=total_amount,
        payment_method=reissue_data.payment_method,
        comment=f"Reissue of sale #{sale_id}",
        status="reissued",
        warranty_days=db_old_sale.warranty_days,
        warranty_enabled=db_old_sale.warranty_enabled,
        source_sale_id=sale_id,
        original_sale_id=sale_id,
        reissued_at=datetime.utcnow()
    )
    db.add(new_sale)
    db.commit()
    db.refresh(new_sale)
    
    db_old_sale.status = "superseded"
    db_old_sale.superseded_by_sale_id = new_sale.id
    db_old_sale.replaced_by_sale_id = new_sale.id
    
    for item in reissue_data.items:
        db_item = models.SaleItem(**item.model_dump(), sale_id=new_sale.id)
        db.add(db_item)
        
        db_product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        old_q = db_product.quantity or 0
        db_product.quantity = old_q - item.quantity
        
        mov = models.StockMovement(
            product_id=db_product.id,
            movement_type="sale_reissue_deduct",
            quantity_delta=-item.quantity,
            old_quantity=old_q,
            new_quantity=db_product.quantity,
            reason="sale_reissue_deduct",
            comment=f"Stock deduct for sale {new_sale.id} reissue"
        )
        db.add(mov)
        
        old_s = db_product.status
        old_loc = db_product.storage_location
        if db_product.quantity == 0:
            db_product.status = "sold"
            db_product.storage_location = "archive"
            
        log_product_event(db, db_product.id, "sale_reissue_deduct", old_value={"status": old_s, "quantity": old_q, "storage_location": old_loc}, new_value={"status": db_product.status, "quantity": db_product.quantity, "storage_location": db_product.storage_location}, comment=f"Deducted for sale {new_sale.id}")

    log_audit(db, "sale", db_old_sale.id, "superseded", old_value={"status": "canceled"}, new_value={"status": "superseded", "superseded_by_sale_id": new_sale.id})
    log_audit(db, "sale", new_sale.id, "reissued", new_value={"status": "reissued", "source_sale_id": sale_id})
    db.commit()
    db.refresh(new_sale)
    return new_sale


@router.post("/{sale_id}/correct", response_model=schemas.Sale)
def correct_sale(sale_id: int, correct_data: schemas.SaleCorrect, db: Session = Depends(get_db)):
    db_sale = db.query(models.Sale).filter(models.Sale.id == sale_id).first()
    if not db_sale:
        raise HTTPException(status_code=404, detail="Sale not found")

    # Section 4: Primary editable state: completed or reissued sale.
    # Do not allow direct correction of canceled or superseded sales.
    if db_sale.status in ["canceled", "cancelled", "superseded"]:
        raise HTTPException(status_code=400, detail=f"Sale in status '{db_sale.status}' cannot be corrected")
    if db_sale.status not in ["completed", "reissued"]:
        raise HTTPException(status_code=400, detail=f"Sale in status '{db_sale.status}' cannot be corrected")

    # Validate payment method if provided
    if correct_data.payment_method:
        if correct_data.payment_method not in VALID_PAYMENT_METHODS:
            raise HTTPException(status_code=400, detail=f"Invalid payment method. Allowed: {', '.join(VALID_PAYMENT_METHODS)}")

    if not correct_data.items:
        raise HTTPException(status_code=400, detail="Sale must contain at least one item")

    # Validate items and check duplicate product_id
    seen_pids = set()
    for item in correct_data.items:
        if item.quantity <= 0:
            raise HTTPException(status_code=400, detail="Item quantity must be > 0")
        if item.price < 0:
            raise HTTPException(status_code=400, detail="Item price must be >= 0")
        if item.product_id is not None:
            if item.product_id in seen_pids:
                raise HTTPException(status_code=400, detail=f"Duplicate product_id {item.product_id} in sale items")
            seen_pids.add(item.product_id)

    # 1. Capture BEFORE snapshot
    old_items = db.query(models.SaleItem).filter(models.SaleItem.sale_id == sale_id).all()
    before_snapshot = {
        "total_amount": db_sale.total_amount,
        "payment_method": db_sale.payment_method,
        "items": [
            {
                "product_id": it.product_id,
                "title": it.title,
                "price": it.price,
                "quantity": it.quantity
            }
            for it in old_items
        ]
    }

    # For repair-generated sales: ensure items remain service lines (no physical stock items)
    if db_sale.source_type == "repair":
        if any(item.product_id is not None for item in correct_data.items):
            raise HTTPException(
                status_code=400,
                detail="Продажа ремонта не может содержать складские товары"
            )

    # 2. Inventory delta validation
    old_quantities = {it.product_id: it.quantity for it in old_items if it.product_id is not None}
    new_quantities = {it.product_id: it.quantity for it in correct_data.items if it.product_id is not None}
    all_pids = set(old_quantities.keys()) | set(new_quantities.keys())

    for pid in all_pids:
        old_q = old_quantities.get(pid, 0)
        new_q = new_quantities.get(pid, 0)
        delta = new_q - old_q
        if delta > 0:
            db_product = db.query(models.Product).filter(models.Product.id == pid).first()
            if not db_product:
                raise HTTPException(status_code=404, detail=f"Product {pid} not found")
            if old_q == 0:
                if db_product.status not in ["in_stock", "reserved"]:
                    raise HTTPException(status_code=400, detail=f"Cannot add product {pid} in status '{db_product.status}'")
                if db_product.storage_location != "store":
                    raise HTTPException(status_code=400, detail=f"Product {pid} must be in 'store' location to be sold")
            if (db_product.quantity or 0) < delta:
                raise HTTPException(
                    status_code=400,
                    detail=f"Недостаточно товара '{db_product.title}' на складе (требуется {delta}, доступно {db_product.quantity or 0})"
                )

    # 3. Apply inventory reconciliation
    for pid in all_pids:
        old_q = old_quantities.get(pid, 0)
        new_q = new_quantities.get(pid, 0)
        delta = new_q - old_q
        db_product = db.query(models.Product).filter(models.Product.id == pid).first()
        if not db_product:
            continue

        prod_old_qty = db_product.quantity or 0
        prod_old_status = db_product.status
        prod_old_loc = db_product.storage_location

        if delta > 0:
            # Deduct additional stock
            db_product.quantity = prod_old_qty - delta
            mov = models.StockMovement(
                product_id=db_product.id,
                movement_type="sale_correction_deduct",
                quantity_delta=-delta,
                old_quantity=prod_old_qty,
                new_quantity=db_product.quantity,
                reason="sale_correction_deduct",
                comment=f"Sale {sale_id} correction: added {delta} pcs"
            )
            db.add(mov)
            if db_product.quantity == 0:
                db_product.status = "sold"
                db_product.storage_location = "archive"
            log_product_event(
                db, db_product.id, "sale_correction_deduct",
                old_value={"status": prod_old_status, "quantity": prod_old_qty, "storage_location": prod_old_loc},
                new_value={"status": db_product.status, "quantity": db_product.quantity, "storage_location": db_product.storage_location},
                comment=f"Deducted {delta} for sale {sale_id} correction"
            )
        elif delta < 0:
            # Return stock
            return_qty = -delta
            db_product.quantity = prod_old_qty + return_qty
            mov = models.StockMovement(
                product_id=db_product.id,
                movement_type="sale_correction_return",
                quantity_delta=return_qty,
                old_quantity=prod_old_qty,
                new_quantity=db_product.quantity,
                reason="sale_correction_return",
                comment=f"Sale {sale_id} correction: returned {return_qty} pcs"
            )
            db.add(mov)
            if db_product.status == "sold" and db_product.quantity > 0:
                db_product.status = "in_stock"
                if db_product.storage_location == "archive":
                    db_product.storage_location = "store"
            log_product_event(
                db, db_product.id, "sale_correction_return",
                old_value={"status": prod_old_status, "quantity": prod_old_qty, "storage_location": prod_old_loc},
                new_value={"status": db_product.status, "quantity": db_product.quantity, "storage_location": db_product.storage_location},
                comment=f"Returned {return_qty} for sale {sale_id} correction"
            )

    # 4. Reconcile Avito tasks for removed products
    removed_pids = [pid for pid in all_pids if new_quantities.get(pid, 0) == 0 and old_quantities.get(pid, 0) > 0]
    for rpid in removed_pids:
        tasks_to_cancel = db.query(models.AvitoPostSaleTask).filter(
            models.AvitoPostSaleTask.sale_id == sale_id,
            models.AvitoPostSaleTask.product_id == rpid,
            models.AvitoPostSaleTask.status.in_(["suggested", "queued", "manual_required"])
        ).all()
        for t in tasks_to_cancel:
            t.status = "canceled"

    # 5. Replace items and recalculate total
    for it in old_items:
        db.delete(it)

    new_total = 0.0
    saved_new_items = []
    for item in correct_data.items:
        line_total = item.price * item.quantity
        new_total += line_total
        title = item.title
        if not title and item.product_id:
            p = db.query(models.Product).filter(models.Product.id == item.product_id).first()
            if p:
                title = p.title
        db_item = models.SaleItem(
            sale_id=sale_id,
            product_id=item.product_id,
            title=title or (f"Товар #{item.product_id}" if item.product_id else "Позиция"),
            price=item.price,
            quantity=item.quantity
        )
        db.add(db_item)
        saved_new_items.append({
            "product_id": item.product_id,
            "title": db_item.title,
            "price": item.price,
            "quantity": item.quantity
        })

    old_payment_method = db_sale.payment_method
    new_payment_method = correct_data.payment_method if correct_data.payment_method else old_payment_method
    db_sale.payment_method = new_payment_method
    db_sale.total_amount = new_total
    db_sale.revision_count = (db_sale.revision_count or 0) + 1

    # 6. Capture AFTER snapshot & human-readable diff
    after_snapshot = {
        "total_amount": new_total,
        "payment_method": new_payment_method,
        "items": saved_new_items
    }

    human_bullets = []
    payment_diff = None
    if old_payment_method != new_payment_method:
        old_label = PAYMENT_METHODS_LABELS.get(old_payment_method, old_payment_method)
        new_label = PAYMENT_METHODS_LABELS.get(new_payment_method, new_payment_method)
        human_bullets.append(f"• Способ оплаты: {old_label} -> {new_label}")
        payment_diff = {"old": old_payment_method, "new": new_payment_method}

    amount_diff = None
    if before_snapshot["total_amount"] != new_total:
        human_bullets.append(f"• Итог: {before_snapshot['total_amount']:,.0f} ₽ -> {new_total:,.0f} ₽".replace(",", " "))
        amount_diff = {"old": before_snapshot["total_amount"], "new": new_total}

    items_removed = []
    for it in before_snapshot["items"]:
        pid = it.get("product_id")
        matching = [n for n in after_snapshot["items"] if n.get("product_id") == pid] if pid else []
        if not matching:
            items_removed.append(it)
            human_bullets.append(f"• Удалён товар: {it.get('title')}")

    items_added = []
    for n in after_snapshot["items"]:
        pid = n.get("product_id")
        matching = [it for it in before_snapshot["items"] if it.get("product_id") == pid] if pid else []
        if not matching:
            items_added.append(n)
            human_bullets.append(f"• Добавлен товар: {n.get('title')}")

    items_modified = []
    for n in after_snapshot["items"]:
        pid = n.get("product_id")
        if pid:
            matching = [it for it in before_snapshot["items"] if it.get("product_id") == pid]
            if matching:
                old_it = matching[0]
                diff_it = {}
                if old_it["price"] != n["price"]:
                    diff_it["old_price"] = old_it["price"]
                    diff_it["new_price"] = n["price"]
                    human_bullets.append(f"• Изменена цена: {n.get('title')} ({old_it['price']:,.0f} ₽ -> {n['price']:,.0f} ₽)".replace(",", " "))
                if old_it["quantity"] != n["quantity"]:
                    diff_it["old_quantity"] = old_it["quantity"]
                    diff_it["new_quantity"] = n["quantity"]
                    human_bullets.append(f"• Изменено количество: {n.get('title')} ({old_it['quantity']} шт. -> {n['quantity']} шт.)")
                if diff_it:
                    diff_it["product_id"] = pid
                    diff_it["title"] = n.get("title")
                    items_modified.append(diff_it)

    structured_diff = {
        "payment_method": payment_diff,
        "total_amount": amount_diff,
        "items_removed": items_removed,
        "items_added": items_added,
        "items_modified": items_modified,
        "human_bullets": human_bullets
    }

    # 7. Append immutable revision record
    revision = models.SaleRevision(
        sale_id=sale_id,
        revision_no=db_sale.revision_count,
        changed_by=correct_data.changed_by or "Администратор",
        comment=correct_data.comment,
        before_snapshot=json.dumps(before_snapshot, ensure_ascii=False),
        after_snapshot=json.dumps(after_snapshot, ensure_ascii=False),
        structured_diff=json.dumps(structured_diff, ensure_ascii=False)
    )
    db.add(revision)

    log_audit(
        db, "sale", db_sale.id, "correct",
        old_value=before_snapshot,
        new_value=after_snapshot,
        comment=correct_data.comment
    )

    # Stage 11B Compatibility: If linked to a repair, synchronize RepairOrder financials and record history
    if db_sale.source_type == "repair" and db_sale.source_id:
        linked_repair = db.query(models.RepairOrder).filter(models.RepairOrder.id == db_sale.source_id).first()
        if linked_repair:
            old_repair_amt = linked_repair.final_amount or linked_repair.price or 0.0
            linked_repair.final_amount = new_total
            linked_repair.price = new_total
            if new_payment_method:
                linked_repair.payment_method = new_payment_method
            linked_repair.updated_at = datetime.utcnow()

            repair_hist = models.RepairStatusHistory(
                repair_id=linked_repair.id,
                old_status=linked_repair.status,
                new_status=linked_repair.status,
                comment=f"Скорректирована связанная продажа №{db_sale.id} (ревизия №{db_sale.revision_count}): сумма {old_repair_amt:,.0f} ₽ -> {new_total:,.0f} ₽. Причина: {correct_data.comment}".replace(",", " "),
                changed_by=correct_data.changed_by or "Администратор",
                changed_at=datetime.utcnow()
            )
            db.add(repair_hist)
            log_audit(
                db,
                "repair_order",
                linked_repair.id,
                "repair.sale_corrected",
                old_value={"final_amount": old_repair_amt, "payment_method": old_payment_method},
                new_value={"final_amount": new_total, "payment_method": new_payment_method, "sale_id": db_sale.id}
            )

    db.commit()
    db.refresh(db_sale)
    return db_sale


@router.get("/{sale_id}/revisions", response_model=schemas.SaleRevisionListResponse)
def get_sale_revisions(sale_id: int, db: Session = Depends(get_db)):
    db_sale = db.query(models.Sale).filter(models.Sale.id == sale_id).first()
    if not db_sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    revisions = db.query(models.SaleRevision).filter(
        models.SaleRevision.sale_id == sale_id
    ).order_by(models.SaleRevision.revision_no.asc()).all()
    return {
        "items": revisions,
        "total": len(revisions)
    }


def _hard_delete_sale(db: Session, db_sale: models.Sale) -> int:
    sale_id = db_sale.id

    # 1. Restore product inventory if the sale was active (not canceled)
    if db_sale.status not in ["canceled", "cancelled"]:
        sale_items = db.query(models.SaleItem).filter(models.SaleItem.sale_id == sale_id).all()
        for item in sale_items:
            if item.product_id:
                db_product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
                if db_product:
                    old_quantity = db_product.quantity or 0
                    db_product.quantity = old_quantity + item.quantity
                    old_status = db_product.status
                    old_location = db_product.storage_location
                    if db_product.status == "sold" and db_product.quantity > 0:
                        db_product.status = "in_stock"
                        if db_product.storage_location == "archive":
                            db_product.storage_location = "store"

                    log_product_event(
                        db,
                        db_product.id,
                        "sale_deleted",
                        old_value={"status": old_status, "quantity": old_quantity, "storage_location": old_location},
                        new_value={"status": db_product.status, "quantity": db_product.quantity, "storage_location": db_product.storage_location},
                        comment=f"Восстановлен остаток товара после безвозвратного удаления продажи #{sale_id}"
                    )

    # 2. Delete associated stock movements
    stock_movs = db.query(models.StockMovement).filter(
        models.StockMovement.comment.like(f"%Sale {sale_id}%")
    ).all()
    for sm in stock_movs:
        db.delete(sm)

    # 3. Delete avito post sale tasks
    avito_tasks = db.query(models.AvitoPostSaleTask).filter(models.AvitoPostSaleTask.sale_id == sale_id).all()
    for task in avito_tasks:
        db.delete(task)

    # 4. Delete sale revisions
    revisions = db.query(models.SaleRevision).filter(models.SaleRevision.sale_id == sale_id).all()
    for rev in revisions:
        db.delete(rev)

    # 5. Decouple linked repair orders
    repairs = db.query(models.RepairOrder).filter(models.RepairOrder.sale_id == sale_id).all()
    for rep in repairs:
        rep.sale_id = None
        rep.final_amount = None
        rep.payment_method = None
        rep.warranty_days = None

    if db_sale.source_type == "repair" and db_sale.source_id:
        rep_by_source = db.query(models.RepairOrder).filter(models.RepairOrder.id == db_sale.source_id).first()
        if rep_by_source and rep_by_source.sale_id == sale_id:
            rep_by_source.sale_id = None
            rep_by_source.final_amount = None
            rep_by_source.payment_method = None
            rep_by_source.warranty_days = None

    # 6. Decouple other sales referencing this sale
    related_sales = db.query(models.Sale).filter(
        or_(
            models.Sale.original_sale_id == sale_id,
            models.Sale.replaced_by_sale_id == sale_id,
            models.Sale.source_sale_id == sale_id,
            models.Sale.superseded_by_sale_id == sale_id
        )
    ).all()
    for rs in related_sales:
        if rs.original_sale_id == sale_id:
            rs.original_sale_id = None
        if rs.replaced_by_sale_id == sale_id:
            rs.replaced_by_sale_id = None
        if rs.source_sale_id == sale_id:
            rs.source_sale_id = None
        if rs.superseded_by_sale_id == sale_id:
            rs.superseded_by_sale_id = None

    # 7. Delete sale items
    items = db.query(models.SaleItem).filter(models.SaleItem.sale_id == sale_id).all()
    for it in items:
        db.delete(it)

    # 8. Log audit before deletion
    log_audit(
        db,
        "sale",
        sale_id,
        "hard_delete",
        old_value={"total_amount": db_sale.total_amount, "status": db_sale.status, "comment": db_sale.comment}
    )

    # 9. Delete sale
    db.delete(db_sale)
    return sale_id


@router.post("/bulk-delete", response_model=schemas.BulkDeleteResponse)
def bulk_delete_sales(req: schemas.SaleBulkDeleteRequest, db: Session = Depends(get_db)):
    deleted = []
    for s_id in req.sale_ids:
        db_sale = db.query(models.Sale).filter(models.Sale.id == s_id).first()
        if db_sale:
            _hard_delete_sale(db, db_sale)
            deleted.append(s_id)
    db.commit()
    return {
        "status": "ok",
        "deleted_count": len(deleted),
        "deleted_ids": deleted
    }


@router.delete("/{sale_id}", response_model=schemas.BulkDeleteResponse)
def delete_sale(sale_id: int, db: Session = Depends(get_db)):
    db_sale = db.query(models.Sale).filter(models.Sale.id == sale_id).first()
    if not db_sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    _hard_delete_sale(db, db_sale)
    db.commit()
    return {
        "status": "ok",
        "deleted_count": 1,
        "deleted_ids": [sale_id]
    }


