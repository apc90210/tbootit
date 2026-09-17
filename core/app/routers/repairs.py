from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc, text
from typing import Optional, List
from datetime import datetime, date, timedelta

from app.database import get_db
from app import models, schemas
from app.services.repair_number_service import generate_repair_number
from app.routers.customers import log_audit

router = APIRouter()

VALID_TRANSITIONS = {
    "received": ["diagnostics", "canceled"],
    "diagnostics": ["waiting_customer", "waiting_parts", "in_repair", "ready", "unrepairable", "canceled"],
    "waiting_customer": ["diagnostics", "waiting_parts", "in_repair", "unrepairable", "canceled"],
    "waiting_parts": ["waiting_customer", "in_repair", "unrepairable", "canceled"],
    "in_repair": ["waiting_customer", "waiting_parts", "ready", "unrepairable", "canceled"],
    "ready": ["in_repair", "issued"],
    "unrepairable": ["issued", "canceled"],
    "issued": [],
    "canceled": []
}

PAYMENT_METHODS_LABELS = {
    "cash": "Наличные",
    "card": "Безнал / карта",
    "bank_card": "Безнал / карта",
    "acquiring": "Безнал / карта",
    "transfer": "Перевод",
    "sbp": "СБП",
    "legal_entity_account": "Счёт юрлица",
    "mixed": "Смешанная оплата",
    "other": "Другое",
    "unspecified": "Не указано"
}

def enrich_repair_labels(db_repair: models.RepairOrder, db: Session = None) -> models.RepairOrder:
    if db_repair:
        setattr(db_repair, "status_label", schemas.REPAIR_STATUSES.get(db_repair.status, db_repair.status))
        setattr(db_repair, "priority_label", schemas.REPAIR_PRIORITIES.get(db_repair.priority, db_repair.priority))
        if db_repair.sale_id:
            setattr(db_repair, "linked_sale_id", db_repair.sale_id)
        elif db is not None:
            linked_sale = db.query(models.Sale).filter(
                models.Sale.source_type == "repair",
                models.Sale.source_id == db_repair.id
            ).first()
            if linked_sale:
                setattr(db_repair, "linked_sale_id", linked_sale.id)
                db_repair.sale_id = linked_sale.id
    return db_repair

@router.get("/options")
def get_repair_options():
    statuses_list = [{"value": k, "label": v} for k, v in schemas.REPAIR_STATUSES.items()]
    priorities_list = [{"value": k, "label": v} for k, v in schemas.REPAIR_PRIORITIES.items()]
    return {
        "statuses": statuses_list,
        "priorities": priorities_list,
        "device_types": schemas.REPAIR_DEVICE_TYPES,
        "default_diagnostic_fee": 500
    }

@router.post("/", response_model=schemas.RepairOrder, status_code=status.HTTP_201_CREATED)
def create_repair(repair_in: schemas.RepairOrderCreate, db: Session = Depends(get_db)):
    now = datetime.utcnow()
    number = generate_repair_number(db, accepted_at=now)

    payload = repair_in.model_dump()

    # Customer integration & snapshot logic
    cust_id = payload.get("customer_id")
    cust_phone = payload.get("customer_phone")
    cust_name = payload.get("customer_name")
    cust_email = payload.get("customer_email")

    if cust_id:
        existing_cust = db.query(models.Customer).filter(models.Customer.id == cust_id).first()
        if not existing_cust:
            raise HTTPException(status_code=404, detail="Указанный клиент не найден")
        if not cust_name: payload["customer_name"] = existing_cust.name
        if not cust_phone: payload["customer_phone"] = existing_cust.phone
        if not cust_email: payload["customer_email"] = existing_cust.email
    elif cust_phone and cust_phone.strip():
        clean_phone = cust_phone.strip()
        existing_cust = db.query(models.Customer).filter(models.Customer.phone == clean_phone).first()
        if existing_cust:
            payload["customer_id"] = existing_cust.id
            if not cust_name: payload["customer_name"] = existing_cust.name
            if not cust_email: payload["customer_email"] = existing_cust.email
        elif cust_name and cust_name.strip():
            new_cust = models.Customer(
                name=cust_name.strip(),
                phone=clean_phone,
                email=cust_email.strip() if cust_email else None
            )
            db.add(new_cust)
            db.flush()
            payload["customer_id"] = new_cust.id

    db_repair = models.RepairOrder(
        number=number,
        status="received",
        accepted_at=now,
        created_at=now,
        updated_at=now,
        **payload
    )

    db.add(db_repair)
    db.commit()
    db.refresh(db_repair)

    # Initial history entry
    hist = models.RepairStatusHistory(
        repair_id=db_repair.id,
        old_status=None,
        new_status="received",
        comment="Приём техники в ремонт",
        changed_at=now
    )
    db.add(hist)
    
    # Audit log entry
    log_audit(
        db,
        "repair_order",
        db_repair.id,
        "repair.created",
        new_value={
            "id": db_repair.id,
            "number": db_repair.number,
            "customer_name": db_repair.customer_name,
            "customer_phone": db_repair.customer_phone,
            "device_type": db_repair.device_type,
            "brand": db_repair.brand,
            "model": db_repair.model,
            "reported_issue": db_repair.reported_issue,
            "status": "received",
            "priority": db_repair.priority,
            "diagnostic_fee": db_repair.diagnostic_fee
        }
    )
    db.commit()
    db.refresh(db_repair)

    return enrich_repair_labels(db_repair)

