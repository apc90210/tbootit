import json
import urllib.parse
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app import models, schemas

router = APIRouter()

OFFICIAL_API_AVAILABLE = False


def log_audit(db: Session, entity_type: str, entity_id: int, action: str, old_value: Any = None, new_value: Any = None):
    log = models.AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        old_value=json.dumps(old_value, ensure_ascii=False) if old_value else None,
        new_value=json.dumps(new_value, ensure_ascii=False) if new_value else None
    )
    db.add(log)


def _canonical_avito_url(listing_url: Optional[str], avito_listing_id: str) -> str:
    canonical = f"https://www.avito.ru/{avito_listing_id}"
    if listing_url:
        try:
            parsed = urllib.parse.urlparse(listing_url)
            host = (parsed.netloc or "").lower()
            if host in ["www.avito.ru", "avito.ru", "m.avito.ru"]:
                if str(avito_listing_id) in parsed.path or str(avito_listing_id) in parsed.query:
                    return listing_url
        except Exception:
            pass
    return canonical


def _enrich_task(task: models.AvitoPostSaleTask, db: Session) -> Dict[str, Any]:
    prod = db.query(models.Product).filter(models.Product.id == task.product_id).first()
    canonical_url = _canonical_avito_url(task.listing_url, task.avito_listing_id)
    return {
        "id": task.id,
        "sale_id": task.sale_id,
        "product_id": task.product_id,
        "product_title": prod.title if prod else f"Товар #{task.product_id}",
        "product_sku": prod.sku if prod else None,
        "external_listing_id": task.external_listing_id,
        "avito_listing_id": task.avito_listing_id,
        "listing_url": canonical_url,
        "status": task.status,
        "action": task.action,
        "requested_by": task.requested_by,
        "requested_at": task.requested_at.isoformat() if task.requested_at else None,
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "finished_at": task.finished_at.isoformat() if task.finished_at else None,
        "attempt_count": task.attempt_count,
        "last_error": task.last_error,
        "execution_mode": task.execution_mode,
        "result_metadata": task.result_metadata,
    }


@router.get("/api/sales/{sale_id}/avito-tasks")
def get_sale_avito_tasks(sale_id: int, db: Session = Depends(get_db)):
    """
    Inspects sale items. If any product is linked to an active Avito listing,
    creates (if not exists) or retrieves persistent AvitoPostSaleTask records in 'suggested' status.
    Idempotent: unique on (sale_id, product_id, avito_listing_id, action).
    """
    sale = db.query(models.Sale).filter(models.Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail=f"Sale #{sale_id} not found")

    items = db.query(models.SaleItem).filter(models.SaleItem.sale_id == sale_id).all()
    tasks = []

    for item in items:
        if not item.product_id:
            continue

        # Look up active Avito listings for this product
        ext_listings = db.query(models.ProductExternalListing).filter(
            models.ProductExternalListing.product_id == item.product_id,
            models.ProductExternalListing.marketplace == "avito",
            models.ProductExternalListing.remote_status.in_(["active", "published"])
        ).all()

        for ext in ext_listings:
            # Check if task already exists
            existing_task = db.query(models.AvitoPostSaleTask).filter(
                models.AvitoPostSaleTask.sale_id == sale_id,
                models.AvitoPostSaleTask.product_id == item.product_id,
                models.AvitoPostSaleTask.avito_listing_id == str(ext.external_item_id),
                models.AvitoPostSaleTask.action == "deactivate"
            ).first()

            if not existing_task:
                canonical_url = _canonical_avito_url(ext.external_url, str(ext.external_item_id))
                new_task = models.AvitoPostSaleTask(
                    sale_id=sale_id,
                    product_id=item.product_id,
                    external_listing_id=ext.id,
                    avito_listing_id=str(ext.external_item_id),
                    listing_url=canonical_url,
                    status="suggested",
                    action="deactivate",
                    execution_mode="manual",
                    attempt_count=0
                )
                db.add(new_task)
                db.commit()
                db.refresh(new_task)
                tasks.append(_enrich_task(new_task, db))
            else:
                tasks.append(_enrich_task(existing_task, db))

    # Also load any already created tasks for this sale that may be in other states (queued, processing, success, etc.)
    all_sale_tasks = db.query(models.AvitoPostSaleTask).filter(
        models.AvitoPostSaleTask.sale_id == sale_id
    ).all()

    existing_task_ids = {t["id"] for t in tasks}
    for t in all_sale_tasks:
        if t.id not in existing_task_ids:
            tasks.append(_enrich_task(t, db))

    # Inspect all external listings for products in this sale
    product_ids = [item.product_id for item in items if item.product_id]
    all_ext_listings = []
    if product_ids:
        all_ext_listings = db.query(models.ProductExternalListing).filter(
            models.ProductExternalListing.product_id.in_(product_ids),
            models.ProductExternalListing.marketplace == "avito"
        ).all()

    has_linked = len(all_ext_listings) > 0
    all_archived = has_linked and all(
        ext.remote_status in ["archived", "inactive", "closed"] for ext in all_ext_listings
    )
    if not all_archived and tasks and all(t["status"] == "success" for t in tasks):
        all_archived = True

    return {
        "sale_id": sale_id,
        "count": len(tasks),
        "tasks": tasks,
        "has_linked_listings": has_linked,
        "all_archived": all_archived
    }


