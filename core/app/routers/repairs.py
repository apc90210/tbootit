from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc, text
from typing import Optional, List
from datetime import datetime, date

from app.database import get_db
from app import models, schemas
from app.services.repair_number_service import generate_repair_number
from app.routers.customers import log_audit

router = APIRouter()

VALID_TRANSITIONS = {
    "received": ["diagnostics", "canceled"],
    "diagnostics": ["waiting_customer", "waiting_parts", "in_repair", "unrepairable", "canceled"],
    "waiting_customer": ["diagnostics", "waiting_parts", "in_repair", "unrepairable", "canceled"],
    "waiting_parts": ["waiting_customer", "in_repair", "unrepairable", "canceled"],
    "in_repair": ["waiting_customer", "waiting_parts", "ready", "unrepairable", "canceled"],
    "ready": ["in_repair", "issued"],
    "unrepairable": ["issued", "canceled"],
    "issued": [],
    "canceled": []
}

def enrich_repair_labels(db_repair: models.RepairOrder) -> models.RepairOrder:
    if db_repair:
        setattr(db_repair, "status_label", schemas.REPAIR_STATUSES.get(db_repair.status, db_repair.status))
        setattr(db_repair, "priority_label", schemas.REPAIR_PRIORITIES.get(db_repair.priority, db_repair.priority))
    return db_repair

@router.get("/options")
def get_repair_options():
    statuses_list = [{"value": k, "label": v} for k, v in schemas.REPAIR_STATUSES.items()]
    priorities_list = [{"value": k, "label": v} for k, v in schemas.REPAIR_PRIORITIES.items()]
    return {
        "statuses": statuses_list,
        "priorities": priorities_list,
        "device_types": schemas.REPAIR_DEVICE_TYPES
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
            "priority": db_repair.priority
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
        "reported_issue": db_repair.reported_issue
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

    allowed_next = VALID_TRANSITIONS.get(current_status, [])
    if new_status not in allowed_next:
        cur_label = schemas.REPAIR_STATUSES.get(current_status, current_status)
        new_label = schemas.REPAIR_STATUSES.get(new_status, new_status)
        raise HTTPException(
            status_code=409,
            detail=f"Недопустимый переход статуса из '{cur_label}' в '{new_label}'"
        )

    now = datetime.utcnow()
    db_repair.status = new_status
    db_repair.updated_at = now

    if new_status == "issued":
        db_repair.issued_at = now
        db_repair.closed_at = now
    elif new_status == "canceled":
        db_repair.canceled_at = now
        db_repair.closed_at = now

    hist = models.RepairStatusHistory(
        repair_id=db_repair.id,
        old_status=current_status,
        new_status=new_status,
        comment=status_in.comment or f"Изменение статуса на '{schemas.REPAIR_STATUSES.get(new_status, new_status)}'",
        changed_by=status_in.changed_by,
        changed_at=now
    )
    db.add(hist)

    event_type = "repair.status_changed"
    if new_status == "issued":
        event_type = "repair.issued"
    elif new_status == "canceled":
        event_type = "repair.canceled"

    log_audit(
        db,
        "repair_order",
        db_repair.id,
        event_type,
        old_value={"status": current_status},
        new_value={"status": new_status, "comment": status_in.comment}
    )

    db.commit()
    db.refresh(db_repair)

    return enrich_repair_labels(db_repair)