@router.get("/", response_model=schemas.RepairListResponse)
def get_repairs(
    q: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    device_type: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    customer_phone: Optional[str] = Query(None),
    serial_number: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    sort: str = Query("accepted_at_desc"),
    db: Session = Depends(get_db)
):
    query = db.query(models.RepairOrder)

    if q and q.strip():
        term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                models.RepairOrder.number.ilike(term),
                models.RepairOrder.customer_name.ilike(term),
                models.RepairOrder.customer_phone.ilike(term),
                models.RepairOrder.device_type.ilike(term),
                models.RepairOrder.brand.ilike(term),
                models.RepairOrder.model.ilike(term),
                models.RepairOrder.serial_number.ilike(term),
                models.RepairOrder.reported_issue.ilike(term)
            )
        )

    if status and status.strip():
        query = query.filter(models.RepairOrder.status == status.strip())
    if priority and priority.strip():
        query = query.filter(models.RepairOrder.priority == priority.strip())
    if device_type and device_type.strip():
        query = query.filter(models.RepairOrder.device_type == device_type.strip())
    if assigned_to and assigned_to.strip():
        query = query.filter(models.RepairOrder.assigned_to.ilike(f"%{assigned_to.strip()}%"))
    if customer_phone and customer_phone.strip():
        query = query.filter(models.RepairOrder.customer_phone.ilike(f"%{customer_phone.strip()}%"))
    if serial_number and serial_number.strip():
        query = query.filter(models.RepairOrder.serial_number.ilike(f"%{serial_number.strip()}%"))

    if date_from and date_from.strip():
        try:
            df = datetime.fromisoformat(date_from.strip())
            query = query.filter(models.RepairOrder.accepted_at >= df)
        except Exception:
            pass

    if date_to and date_to.strip():
        try:
            dt_to = datetime.fromisoformat(date_to.strip())
            if len(date_to.strip()) <= 10:
                dt_to = dt_to.replace(hour=23, minute=59, second=59, microsecond=999999)
            query = query.filter(models.RepairOrder.accepted_at <= dt_to)
        except Exception:
            pass

    # Sorting
    if sort == "accepted_at_asc":
        query = query.order_by(asc(models.RepairOrder.accepted_at), asc(models.RepairOrder.id))
    elif sort == "created_at_desc":
        query = query.order_by(desc(models.RepairOrder.created_at), desc(models.RepairOrder.id))
    else:
        query = query.order_by(desc(models.RepairOrder.accepted_at), desc(models.RepairOrder.id))

    total = query.count()
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    enriched_items = [enrich_repair_labels(item) for item in items]
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    return {
        "items": enriched_items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }

@router.get("/by-number/{number}", response_model=schemas.RepairOrder)
def get_repair_by_number(number: str, db: Session = Depends(get_db)):
    db_repair = db.query(models.RepairOrder).filter(models.RepairOrder.number == number.strip()).first()
    if not db_repair:
        raise HTTPException(status_code=404, detail="Ремонтный заказ не найден")
    return enrich_repair_labels(db_repair)

@router.get("/{repair_id}", response_model=schemas.RepairOrder)
def get_repair(repair_id: int, db: Session = Depends(get_db)):
    db_repair = db.query(models.RepairOrder).filter(models.RepairOrder.id == repair_id).first()
    if not db_repair:
        raise HTTPException(status_code=404, detail="Ремонтный заказ не найден")
    return enrich_repair_labels(db_repair)