@router.post("/api/sales/{sale_id}/avito-deactivate")
def queue_sale_avito_deactivation(
    sale_id: int,
    payload: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
):
    """
    Enqueues post-sale Avito deactivation task(s) for a sale.
    Transitions 'suggested' or 'failed' tasks to 'queued'.
    """
    sale = db.query(models.Sale).filter(models.Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail=f"Sale #{sale_id} not found")

    # First ensure any active listings have tasks created
    get_sale_avito_tasks(sale_id, db)

    tasks = db.query(models.AvitoPostSaleTask).filter(
        models.AvitoPostSaleTask.sale_id == sale_id
    ).all()

    target_task_ids = None
    if payload and "task_ids" in payload:
        target_task_ids = set(payload["task_ids"])

    updated = []
    for t in tasks:
        if target_task_ids is not None and t.id not in target_task_ids:
            continue
        if t.status in ["suggested", "failed", "manual_required"]:
            t.status = "queued"
            t.last_error = None
            db.add(t)
            updated.append(t)

    db.commit()
    for t in updated:
        db.refresh(t)

    all_tasks = db.query(models.AvitoPostSaleTask).filter(
        models.AvitoPostSaleTask.sale_id == sale_id
    ).all()

    return {
        "sale_id": sale_id,
        "queued_count": len(updated),
        "tasks": [_enrich_task(t, db) for t in all_tasks]
    }


