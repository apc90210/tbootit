import os
from typing import Optional
from fastapi import APIRouter, Request, Query, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.core_client import core_client

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return RedirectResponse(url="/repairs", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/repairs", response_class=HTMLResponse)
async def list_repairs(
    request: Request,
    q: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = Query(None),
    device_type: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    customer_phone: Optional[str] = Query(None),
    serial_number: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1),
    msg: Optional[str] = Query(None)
):
    params = {"page": page, "page_size": page_size}
    if q and q.strip(): params["q"] = q.strip()
    if status_filter and status_filter.strip(): params["status"] = status_filter.strip()
    if priority and priority.strip(): params["priority"] = priority.strip()
    if device_type and device_type.strip(): params["device_type"] = device_type.strip()
    if assigned_to and assigned_to.strip(): params["assigned_to"] = assigned_to.strip()
    if customer_phone and customer_phone.strip(): params["customer_phone"] = customer_phone.strip()
    if serial_number and serial_number.strip(): params["serial_number"] = serial_number.strip()

    data = await core_client.get_repairs(params)
    options = await core_client.get_repair_options()

    if isinstance(data, dict) and data.get("error"):
        return templates.TemplateResponse(
            request=request, name="error.html", context={
                "message": f"Ошибка связи с Core API: {data.get('details', 'Сервис недоступен')}"
            }
        )

    statuses_list = options.get("statuses", []) if isinstance(options, dict) else []
    priorities_list = options.get("priorities", []) if isinstance(options, dict) else []
    device_types_list = options.get("device_types", []) if isinstance(options, dict) else []

    items_list = data.get("items", []) if isinstance(data, dict) else []
    total_count = data.get("total", 0) if isinstance(data, dict) else 0

    return templates.TemplateResponse(
        request=request, name="repairs_list.html", context={
            "items": items_list,
            "total": total_count,
            "statuses": statuses_list,
            "priorities": priorities_list,
            "device_types": device_types_list,
            "q": q or "",
            "status_filter": status_filter or "",
            "priority": priority or "",
            "device_type": device_type or "",
            "assigned_to": assigned_to or "",
            "page": page,
            "msg": msg or ""
        }
    )

DEFAULT_COMPLETENESS = "Ноутбук, зарядка, чехол..."
DEFAULT_APPEARANCE = "Потёртости, царпины..."

@router.get("/repairs/new", response_class=HTMLResponse)
async def new_repair_form(request: Request, error_msg: Optional[str] = None):
    options = await core_client.get_repair_options()
    if isinstance(options, dict) and options.get("error"):
        options = {"statuses": [], "priorities": [], "device_types": []}

    default_fee = options.get("default_diagnostic_fee", 500) if isinstance(options, dict) else 500
    default_form_data = {
        "completeness": DEFAULT_COMPLETENESS,
        "appearance": DEFAULT_APPEARANCE,
        "diagnostic_fee": default_fee
    }

    return templates.TemplateResponse(
        request=request, name="repair_new.html", context={
            "options": options,
            "error_msg": error_msg or "",
            "form_data": default_form_data
        }
    )