@router.get("/{repair_id}/history", response_model=List[schemas.RepairStatusHistorySchema])
def get_repair_history(repair_id: int, db: Session = Depends(get_db)):
    db_repair = db.query(models.RepairOrder).filter(models.RepairOrder.id == repair_id).first()
    if not db_repair:
        raise HTTPException(status_code=404, detail="Ремонтный заказ не найден")
    return db.query(models.RepairStatusHistory).filter(models.RepairStatusHistory.repair_id == repair_id).order_by(asc(models.RepairStatusHistory.changed_at)).all()

@router.patch("/{repair_id}", response_model=schemas.RepairOrder)
def update_repair(repair_id: int, repair_update: schemas.RepairOrderUpdate, db: Session = Depends(get_db)):
    db_repair = db.query(models.RepairOrder).filter(models.RepairOrder.id == repair_id).first()
    if not db_repair:
        raise HTTPException(status_code=404, detail="Ремонтный заказ не найден")

    # Protection for terminal closed repairs
    if db_repair.status in ["issued", "canceled"]:
        raise HTTPException(status_code=409, detail="Запрещено редактировать закрытый или отменённый ремонт")

    old_data = {
        "customer_name": db_repair.customer_name,
        "customer_phone": db_repair.customer_phone,
        "device_type": db_repair.device_type,
        "brand": db_repair.brand,
        "model": db_repair.model,
        "reported_issue": db_repair.reported_issue,
        "diagnostic_fee": db_repair.diagnostic_fee,
        "diagnosis_text": db_repair.diagnosis_text,
        "planned_works_text": db_repair.planned_works_text,
        "planned_parts_text": db_repair.planned_parts_text,
        "estimated_repair_amount": db_repair.estimated_repair_amount
    }

    update_dict = repair_update.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(db_repair, key, value)

    now = datetime.utcnow()
    db_repair.updated_at = now

    db.commit()
    db.refresh(db_repair)

    log_audit(
        db,
        "repair_order",
        db_repair.id,
        "repair.updated",
        old_value=old_data,
        new_value=update_dict
    )
    db.commit()

    return enrich_repair_labels(db_repair)

