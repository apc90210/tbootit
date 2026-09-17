import os
from typing import Optional
from fastapi import APIRouter, Request, Query, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.core_client import core_client

router = APIRouter(redirect_slashes=False)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

def is_owner_request(request: Request) -> bool:
    """Check if the request originates from an authenticated OWNER certificate."""
    if request.headers.get("x-auth-is-owner") == "1":
        return True
    if request.headers.get("x-client-role") == "owner":
        return True
    return False


@router.get("/", response_class=HTMLResponse)
@router.get("/repairs", response_class=HTMLResponse)
@router.get("/repairs/", response_class=HTMLResponse)
async def list_repairs(
    request: Request,
    q: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = Query(None),
    device_type: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    customer_phone: Optional[str] = Query(None),
    serial_number: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    sort: Optional[str] = Query(None),
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
    if date_from and date_from.strip(): params["date_from"] = date_from.strip()
    if date_to and date_to.strip(): params["date_to"] = date_to.strip()
    if sort and sort.strip(): params["sort"] = sort.strip()

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
            "customer_phone": customer_phone or "",
            "serial_number": serial_number or "",
            "date_from": date_from or "",
            "date_to": date_to or "",
            "sort": sort or "",
            "page": page,
            "page_size": page_size,
            "msg": msg or "",
            "is_owner": is_owner_request(request),
        }
    )


