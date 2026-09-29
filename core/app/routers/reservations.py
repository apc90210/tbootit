import re
import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app import models, schemas
from app.config import settings
from app.routers.products import log_audit

router = APIRouter()


def normalize_phone(phone: str) -> str:
    """
    Normalizes a Russian phone number string to canonical +7XXXXXXXXXX.
    Accepts:
      +7 912 345-67-89, 8 (912) 345-67-89, 89123456789, +79123456789, 79123456789, 9123456789
    Rejects numbers with invalid length or illegal non-phone characters.
    """
    if not phone or not isinstance(phone, str) or not phone.strip():
        raise HTTPException(
            status_code=422,
            detail="Номер телефона обязателен для заполнения"
        )

    # Extract all digits
    digits = re.sub(r"\D", "", phone.strip())

    if len(digits) == 10:
        digits = "7" + digits
    elif len(digits) == 11:
        if digits[0] in ("7", "8"):
            digits = "7" + digits[1:]
        else:
            raise HTTPException(
                status_code=422,
                detail="Некорректный код страны в номере телефона. Допустимы номера РФ (+7/8)."
            )
    else:
        raise HTTPException(
            status_code=422,
            detail="Некорректный номер телефона. Введите номер в формате +7 (9XX) XXX-XX-XX"
        )

    return f"+{digits}"


def _verify_owner(request: Request):
    """Verify owner authentication headers from Admin-Shell proxy or internal call."""
    auth_is_owner = request.headers.get("x-auth-is-owner")
    api_token = request.headers.get("x-api-token")
    if auth_is_owner != "1" or api_token != settings.api_token:
        raise HTTPException(
            status_code=403,
            detail="Доступ запрещён: требуется сертификат владельца и внутренний токен"
        )


def _verify_internal_token(request: Request):
    """Verify internal server-to-server token for web backend requests."""
    api_token = request.headers.get("x-api-token")
    if not api_token or api_token != settings.api_token:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: invalid or missing API token"
        )


def _to_response(req_obj: models.ReservationRequest, is_duplicate: bool = False) -> schemas.ReservationRequestResponse:
    p = req_obj.product
    return schemas.ReservationRequestResponse(
        id=req_obj.id,
        product_id=req_obj.product_id,
        phone=req_obj.phone,
        status=req_obj.status,
        customer_name=req_obj.customer_name,
        comment=req_obj.comment,
        created_at=req_obj.created_at,
        updated_at=req_obj.updated_at,
        confirmed_at=req_obj.confirmed_at,
        cancelled_at=req_obj.cancelled_at,
        product_title=(p.site_title or p.title) if p else None,
        product_price=p.sale_price if p else None,
        product_status=p.status if p else None,
        is_duplicate=is_duplicate,
    )


@router.post("/", response_model=schemas.ReservationRequestResponse, status_code=201)
def create_reservation_request(
    body: schemas.ReservationRequestCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Public server-to-server reservation request creation.
    Called by trusted web backend (tboot-site) with internal API token.
    Enforces server-side product availability validation and duplicate prevention.
    """
    _verify_internal_token(request)

    phone_norm = normalize_phone(body.phone)

    # 1. Product existence & availability check
    product = db.query(models.Product).filter(models.Product.id == body.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")

    if product.status != "in_stock":
        raise HTTPException(
            status_code=409,
            detail="К сожалению, товар уже недоступен для резервирования."
        )

    if (product.quantity or 0) <= 0:
        raise HTTPException(
            status_code=409,
            detail="К сожалению, товар уже недоступен для резервирования."
        )

    if product.is_published_site != 1:
        raise HTTPException(
            status_code=409,
            detail="К сожалению, товар недоступен для резервирования на сайте."
        )

    # 2. Anti-spam / duplicate pending protection for same (product_id, phone)
    existing = db.query(models.ReservationRequest).filter(
        models.ReservationRequest.product_id == body.product_id,
        models.ReservationRequest.phone == phone_norm,
        models.ReservationRequest.status == "pending"
    ).first()

    if existing:
        return _to_response(existing, is_duplicate=True)

    # 3. Create new pending reservation request
    customer_name = body.customer_name.strip() if body.customer_name and body.customer_name.strip() else None
    new_req = models.ReservationRequest(
        product_id=body.product_id,
        phone=phone_norm,
        status="pending",
        customer_name=customer_name
    )
    db.add(new_req)
    db.commit()
    db.refresh(new_req)

    # Audit logging
    log_audit(
        db,
        "reservation_request",
        new_req.id,
        "create",
        new_value={
            "product_id": body.product_id,
            "phone": phone_norm,
            "status": "pending",
            "customer_name": customer_name
        },
        comment=f"New reservation request #{new_req.id} for product #{body.product_id}"
    )
    db.commit()

    return _to_response(new_req, is_duplicate=False)


@router.get("/", response_model=schemas.ReservationRequestListResponse)
def list_reservation_requests(
    request: Request,
    status: Optional[str] = Query(None, description="Filter by status: pending, confirmed, cancelled"),
    product_id: Optional[int] = Query(None, description="Filter by product ID"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Owner-only list of reservation requests with filtering and pagination.
    """
    _verify_owner(request)

    query = db.query(models.ReservationRequest)

    if status:
        query = query.filter(models.ReservationRequest.status == status)
    if product_id:
        query = query.filter(models.ReservationRequest.product_id == product_id)

    total = query.count()
    items = query.order_by(desc(models.ReservationRequest.created_at)).offset(offset).limit(limit).all()

    return schemas.ReservationRequestListResponse(
        items=[_to_response(item) for item in items],
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/{req_id}", response_model=schemas.ReservationRequestResponse)
def get_reservation_request(
    req_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Owner-only view of a single reservation request.
    """
    _verify_owner(request)

    req_obj = db.query(models.ReservationRequest).filter(models.ReservationRequest.id == req_id).first()
    if not req_obj:
        raise HTTPException(status_code=404, detail="Заявка на резерв не найдена")

    return _to_response(req_obj)


@router.patch("/{req_id}/status", response_model=schemas.ReservationRequestResponse)
def update_reservation_status(
    req_id: int,
    body: schemas.ReservationRequestStatusUpdate,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Owner-only status update for a reservation request (pending -> confirmed | cancelled).
    Crucial business invariant: does NOT create a sale, does NOT decrement stock, does NOT modify product status.
    """
    _verify_owner(request)

    if body.status not in ("confirmed", "cancelled"):
        raise HTTPException(
            status_code=422,
            detail="Недопустимый статус. Разрешены только: 'confirmed', 'cancelled'"
        )

    req_obj = db.query(models.ReservationRequest).filter(models.ReservationRequest.id == req_id).first()
    if not req_obj:
        raise HTTPException(status_code=404, detail="Заявка на резерв не найдена")

    old_status = req_obj.status
    now = datetime.datetime.now(datetime.timezone.utc)

    req_obj.status = body.status
    if body.comment is not None:
        req_obj.comment = body.comment.strip() if body.comment.strip() else None

    if body.status == "confirmed":
        req_obj.confirmed_at = now
    elif body.status == "cancelled":
        req_obj.cancelled_at = now

    comment = f"Reservation request #{req_id} status changed: {old_status} -> {body.status}"
    if body.comment:
        comment += f" (комментарий: {body.comment.strip()})"

    log_audit(
        db,
        "reservation_request",
        req_id,
        f"status_{body.status}",
        old_value={"status": old_status},
        new_value={"status": body.status, "comment": req_obj.comment},
        comment=comment
    )

    db.commit()
    db.refresh(req_obj)

    return _to_response(req_obj)