@router.post("/{repair_id}/status", response_model=schemas.RepairOrder)
def update_repair_status(repair_id: int, status_in: schemas.RepairOrderStatusUpdate, db: Session = Depends(get_db)):
    db_repair = db.query(models.RepairOrder).filter(models.RepairOrder.id == repair_id).first()
    if not db_repair:
        raise HTTPException(status_code=404, detail="Ремонтный заказ не найден")

    current_status = db_repair.status
    new_status = status_in.status

    if new_status not in schemas.REPAIR_STATUSES:
        raise HTTPException(status_code=400, detail=f"Неизвестный статус ремонта '{new_status}'")

    if current_status == "issued" and new_status != "issued":
        raise HTTPException(
            status_code=409,
            detail=f"Ремонт уже выдан (связанная продажа №{db_repair.sale_id or '?'}). Случайный откат статуса выданного ремонта заблокирован во избежание расхождений в учёте и отчётах."
        )

    allowed_next = VALID_TRANSITIONS.get(current_status, [])
    if new_status not in allowed_next and not (current_status == "issued" and new_status == "issued"):
        cur_label = schemas.REPAIR_STATUSES.get(current_status, current_status)
        new_label = schemas.REPAIR_STATUSES.get(new_status, new_status)
        raise HTTPException(
            status_code=409,
            detail=f"Недопустимый переход статуса из '{cur_label}' в '{new_label}'"
        )

    effective_amount = (
        status_in.estimated_repair_amount
        if status_in.estimated_repair_amount is not None
        else db_repair.estimated_repair_amount
    )

    if current_status == "diagnostics" and new_status != "diagnostics":
        if effective_amount is None:
            raise HTTPException(
                status_code=400,
                detail="Для выхода из статуса «Диагностика» укажите стоимость ремонта. Можно указать 0 ₽."
            )

    old_amount = db_repair.estimated_repair_amount
    if status_in.estimated_repair_amount is not None:
        db_repair.estimated_repair_amount = status_in.estimated_repair_amount

    now = datetime.utcnow()
    db_repair.status = new_status
    db_repair.updated_at = now

    hist_comment = status_in.comment.strip() if (status_in.comment and status_in.comment.strip()) else None

    if new_status == "issued":
        # Stage 11B: Ready -> Issued requires final_amount, payment_method, warranty_days
        final_amt = status_in.final_amount
        if final_amt is None:
            if status_in.estimated_repair_amount is not None:
                final_amt = float(status_in.estimated_repair_amount)
            elif db_repair.estimated_repair_amount is not None:
                final_amt = float(db_repair.estimated_repair_amount)
            elif db_repair.price is not None:
                final_amt = float(db_repair.price)
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Для выдачи ремонта необходимо указать окончательную стоимость ремонта"
                )
        else:
            final_amt = float(final_amt)

        if final_amt < 0:
            raise HTTPException(
                status_code=400,
                detail="Окончательная стоимость ремонта не может быть отрицательной"
            )

        pm = status_in.payment_method
        if not pm or not pm.strip():
            raise HTTPException(
                status_code=400,
                detail="Для выдачи ремонта необходимо указать способ оплаты"
            )
        pm = pm.strip()

        wd = status_in.warranty_days
        if wd is None:
            raise HTTPException(
                status_code=400,
                detail="Для выдачи ремонта необходимо указать срок гарантии (0 = без гарантии)"
            )
        if wd < 0:
            raise HTTPException(
                status_code=400,
                detail="Срок гарантии не может быть отрицательным"
            )

        # Idempotency: find existing linked sale or create exactly one
        linked_sale = None
        if db_repair.sale_id:
            linked_sale = db.query(models.Sale).filter(models.Sale.id == db_repair.sale_id).first()
        if not linked_sale:
            linked_sale = db.query(models.Sale).filter(
                models.Sale.source_type == "repair",
                models.Sale.source_id == db_repair.id
            ).first()

        desc_parts = [f"Ремонт {db_repair.number}"]
        dev_info = " ".join([p for p in [db_repair.device_type, db_repair.brand, db_repair.model] if p and p.strip()])
        if dev_info:
            desc_parts.append(f"- {dev_info}")
        if db_repair.reported_issue and db_repair.reported_issue.strip():
            desc_parts.append(f". Неисправность: {db_repair.reported_issue.strip()}")
        sale_comment = " ".join(desc_parts)

        if not linked_sale:
            linked_sale = models.Sale(
                customer_id=db_repair.customer_id,
                total_amount=final_amt,
                payment_method=pm,
                comment=sale_comment,
                status="completed",
                source_type="repair",
                source_id=db_repair.id,
                warranty_days=wd,
                warranty_enabled=1 if wd > 0 else 0,
                created_at=now
            )
            db.add(linked_sale)
            db.flush()

            sale_item = models.SaleItem(
                sale_id=linked_sale.id,
                product_id=None,
                title=f"Ремонтные работы: {db_repair.device_type or 'Устройство'} {db_repair.brand or ''} {db_repair.model or ''} ({db_repair.number})".strip(),
                price=final_amt,
                quantity=1,
                created_at=now
            )
            db.add(sale_item)
            db.flush()

            log_audit(
                db,
                "repair_order",
                db_repair.id,
                "repair.sale_created",
                new_value={
                    "repair_id": db_repair.id,
                    "repair_number": db_repair.number,
                    "sale_id": linked_sale.id,
                    "amount": final_amt,
                    "payment_method": pm,
                    "warranty_days": wd,
                    "source_type": "repair"
                }
            )
        else:
            # Re-affirm completed status and matching financials on idempotent call
            linked_sale.status = "completed"
            linked_sale.total_amount = final_amt
            linked_sale.payment_method = pm
            linked_sale.warranty_days = wd
            linked_sale.warranty_enabled = 1 if wd > 0 else 0
            db.flush()

        db_repair.final_amount = final_amt
        db_repair.price = final_amt
        db_repair.payment_method = pm
        db_repair.warranty_days = wd
        db_repair.sale_id = linked_sale.id
        db_repair.issued_at = now
        db_repair.closed_at = now

        pm_human = PAYMENT_METHODS_LABELS.get(pm, pm)
        auto_hist = f"Ремонт выдан клиенту. Оплата: {final_amt:g} ₽ ({pm_human}). Гарантия: {wd} дн. Продажа №{linked_sale.id}"
        hist_comment = f"{auto_hist} | {hist_comment}" if hist_comment else auto_hist

    elif new_status == "canceled":
        db_repair.canceled_at = now
        db_repair.closed_at = now

        existing_sale = db.query(models.Sale).filter(
            models.Sale.source_type == "repair",
            models.Sale.source_id == db_repair.id
        ).first()
        if existing_sale:
            existing_sale.status = "canceled"
            existing_sale.cancelled_at = now
            existing_sale.canceled_by = status_in.changed_by
            db.flush()
            log_audit(
                db,
                "repair_order",
                db_repair.id,
                "repair.sale_canceled",
                new_value={
                    "repair_id": db_repair.id,
                    "repair_number": db_repair.number,
                    "sale_id": existing_sale.id,
                    "amount": existing_sale.total_amount,
                    "source_type": "repair"
                }
            )

    # Note: When new_status == "ready", work is finished but NO sale is created.
    # Revenue occurs strictly on ready -> issued!

    hist = models.RepairStatusHistory(
        repair_id=db_repair.id,
        old_status=current_status,
        new_status=new_status,
        comment=hist_comment,
        changed_by=status_in.changed_by,
        changed_at=now
    )
    db.add(hist)

    event_type = "repair.status_changed"
    if new_status == "issued":
        event_type = "repair.issued"
    elif new_status == "canceled":
        event_type = "repair.canceled"

    audit_old = {"status": current_status}
    audit_new = {"status": new_status, "comment": hist_comment}
    if old_amount != db_repair.estimated_repair_amount:
        audit_old["estimated_repair_amount"] = old_amount
        audit_new["estimated_repair_amount"] = db_repair.estimated_repair_amount
    if db_repair.final_amount is not None:
        audit_new["final_amount"] = db_repair.final_amount
    if db_repair.sale_id is not None:
        audit_new["sale_id"] = db_repair.sale_id

    log_audit(
        db,
        "repair_order",
        db_repair.id,
        event_type,
        old_value=audit_old,
        new_value=audit_new
    )

    db.commit()
    db.refresh(db_repair)

    return enrich_repair_labels(db_repair, db)