@router.post("/repairs/new")
async def create_repair_submit(
    request: Request,
    customer_name: str = Form(...),
    customer_phone: str = Form(...),
    device_type: str = Form(...),
    reported_issue: str = Form(...),
    customer_email: Optional[str] = Form(None),
    brand: Optional[str] = Form(None),
    model: Optional[str] = Form(None),
    serial_number: Optional[str] = Form(None),
    completeness: Optional[str] = Form(None),
    appearance: Optional[str] = Form(None),
    customer_comment: Optional[str] = Form(None),
    internal_note: Optional[str] = Form(None),
    access_code_provided: Optional[str] = Form("off"),
    assigned_to: Optional[str] = Form(None),
    priority: Optional[str] = Form("normal"),
    diagnostic_fee: Optional[float] = Form(500.0)
):
    if diagnostic_fee is None:
        options = await core_client.get_repair_options()
        return templates.TemplateResponse(
            request=request, name="repair_new.html", context={
                "options": options if isinstance(options, dict) else {},
                "error_msg": "Укажите стоимость диагностики",
                "form_data": {
                    "customer_name": customer_name, "customer_phone": customer_phone, "customer_email": customer_email,
                    "device_type": device_type, "brand": brand, "model": model, "serial_number": serial_number,
                    "reported_issue": reported_issue, "completeness": completeness, "appearance": appearance,
                    "customer_comment": customer_comment, "internal_note": internal_note,
                    "access_code_provided": access_code_provided in ["on", "true", "1", "True"],
                    "assigned_to": assigned_to, "priority": priority, "diagnostic_fee": None
                }
            }
        )

    if diagnostic_fee < 0:
        options = await core_client.get_repair_options()
        return templates.TemplateResponse(
            request=request, name="repair_new.html", context={
                "options": options if isinstance(options, dict) else {},
                "error_msg": "Стоимость диагностики не может быть отрицательной",
                "form_data": {
                    "customer_name": customer_name, "customer_phone": customer_phone, "customer_email": customer_email,
                    "device_type": device_type, "brand": brand, "model": model, "serial_number": serial_number,
                    "reported_issue": reported_issue, "completeness": completeness, "appearance": appearance,
                    "customer_comment": customer_comment, "internal_note": internal_note,
                    "access_code_provided": access_code_provided in ["on", "true", "1", "True"],
                    "assigned_to": assigned_to, "priority": priority, "diagnostic_fee": diagnostic_fee
                }
            }
        )

    form_data = {
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "customer_email": customer_email or None,
        "device_type": device_type,
        "brand": brand or None,
        "model": model or None,
        "serial_number": serial_number or None,
        "reported_issue": reported_issue,
        "completeness": completeness if completeness is not None else "",
        "appearance": appearance if appearance is not None else "",
        "customer_comment": customer_comment or None,
        "internal_note": internal_note or None,
        "access_code_provided": access_code_provided in ["on", "true", "1", "True"],
        "assigned_to": assigned_to or None,
        "priority": priority or "normal",
        "diagnostic_fee": diagnostic_fee
    }

    res = await core_client.create_repair(form_data)
    if isinstance(res, dict) and res.get("error"):
        options = await core_client.get_repair_options()
        err_detail = res.get("detail") or res.get("details") or "Ошибка создания ремонта в Core API"
        return templates.TemplateResponse(
            request=request, name="repair_new.html", context={
                "options": options if isinstance(options, dict) else {},
                "error_msg": f"Ошибка создания заказа: {err_detail}",
                "form_data": form_data
            }
        )

    repair_id = res.get("id")
    repair_number = res.get("number", "")
    return RedirectResponse(
        url=f"/repairs/{repair_id}?msg=Ремонт+{repair_number}+успешно+принят",
        status_code=status.HTTP_303_SEE_OTHER
    )

@router.get("/repairs/{repair_id}", response_class=HTMLResponse)
async def repair_detail(request: Request, repair_id: int, msg: Optional[str] = None, error_msg: Optional[str] = None):
    data = await core_client.get_repair(repair_id)
    if isinstance(data, dict) and data.get("error"):
        return templates.TemplateResponse(
            request=request, name="error.html", context={
                "message": data.get("detail") or "Ремонтный заказ не найден"
            }
        )

    options = await core_client.get_repair_options()

    # Determine allowed next statuses for status transition UI
    cur_status = data.get("status")
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
    allowed_codes = VALID_TRANSITIONS.get(cur_status, [])
    all_statuses = options.get("statuses", []) if isinstance(options, dict) else []
    allowed_statuses = [st for st in all_statuses if st["value"] in allowed_codes]

    return templates.TemplateResponse(
        request=request, name="repair_detail.html", context={
            "repair": data,
            "allowed_statuses": allowed_statuses,
            "msg": msg or "",
            "error_msg": error_msg or ""
        }
    )

@router.get("/repairs/{repair_id}/edit", response_class=HTMLResponse)
async def repair_edit_form(request: Request, repair_id: int, error_msg: Optional[str] = None):
    data = await core_client.get_repair(repair_id)
    if isinstance(data, dict) and data.get("error"):
        return templates.TemplateResponse(
            request=request, name="error.html", context={
                "message": data.get("detail") or "Ремонтный заказ не найден"
            }
        )

    if data.get("status") in ["issued", "canceled"]:
        return templates.TemplateResponse(
            request=request, name="error.html", context={
                "message": "Запрещено редактировать закрытый или отменённый ремонт"
            }
        )

    options = await core_client.get_repair_options()

    return templates.TemplateResponse(
        request=request, name="repair_edit.html", context={
            "repair": data,
            "options": options if isinstance(options, dict) else {},
            "error_msg": error_msg or ""
        }
    )