@router.get("/api/avito/post-sale-tasks")
def list_post_sale_tasks(
    status: Optional[str] = Query(None),
    limit: int = Query(50),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    """List persistent post-sale deactivation tasks."""
    query = db.query(models.AvitoPostSaleTask)
    if status and status.strip():
        query = query.filter(models.AvitoPostSaleTask.status == status.strip())

    query = query.order_by(desc(models.AvitoPostSaleTask.requested_at))
    total = query.count()
    items = query.offset(offset).limit(limit).all()

    return {
        "items": [_enrich_task(t, db) for t in items],
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.post("/api/avito/post-sale-tasks/{task_id}/queue")
def queue_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.AvitoPostSaleTask).filter(models.AvitoPostSaleTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = "queued"
    task.last_error = None
    db.commit()
    db.refresh(task)
    return _enrich_task(task, db)


@router.post("/api/avito/post-sale-tasks/{task_id}/retry")
def retry_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.AvitoPostSaleTask).filter(models.AvitoPostSaleTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = "queued"
    task.last_error = None
    db.commit()
    db.refresh(task)
    return _enrich_task(task, db)


@router.post("/api/avito/post-sale-tasks/{task_id}/cancel")
def cancel_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.AvitoPostSaleTask).filter(models.AvitoPostSaleTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = "canceled"
    db.commit()
    db.refresh(task)
    return _enrich_task(task, db)


@router.post("/api/avito/post-sale-tasks/{task_id}/manual-confirm")
def manual_confirm_task(task_id: int, db: Session = Depends(get_db)):
    """
    Operator explicitly confirms: 'Я снял объявление'.
    1. Task transitioned to 'success'
    2. execution_mode set to 'manual'
    3. ProductExternalListing.remote_status updated to 'archived'
    4. Audit event written
    """
    task = db.query(models.AvitoPostSaleTask).filter(models.AvitoPostSaleTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    now = datetime.utcnow()
    task.status = "success"
    task.execution_mode = "manual"
    task.finished_at = now
    task.last_error = None
    task.result_metadata = json.dumps({"confirmed_by": "operator_manual", "confirmed_at": now.isoformat()}, ensure_ascii=False)

    ext = None
    if task.external_listing_id:
        ext = db.query(models.ProductExternalListing).filter(
            models.ProductExternalListing.id == task.external_listing_id
        ).first()
    if not ext:
        ext = db.query(models.ProductExternalListing).filter(
            models.ProductExternalListing.marketplace == "avito",
            models.ProductExternalListing.external_item_id == task.avito_listing_id
        ).first()
    if ext:
        ext.remote_status = "archived"
        ext.sync_state = "synced"
        db.add(ext)

    log_audit(
        db,
        entity_type="avito_post_sale_task",
        entity_id=task.id,
        action="avito_listing_deactivated_after_sale",
        new_value={
            "task_id": task.id,
            "sale_id": task.sale_id,
            "product_id": task.product_id,
            "avito_listing_id": task.avito_listing_id,
            "execution_mode": "manual",
            "confirmation_method": "operator_click",
            "timestamp": now.isoformat()
        }
    )

    db.commit()
    db.refresh(task)
    return _enrich_task(task, db)


@router.post("/api/avito/post-sale-tasks/{task_id}/mark-opened")
def mark_task_opened(task_id: int, db: Session = Depends(get_db)):
    """
    Operator chose to open Avito for manual removal.
    Transitions task to 'manual_required' without marking success.
    """
    task = db.query(models.AvitoPostSaleTask).filter(models.AvitoPostSaleTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status in ["suggested", "queued"]:
        task.status = "manual_required"
        task.execution_mode = "manual"
        db.commit()
        db.refresh(task)
    return _enrich_task(task, db)


@router.post("/api/sales/{sale_id}/avito-manual-confirm")
def manual_confirm_sale_tasks(sale_id: int, db: Session = Depends(get_db)):
    """
    Confirms manual deactivation for all tasks of a sale.
    """
    tasks = db.query(models.AvitoPostSaleTask).filter(
        models.AvitoPostSaleTask.sale_id == sale_id
    ).all()
    confirmed = []
    for t in tasks:
        if t.status in ["suggested", "queued", "manual_required", "failed"]:
            manual_confirm_task(t.id, db)
            confirmed.append(t)
    return {"sale_id": sale_id, "confirmed_count": len(confirmed)}


@router.post("/api/sales/{sale_id}/avito-manual-open")
def manual_open_sale_tasks(sale_id: int, db: Session = Depends(get_db)):
    """
    Operator clicked [Снять с Avito вручную].
    Transitions tasks for this sale to 'manual_required'.
    Crucial: does NOT mark success!
    """
    tasks = db.query(models.AvitoPostSaleTask).filter(
        models.AvitoPostSaleTask.sale_id == sale_id
    ).all()
    opened_count = 0
    for t in tasks:
        if t.status in ["suggested", "queued"]:
            t.status = "manual_required"
            t.execution_mode = "manual"
            db.add(t)
            opened_count += 1
    db.commit()
    return {"sale_id": sale_id, "opened_count": opened_count}


@router.post("/api/sales/{sale_id}/avito-dismiss")
def dismiss_sale_tasks(sale_id: int, db: Session = Depends(get_db)):
    """
    Operator clicked 'Не снимать'.
    Transitions suggested tasks to 'canceled'. Does NOT mutate listing!
    """
    tasks = db.query(models.AvitoPostSaleTask).filter(
        models.AvitoPostSaleTask.sale_id == sale_id
    ).all()
    canceled_count = 0
    for t in tasks:
        if t.status in ["suggested", "queued"]:
            t.status = "canceled"
            db.add(t)
            canceled_count += 1
    db.commit()
    return {"sale_id": sale_id, "canceled_count": canceled_count}



@router.get("/api/avito/post-sale-tasks/next")
def get_next_queued_task(db: Session = Depends(get_db)):
    """
    Picks the oldest 'queued' task, transitions it to 'processing',
    increments attempt_count, sets started_at, and returns payload.
    """
    task = db.query(models.AvitoPostSaleTask).filter(
        models.AvitoPostSaleTask.status == "queued"
    ).order_by(models.AvitoPostSaleTask.requested_at.asc()).first()

    if not task:
        return {"task": None}

    task.status = "processing"
    task.started_at = datetime.utcnow()
    task.attempt_count = (task.attempt_count or 0) + 1
    db.commit()
    db.refresh(task)

    return {
        "task": {
            "task_id": task.id,
            "action": task.action,
            "sale_id": task.sale_id,
            "product_id": task.product_id,
            "avito_listing_id": task.avito_listing_id,
            "listing_url": task.listing_url,
            "attempt_count": task.attempt_count
        }
    }


@router.post("/api/avito/post-sale-tasks/{task_id}/started")
def mark_task_started(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.AvitoPostSaleTask).filter(models.AvitoPostSaleTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = "processing"
    task.started_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    return _enrich_task(task, db)


@router.post("/api/avito/post-sale-tasks/{task_id}/success")
def mark_task_success(
    task_id: int,
    payload: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
):
    """
    Confirms external deactivation. Only on confirmed confirmation:
    1. Task transitioned to 'success'
    2. ProductExternalListing.remote_status updated to 'archived'
    3. Audit event written: avito_listing_deactivated_after_sale
    4. CRITICAL: Product inventory and completed sale are NEVER touched!
    """
    task = db.query(models.AvitoPostSaleTask).filter(models.AvitoPostSaleTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    now = datetime.utcnow()
    task.status = "success"
    task.finished_at = now
    if payload:
        task.result_metadata = json.dumps(payload, ensure_ascii=False)

    # Update canonical external listing status
    ext = None
    if task.external_listing_id:
        ext = db.query(models.ProductExternalListing).filter(
            models.ProductExternalListing.id == task.external_listing_id
        ).first()

    if not ext:
        ext = db.query(models.ProductExternalListing).filter(
            models.ProductExternalListing.marketplace == "avito",
            models.ProductExternalListing.external_item_id == task.avito_listing_id
        ).first()

    if ext:
        ext.remote_status = "archived"
        ext.sync_state = "synced"
        db.add(ext)

    # Write audit event: avito_listing_deactivated_after_sale
    log_audit(
        db,
        entity_type="avito_post_sale_task",
        entity_id=task.id,
        action="avito_listing_deactivated_after_sale",
        new_value={
            "task_id": task.id,
            "sale_id": task.sale_id,
            "product_id": task.product_id,
            "avito_listing_id": task.avito_listing_id,
            "execution_mode": task.execution_mode,
            "timestamp": now.isoformat()
        }
    )

    db.commit()
    db.refresh(task)
    return _enrich_task(task, db)


@router.post("/api/avito/post-sale-tasks/{task_id}/failed")
def mark_task_failed(
    task_id: int,
    payload: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
):
    """
    Records task failure. If attempt_count >= 3 or not can_retry:
    transitions to 'manual_required'. Else 'failed'.
    """
    task = db.query(models.AvitoPostSaleTask).filter(models.AvitoPostSaleTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    err_msg = "Ошибка выполнения задачи"
    can_retry = True
    if payload:
        err_msg = payload.get("error") or payload.get("message") or err_msg
        if "can_retry" in payload:
            can_retry = bool(payload["can_retry"])
        task.result_metadata = json.dumps(payload, ensure_ascii=False)

    task.last_error = str(err_msg)

    # Check retry limit: 3 attempts
    if (task.attempt_count or 0) >= 3 or not can_retry:
        task.status = "manual_required"
    else:
        task.status = "failed"

    db.commit()
    db.refresh(task)
    return _enrich_task(task, db)