@router.get("/{repair_id}/receipt-data", response_model=schemas.RepairReceiptResponse)
def get_repair_receipt_data(repair_id: int, db: Session = Depends(get_db)):
    db_repair = db.query(models.RepairOrder).filter(models.RepairOrder.id == repair_id).first()
    if not db_repair:
        raise HTTPException(status_code=404, detail="Ремонтный заказ не найден")

    enrich_repair_labels(db_repair, db)

    # Organization settings
    org_settings = db.query(models.OrganizationSettings).first()
    org_info = {
        "name": (org_settings.organization_name if org_settings and org_settings.organization_name else "ТехноРебут Сервис"),
        "phone": (org_settings.phone if org_settings and org_settings.phone else "+7 (999) 000-00-00"),
        "address": (org_settings.address if org_settings and org_settings.address else "г. Москва"),
        "inn": (org_settings.inn if org_settings and org_settings.inn else "")
    }

    final_amt = db_repair.final_amount if db_repair.final_amount is not None else (db_repair.price or db_repair.estimated_repair_amount or 0.0)
    w_days = db_repair.warranty_days if db_repair.warranty_days is not None else 0

    warranty_until = None
    if w_days > 0 and db_repair.issued_at:
        w_until_dt = db_repair.issued_at + timedelta(days=w_days)
        warranty_until = w_until_dt.strftime("%d.%m.%Y")

    if w_days == 0:
        warranty_label = "Без гарантии"
    else:
        warranty_label = f"{w_days} дн." + (f" (до {warranty_until})" if warranty_until else "")

    pm_key = db_repair.payment_method or "unspecified"
    pm_label = PAYMENT_METHODS_LABELS.get(pm_key, pm_key)

    work_desc = db_repair.work_description or db_repair.planned_works_text or "Выполнен комплекс диагностических и ремонтных работ"

    return {
        "repair_id": db_repair.id,
        "repair_number": db_repair.number or f"R-{db_repair.id}",
        "status": db_repair.status,
        "status_label": db_repair.status_label,
        "accepted_at": db_repair.accepted_at,
        "issued_at": db_repair.issued_at,
        "customer_name": db_repair.customer_name or "Клиент",
        "customer_phone": db_repair.customer_phone or "—",
        "customer_email": db_repair.customer_email or "",
        "device_type": db_repair.device_type or "Устройство",
        "brand": db_repair.brand or "",
        "model": db_repair.model or "",
        "serial_number": db_repair.serial_number or db_repair.device_serial or "Не указан",
        "reported_issue": db_repair.reported_issue or db_repair.problem_description or "—",
        "diagnosis_text": db_repair.diagnosis_text or db_repair.diagnostics_result or "—",
        "planned_works_text": db_repair.planned_works_text or "",
        "work_description": work_desc,
        "final_amount": float(final_amt),
        "payment_method": pm_key,
        "payment_method_label": pm_label,
        "warranty_days": w_days,
        "warranty_label": warranty_label,
        "warranty_until": warranty_until,
        "sale_id": db_repair.sale_id or getattr(db_repair, "linked_sale_id", None),
        "organization": org_info
    }