@router.post("/repairs/bulk-delete")
@router.post("/repairs/repairs/bulk-delete")
async def bulk_delete_repairs_endpoint(request: Request):
    if not is_owner_request(request):
        return JSONResponse(
            status_code=403,
            content={"error": True, "detail": "Доступ запрещён: функция безвозвратного удаления доступна только владельцу (сертификат owner)"}
        )

    repair_ids = []
    try:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            data = await request.json()
            repair_ids = data.get("repair_ids", [])
        else:
            form = await request.form()
            raw_ids = form.getlist("selected_ids") or form.getlist("repair_ids")
            if not raw_ids and form.get("repair_ids"):
                raw_ids = str(form.get("repair_ids")).split(",")
            repair_ids = [int(x) for x in raw_ids if str(x).strip().isdigit()]
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": True, "detail": f"Ошибка разбора ID ремонтов: {e}"})

    if not repair_ids:
        return JSONResponse(status_code=400, content={"error": True, "detail": "Не выбрано ни одного ремонта для удаления"})

    res = await core_client.bulk_delete_repairs(repair_ids)
    if res and isinstance(res, dict) and res.get("error"):
        return JSONResponse(
            status_code=res.get("status_code", 500),
            content={"error": True, "detail": res.get("detail", "Ошибка удаления в Core API")}
        )

    return JSONResponse(content={
        "success": True,
        "deleted_count": res.get("deleted_count", len(repair_ids)),
        "deleted_ids": res.get("deleted_ids", repair_ids)
    })


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
    diagnostic_fee: Optional[int] = Form(500)
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
        "received": ["diagnostics", "in_repair", "ready", "canceled"],
        "diagnostics": ["waiting_customer", "waiting_parts", "in_repair", "ready", "unrepairable", "canceled"],
        "waiting_customer": ["diagnostics", "waiting_parts", "in_repair", "ready", "unrepairable", "canceled"],
        "waiting_parts": ["waiting_customer", "in_repair", "ready", "unrepairable", "canceled"],
        "in_repair": ["waiting_customer", "waiting_parts", "ready", "unrepairable", "canceled"],
        "ready": ["in_repair", "issued"],
        "unrepairable": ["diagnostics", "in_repair", "ready", "issued", "canceled"],
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
    diagnostic_fee: Optional[int] = Form(None),
    diagnosis_text: Optional[str] = Form(None),
    planned_works_text: Optional[str] = Form(None),
    planned_parts_text: Optional[str] = Form(None),
    estimated_repair_amount: Optional[int] = Form(None)
):
    if diagnostic_fee is not None and diagnostic_fee < 0:
        options = await core_client.get_repair_options()
        data = await core_client.get_repair(repair_id)
        form_repair = data if isinstance(data, dict) else {}
        form_repair.update({
            "diagnosis_text": diagnosis_text,
            "planned_works_text": planned_works_text,
            "planned_parts_text": planned_parts_text,
            "estimated_repair_amount": estimated_repair_amount,
            "diagnostic_fee": diagnostic_fee
        })
        return templates.TemplateResponse(
            request=request, name="repair_edit.html", context={
                "repair": form_repair,
                "options": options if isinstance(options, dict) else {},
                "error_msg": "Стоимость диагностики не может быть отрицательной"
            }
        )

    if estimated_repair_amount is not None and estimated_repair_amount < 0:
        options = await core_client.get_repair_options()
        data = await core_client.get_repair(repair_id)
        form_repair = data if isinstance(data, dict) else {}
        form_repair.update({
            "diagnosis_text": diagnosis_text,
            "planned_works_text": planned_works_text,
            "planned_parts_text": planned_parts_text,
            "estimated_repair_amount": estimated_repair_amount,
            "diagnostic_fee": diagnostic_fee
        })
        return templates.TemplateResponse(
            request=request, name="repair_edit.html", context={
                "repair": form_repair,
                "options": options if isinstance(options, dict) else {},
                "error_msg": "Предполагаемая стоимость ремонта не может быть отрицательной"
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
        "priority": priority or "normal",
        "diagnosis_text": diagnosis_text if (diagnosis_text and diagnosis_text.strip()) else None,
        "planned_works_text": planned_works_text if (planned_works_text and planned_works_text.strip()) else None,
        "planned_parts_text": planned_parts_text if (planned_parts_text and planned_parts_text.strip()) else None,
        "estimated_repair_amount": estimated_repair_amount
    }
    if diagnostic_fee is not None:
        payload["diagnostic_fee"] = diagnostic_fee

    res = await core_client.update_repair(repair_id, payload)
    if isinstance(res, dict) and res.get("error"):
        options = await core_client.get_repair_options()
        err_detail = res.get("detail") or res.get("details") or "Ошибка обновления карточки"
        data = await core_client.get_repair(repair_id)
        form_repair = data if isinstance(data, dict) else {}
        form_repair.update(payload)
        return templates.TemplateResponse(
            request=request, name="repair_edit.html", context={
                "repair": form_repair,
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
    changed_by: Optional[str] = Form(None),
    estimated_repair_amount_raw: Optional[str] = Form(None, alias="estimated_repair_amount"),
    final_amount_raw: Optional[str] = Form(None, alias="final_amount"),
    payment_method: Optional[str] = Form(None),
    warranty_days_raw: Optional[str] = Form(None, alias="warranty_days")
):
    parsed_amount: Optional[int] = None
    if estimated_repair_amount_raw is not None and estimated_repair_amount_raw.strip() != "":
        try:
            val_float = float(estimated_repair_amount_raw)
            if not val_float.is_integer() or val_float < 0:
                return await repair_detail(
                    request,
                    repair_id,
                    error_msg="Предполагаемая стоимость ремонта должна быть целым неотрицательным числом"
                )
            parsed_amount = int(val_float)
        except ValueError:
            return await repair_detail(
                request,
                repair_id,
                error_msg="Предполагаемая стоимость ремонта должна быть целым числом"
            )

    repair_data = await core_client.get_repair(repair_id)
    if ((repair_data.get("status") == "diagnostics" and status_value != "diagnostics") or status_value == "ready"):
        effective_amount = parsed_amount if parsed_amount is not None else repair_data.get("estimated_repair_amount")
        if effective_amount is None:
            detail_msg = (
                "Для перевода в статус «Готов» укажите стоимость ремонта. Можно указать 0 ₽."
                if status_value == "ready"
                else "Для выхода из статуса «Диагностика» укажите стоимость ремонта. Можно указать 0 ₽."
            )
            return await repair_detail(
                request,
                repair_id,
                error_msg=detail_msg
            )

    parsed_final_amount: Optional[float] = None
    parsed_warranty_days: Optional[int] = None
    pm: Optional[str] = None

    if status_value == "issued":
        # Final amount validation
        if final_amount_raw is not None and final_amount_raw.strip() != "":
            try:
                val = float(final_amount_raw)
                if val < 0:
                    return await repair_detail(
                        request, repair_id, error_msg="Окончательная стоимость ремонта не может быть отрицательной"
                    )
                parsed_final_amount = val
            except ValueError:
                return await repair_detail(
                    request, repair_id, error_msg="Окончательная стоимость ремонта должна быть числом"
                )
        elif estimated_repair_amount_raw is not None and estimated_repair_amount_raw.strip() != "":
            try:
                val = float(estimated_repair_amount_raw)
                if val < 0:
                    return await repair_detail(request, repair_id, error_msg="Стоимость ремонта не может быть отрицательной")
                parsed_final_amount = val
            except ValueError:
                return await repair_detail(request, repair_id, error_msg="Стоимость ремонта должна быть числом")
        elif isinstance(repair_data, dict) and (repair_data.get("estimated_repair_amount") is not None or repair_data.get("price") is not None):
            val = repair_data.get("estimated_repair_amount") if repair_data.get("estimated_repair_amount") is not None else repair_data.get("price")
            parsed_final_amount = float(val)
        else:
            return await repair_detail(
                request, repair_id, error_msg="Для выдачи ремонта необходимо указать окончательную стоимость ремонта"
            )

        # Payment method validation
        if not payment_method or not payment_method.strip():
            return await repair_detail(
                request, repair_id, error_msg="Для выдачи ремонта выберите способ оплаты"
            )
        pm = payment_method.strip()

        # Warranty validation
        if warranty_days_raw is not None and warranty_days_raw.strip() != "":
            try:
                wd = int(warranty_days_raw)
                if wd < 0:
                    return await repair_detail(
                        request, repair_id, error_msg="Срок гарантии не может быть отрицательным"
                    )
                parsed_warranty_days = wd
            except ValueError:
                return await repair_detail(
                    request, repair_id, error_msg="Срок гарантии должен быть целым числом дней (0 = без гарантии)"
                )
        else:
            return await repair_detail(
                request, repair_id, error_msg="Для выдачи ремонта укажите срок гарантии (0 = без гарантии)"
            )

    res = await core_client.update_repair_status(
        repair_id=repair_id,
        status=status_value,
        comment=comment,
        changed_by=changed_by,
        estimated_repair_amount=parsed_amount,
        final_amount=parsed_final_amount,
        payment_method=pm,
        warranty_days=parsed_warranty_days
    )

    if isinstance(res, dict) and res.get("error"):
        err_detail = res.get("detail") or "Недопустимый переход статуса"
        return await repair_detail(request, repair_id, error_msg=err_detail)

    status_label = res.get("status_label") or status_value
    success_msg = f"Статус успешно изменён на «{status_label}»"
    if status_value == "issued":
        sale_id = res.get("sale_id") or res.get("linked_sale_id")
        if sale_id:
            success_msg = f"Ремонт выдан клиенту. Оформлена продажа №{sale_id}."
        else:
            success_msg = "Ремонт выдан клиенту. Оплата успешно принята."

    return RedirectResponse(
        url=f"/repairs/{repair_id}?msg={success_msg}",
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

    if not isinstance(data, dict) or data.get("diagnostic_fee") is None:
        return templates.TemplateResponse(
            request=request, name="error.html", context={
                "message": "В ремонтном заказе отсутствует стоимость диагностики"
            }, status_code=400
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

@router.get("/repairs/{repair_id}/receipt", response_class=HTMLResponse)
@router.get("/{repair_id}/receipt", response_class=HTMLResponse)
async def print_repair_warranty_receipt(request: Request, repair_id: int):
    data = await core_client.get_repair_receipt_data(repair_id)
    if isinstance(data, dict) and data.get("error"):
        return templates.TemplateResponse(
            request=request, name="error.html", context={
                "message": data.get("detail") or "Данные для квитанции не найдены"
            }
        )

    return templates.TemplateResponse(
        request=request, name="repair_warranty_receipt.html", context={
            "receipt": data
        }
    )