@router.post("/repairs/{repair_id}/edit")
async def update_repair_submit(
    request: Request,
    repair_id: int,
    customer_name: str = Form(...),
    customer_phone: str = Form(...),
    device_type: str = Form(...),
    reported_issue: str = Form(...),
    customer_email: Optional[str] = Form(None),
    brand: Optional[str] = Form(None),
    model: Optional[str] = Form(None),
    serial_number: Optional[str] = Form(None),
    completeness: Optional[str] = Form(None),
    appearance: Optional[str] = Form(None),
    customer_comment: Optional[str] = Form(None),
    internal_note: Optional[str] = Form(None),
    access_code_provided: Optional[str] = Form("off"),
    assigned_to: Optional[str] = Form(None),
    priority: Optional[str] = Form("normal"),
    diagnostic_fee: Optional[float] = Form(None)
):
    if diagnostic_fee is not None and diagnostic_fee < 0:
        options = await core_client.get_repair_options()
        data = await core_client.get_repair(repair_id)
        return templates.TemplateResponse(
            request=request, name="repair_edit.html", context={
                "repair": data if isinstance(data, dict) else {},
                "options": options if isinstance(options, dict) else {},
                "error_msg": "Стоимость диагностики не может быть отрицательной"
            }
        )

    payload = {
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "customer_email": customer_email or None,
        "device_type": device_type,
        "brand": brand or None,
        "model": model or None,
        "serial_number": serial_number or None,
        "reported_issue": reported_issue,
        "completeness": completeness or None,
        "appearance": appearance or None,
        "customer_comment": customer_comment or None,
        "internal_note": internal_note or None,
        "access_code_provided": access_code_provided in ["on", "true", "1", "True"],
        "assigned_to": assigned_to or None,
        "priority": priority or "normal"
    }
    if diagnostic_fee is not None:
        payload["diagnostic_fee"] = diagnostic_fee

    res = await core_client.update_repair(repair_id, payload)
    if isinstance(res, dict) and res.get("error"):
        options = await core_client.get_repair_options()
        err_detail = res.get("detail") or res.get("details") or "Ошибка обновления карточки"
        data = await core_client.get_repair(repair_id)
        return templates.TemplateResponse(
            request=request, name="repair_edit.html", context={
                "repair": data if isinstance(data, dict) else payload,
                "options": options if isinstance(options, dict) else {},
                "error_msg": f"Ошибка обновления: {err_detail}"
            }
        )

    return RedirectResponse(
        url=f"/repairs/{repair_id}?msg=Данные+карточки+успешно+обновлены",
        status_code=status.HTTP_303_SEE_OTHER
    )

@router.post("/repairs/{repair_id}/status")
async def update_repair_status_submit(
    request: Request,
    repair_id: int,
    status_value: str = Form(..., alias="status"),
    comment: Optional[str] = Form(None),
    changed_by: Optional[str] = Form(None)
):
    repair_data = await core_client.get_repair(repair_id)
    if isinstance(repair_data, dict) and repair_data.get("status") == "diagnostics" and status_value == "ready":
        if not comment or not comment.strip():
            return await repair_detail(
                request,
                repair_id,
                error_msg="Для перехода из диагностики в статус 'Готов' требуется указать комментарий с описанием выполненных работ"
            )

    res = await core_client.update_repair_status(
        repair_id=repair_id,
        status=status_value,
        comment=comment,
        changed_by=changed_by
    )

    if isinstance(res, dict) and res.get("error"):
        err_detail = res.get("detail") or "Недопустимый переход статуса"
        return await repair_detail(request, repair_id, error_msg=f"Ошибка смены статуса: {err_detail}")

    status_label = res.get("status_label") or status_value
    return RedirectResponse(
        url=f"/repairs/{repair_id}?msg=Статус+успешно+изменён+на+«{status_label}»",
        status_code=status.HTTP_303_SEE_OTHER
    )

@router.get("/repairs/{repair_id}/print", response_class=HTMLResponse)
async def print_repair_order(request: Request, repair_id: int):
    data = await core_client.get_repair(repair_id)
    if isinstance(data, dict) and data.get("error"):
        return templates.TemplateResponse(
            request=request, name="error.html", context={
                "message": data.get("detail") or "Ремонтный заказ не найден"
            }
        )

    org_settings = await core_client.get_organization_settings()
    if isinstance(org_settings, dict) and org_settings.get("error"):
        org_settings = {}

    return templates.TemplateResponse(
        request=request, name="repair_print_order.html", context={
            "repair": data,
            "org": org_settings
        }
    )
