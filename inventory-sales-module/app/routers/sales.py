from typing import Optional
from fastapi import APIRouter, Request, Query, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.core_client import core_client
from app.schemas import SELLABLE_STATUSES, PAYMENT_METHODS, STATUS_LABELS, SALE_STATUS_LABELS
import os
import json

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


def is_owner_request(request: Request) -> bool:
    """Check if the request originates from an authenticated OWNER certificate."""
    if request.headers.get("x-auth-is-owner") == "1":
        return True
    if request.headers.get("x-client-role") == "owner":
        return True
    return False


@router.get("/sales", response_class=HTMLResponse)
async def sales_list(
    request: Request,
    limit: int = Query(50),
    offset: int = Query(0),
    status: Optional[str] = Query(None),
):
    """List of recent sales."""
    params = {"limit": limit, "offset": offset}
    if status and status.strip():
        params["status"] = status.strip()

    data = await core_client.get_sales(params)

    if data and isinstance(data, dict) and "error" in data:
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"message": "Ошибка Core API при загрузке продаж"},
        )

    return templates.TemplateResponse(
        request=request,
        name="sales_list.html",
        context={
            "sales_data": data,
            "limit": limit,
            "offset": offset,
            "selected_status": status or "",
            "payment_methods": PAYMENT_METHODS,
            "sale_status_labels": SALE_STATUS_LABELS,
            "is_owner": is_owner_request(request),
        },
    )


@router.post("/sales/bulk-delete")
async def bulk_delete_sales_endpoint(request: Request):
    if not is_owner_request(request):
        return JSONResponse(
            status_code=403,
            content={"error": True, "detail": "Доступ запрещён: функция безвозвратного удаления доступна только владельцу (сертификат owner)"}
        )

    sale_ids = []
    try:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            data = await request.json()
            sale_ids = data.get("sale_ids", [])
        else:
            form = await request.form()
            raw_ids = form.getlist("selected_ids") or form.getlist("sale_ids")
            if not raw_ids and form.get("sale_ids"):
                raw_ids = str(form.get("sale_ids")).split(",")
            sale_ids = [int(x) for x in raw_ids if str(x).strip().isdigit()]
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": True, "detail": f"Ошибка разбора ID продаж: {e}"})

    if not sale_ids:
        return JSONResponse(status_code=400, content={"error": True, "detail": "Не выбрано ни одной продажи для удаления"})

    res = await core_client.bulk_delete_sales(sale_ids)
    if res and isinstance(res, dict) and res.get("error"):
        return JSONResponse(
            status_code=res.get("status_code", 500),
            content={"error": True, "detail": res.get("detail", "Ошибка удаления в Core API")}
        )

    return JSONResponse(content={
        "success": True,
        "deleted_count": res.get("deleted_count", len(sale_ids)),
        "deleted_ids": res.get("deleted_ids", sale_ids)
    })




@router.get("/sales/new", response_class=HTMLResponse)
async def new_sale_form(request: Request, product_id: Optional[int] = Query(None)):
    """Form for single product direct sale."""
    product = None
    if product_id:
        product = await core_client.get_product(product_id)
        if product and isinstance(product, dict) and "error" in product:
            product = None

    return templates.TemplateResponse(
        request=request,
        name="sales_new.html",
        context={
            "product": product,
            "payment_methods": PAYMENT_METHODS,
        },
    )


@router.post("/sales/create")
async def create_sale_endpoint(
    request: Request,
    product_id: int = Form(...),
    price: float = Form(...),
    quantity: int = Form(1),
    payment_method: str = Form(...),
    warranty_days: Optional[int] = Form(30),
    no_warranty: Optional[str] = Form(None),
    notes: Optional[str] = Form(""),
):
    """Process single product sale creation."""
    if price <= 0:
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"message": "Цена продажи должна быть больше 0"},
        )
    if quantity < 1:
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"message": "Количество товара должно быть не менее 1"},
        )

    prod = await core_client.get_product(product_id)
    if not prod or (isinstance(prod, dict) and "error" in prod):
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"message": "Товар не найден"},
        )

    title = prod.get("title", f"Товар #{product_id}")

    is_no_warranty = no_warranty is not None
    final_warranty_enabled = not is_no_warranty
    final_warranty_days = None if is_no_warranty else (warranty_days if warranty_days is not None else 30)

    payload = {
        "customer_id": None,
        "payment_method": payment_method,
        "comment": notes or "",
        "warranty_days": final_warranty_days,
        "warranty_enabled": final_warranty_enabled,
        "items": [
            {
                "product_id": product_id,
                "title": title,
                "price": price,
                "quantity": quantity,
            }
        ],
    }

    res = await core_client.create_sale(payload)
    if res and isinstance(res, dict) and "error" in res:
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"message": res.get("detail", "Ошибка оформления продажи")},
        )

    sale_id = res.get("id")
    return RedirectResponse(url=f"/sales/{sale_id}", status_code=303)


@router.get("/sales/{sale_id}", response_class=HTMLResponse)
async def sale_detail(request: Request, sale_id: int):
    """Sale detail / success page."""
    sale = await core_client.get_sale(sale_id)

    if sale and isinstance(sale, dict) and "error" in sale:
        if sale.get("status_code") == 404:
            return templates.TemplateResponse(
                request=request,
                name="error.html",
                context={"message": "Продажа не найдена"},
            )
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"message": "Ошибка Core API"},
        )

    # Fetch any Avito post-sale tasks for this sale
    avito_tasks = []
    has_linked_listings = False
    all_archived = False
    try:
        tasks_resp = await core_client.get_sale_avito_tasks(sale_id)
        if tasks_resp and isinstance(tasks_resp, dict):
            avito_tasks = tasks_resp.get("tasks", [])
            has_linked_listings = tasks_resp.get("has_linked_listings", len(avito_tasks) > 0)
            all_archived = tasks_resp.get("all_archived", False)
    except Exception:
        avito_tasks = []

    avito_dismissed = request.query_params.get("avito_dismissed") == "1"
    avito_msg = request.query_params.get("avito_msg")

    # Fetch revision history
    revisions = []
    try:
        rev_resp = await core_client.get_sale_revisions(sale_id)
        if rev_resp and isinstance(rev_resp, dict):
            raw_revs = rev_resp.get("items", [])
            for r in raw_revs:
                try:
                    s_diff = json.loads(r.get("structured_diff", "{}"))
                    r["human_bullets"] = s_diff.get("human_bullets", [])
                except Exception:
                    r["human_bullets"] = []
                revisions.append(r)
    except Exception:
        revisions = []

    return templates.TemplateResponse(
        request=request,
        name="sales_detail.html",
        context={
            "sale": sale,
            "payment_methods": PAYMENT_METHODS,
            "sale_status_labels": SALE_STATUS_LABELS,
            "avito_tasks": avito_tasks,
            "has_linked_listings": has_linked_listings,
            "all_archived": all_archived,
            "avito_dismissed": avito_dismissed,
            "avito_msg": avito_msg,
            "revisions": revisions,
        },
    )

@router.post("/sales/{sale_id}/avito-deactivate")
async def sale_avito_deactivate_endpoint(request: Request, sale_id: int):
    """Queue or mark post-sale Avito deactivation task(s) for manual removal."""
    resp = await core_client.deactivate_sale_avito(sale_id)
    msg = None
    if resp and isinstance(resp, dict):
        tasks = resp.get("tasks", [])
        queued_count = resp.get("queued_count", 0)
        if not tasks:
            msg = "no_listings"
        elif queued_count == 0:
            if all(t.get("status") == "success" for t in tasks):
                msg = "already_deactivated"
            elif any(t.get("status") in ["queued", "processing", "manual_required"] for t in tasks):
                msg = "already_in_progress"
            else:
                msg = "no_tasks_queued"
        else:
            msg = f"queued_{queued_count}"

    url = f"/sales/{sale_id}"
    if msg:
        url += f"?avito_msg={msg}"
    return RedirectResponse(url=url, status_code=303)

@router.post("/sales/{sale_id}/avito-manual-open")
async def sale_avito_manual_open_endpoint(request: Request, sale_id: int):
    """Mark tasks as manual_required when operator opens listing for manual removal."""
    await core_client.mark_sale_manual_open(sale_id)
    return RedirectResponse(url=f"/sales/{sale_id}?avito_msg=manual_opened", status_code=303)

@router.post("/sales/{sale_id}/avito-manual-confirm")
async def sale_avito_manual_confirm_endpoint(request: Request, sale_id: int):
    """Operator explicitly confirms: 'Я снял объявление'."""
    await core_client.manual_confirm_sale_avito(sale_id)
    return RedirectResponse(url=f"/sales/{sale_id}?avito_msg=manual_confirmed", status_code=303)

@router.post("/sales/{sale_id}/avito-dismiss")
async def sale_avito_dismiss_endpoint(request: Request, sale_id: int):
    """Operator chose 'Не снимать'. Transitions tasks to canceled, preserves listing status."""
    await core_client.dismiss_sale_avito(sale_id)
    return RedirectResponse(url=f"/sales/{sale_id}?avito_dismissed=1", status_code=303)


@router.get("/sales/{sale_id}/receipt", response_class=HTMLResponse)
async def sale_receipt(request: Request, sale_id: int):
    """Sale warranty and product receipt preview."""
    sale = await core_client.get_sale(sale_id)

    if sale and isinstance(sale, dict) and "error" in sale:
        if sale.get("status_code") == 404:
            return templates.TemplateResponse(
                request=request,
                name="error.html",
                context={"message": "Продажа не найдена"},
            )
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"message": "Ошибка Core API"},
        )

    # Fetch organization settings
    try:
        from app.defaults import get_effective_settings
        response = await core_client.get_organization_settings()
        org_settings = get_effective_settings(response if not response.get("error") else {})
    except Exception as e:
        from app.defaults import get_effective_settings
        org_settings = get_effective_settings({})
    
    return templates.TemplateResponse(
        request=request,
        name="sale_receipt_preview.html",
        context={
            "sale": sale,
            "payment_methods": PAYMENT_METHODS,
            "org_settings": org_settings,
        },
    )

@router.get("/sales/{sale_id}/cancel", response_class=HTMLResponse)
async def cancel_sale_form(request: Request, sale_id: int):
    sale = await core_client.get_sale(sale_id)
    if sale and isinstance(sale, dict) and "error" in sale:
        return templates.TemplateResponse(
            request=request, name="error.html", context={"message": "Продажа не найдена"}
        )
    if sale.get("status") in ["canceled", "cancelled", "superseded"]:
        return templates.TemplateResponse(
            request=request, name="error.html", context={"message": f"Продажа №{sale_id} не может быть отменена (статус: {sale.get('status')})"}
        )
        
    return templates.TemplateResponse(
        request=request, name="sale_cancel.html", context={
            "sale": sale,
            "payment_methods": PAYMENT_METHODS
        }
    )

@router.post("/sales/{sale_id}/cancel")
async def cancel_sale_endpoint(
    request: Request,
    sale_id: int,
    reason: str = Form(...),
    canceled_by: str = Form("Администратор")
):
    if not reason or not reason.strip():
        return templates.TemplateResponse(
            request=request, name="error.html", context={"message": "Причина отмены обязательна"}
        )
    res = await core_client.cancel_sale(sale_id, reason.strip(), canceled_by.strip() if canceled_by else "Администратор")
    if res and isinstance(res, dict) and "error" in res:
        return templates.TemplateResponse(
            request=request, name="error.html", context={"message": res.get("detail", "Ошибка отмены продажи")}
        )
    return RedirectResponse(url=f"/sales/{sale_id}", status_code=303)

@router.get("/sales/{sale_id}/reissue", response_class=HTMLResponse)
async def reissue_sale_form(request: Request, sale_id: int):
    sale = await core_client.get_sale(sale_id)
    if sale and isinstance(sale, dict) and "error" in sale:
        return templates.TemplateResponse(
            request=request, name="error.html", context={"message": "Продажа не найдена"}
        )
    if sale.get("status") == "superseded" or sale.get("superseded_by_sale_id") or sale.get("replaced_by_sale_id"):
        return templates.TemplateResponse(
            request=request, name="error.html", context={"message": "Исходная продажа уже была заменена"}
        )
    if sale.get("status") not in ["canceled", "cancelled"]:
        return templates.TemplateResponse(
            request=request, name="error.html", context={"message": "Повторно оформить можно только отменённую продажу"}
        )
        
    return templates.TemplateResponse(
        request=request, name="sales_reissue.html", context={
            "sale": sale,
            "payment_methods": PAYMENT_METHODS
        }
    )

@router.post("/sales/{sale_id}/reissue")
async def reissue_sale_endpoint(request: Request, sale_id: int):
    form_data = await request.form()
    reason = form_data.get("reason", "Переоформление")
    payment_method = form_data.get("payment_method", "cash")
    
    items = []
    for key, value in form_data.items():
        if key.startswith("item_product_id_"):
            idx = key.split("_")[-1]
            try:
                prod_id = int(value)
                price = float(form_data.get(f"item_price_{idx}", 0))
                qty = int(form_data.get(f"item_quantity_{idx}", 1))
                title = form_data.get(f"item_title_{idx}", "")
                if qty > 0:
                    items.append({
                        "product_id": prod_id,
                        "title": title,
                        "price": price,
                        "quantity": qty
                    })
            except ValueError:
                pass
                
    if not items:
        return templates.TemplateResponse(
            request=request, name="error.html", context={"message": "Нет товаров для переоформления"}
        )
        
    payload = {
        "reason": reason,
        "payment_method": payment_method,
        "items": items
    }
    
    res = await core_client.reissue_sale(sale_id, payload)
    if res and isinstance(res, dict) and "error" in res:
        return templates.TemplateResponse(
            request=request, name="error.html", context={"message": res.get("detail", "Ошибка переоформления")}
        )
        
    return RedirectResponse(url=f"/sales/{res.get('id')}", status_code=303)


@router.get("/sales/{sale_id}/edit", response_class=HTMLResponse)
async def edit_sale_form(request: Request, sale_id: int):
    sale = await core_client.get_sale(sale_id)
    if sale and isinstance(sale, dict) and "error" in sale:
        return templates.TemplateResponse(
            request=request, name="error.html", context={"message": "Продажа не найдена"}
        )
    if sale.get("status") in ["canceled", "cancelled", "superseded"]:
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"message": f"Продажа №{sale_id} не может быть изменена (статус: {sale.get('status')})"}
        )

    return templates.TemplateResponse(
        request=request,
        name="sales_edit.html",
        context={
            "sale": sale,
            "payment_methods": PAYMENT_METHODS,
        }
    )


@router.post("/sales/{sale_id}/edit")
async def edit_sale_endpoint(request: Request, sale_id: int):
    form_data = await request.form()
    payment_method = form_data.get("payment_method", "cash")
    comment = str(form_data.get("comment", "")).strip() or None
    changed_by = str(form_data.get("changed_by", "Администратор")).strip() or "Администратор"

    items = []
    for key, value in form_data.items():
        if key.startswith("item_product_id_"):
            idx = key.split("_")[-1]
            try:
                raw_val = str(value).strip()
                prod_id = int(raw_val) if raw_val and raw_val != "None" else None
                price = float(form_data.get(f"item_price_{idx}", 0))
                qty = int(form_data.get(f"item_quantity_{idx}", 1))
                title = str(form_data.get(f"item_title_{idx}", "")).strip()
                if qty > 0 and (prod_id is not None or title):
                    items.append({
                        "product_id": prod_id,
                        "title": title or (f"Товар #{prod_id}" if prod_id else "Позиция"),
                        "price": price,
                        "quantity": qty
                    })
            except (ValueError, TypeError):
                pass

    if not items:
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"message": "В продаже должен остаться хотя бы один товар"}
        )

    payload = {
        "payment_method": payment_method,
        "comment": comment,
        "changed_by": changed_by,
        "items": items
    }

    res = await core_client.correct_sale(sale_id, payload)
    if res and isinstance(res, dict) and "error" in res:
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"message": res.get("detail", "Ошибка корректировки продажи")}
        )

    return RedirectResponse(url=f"/sales/{sale_id}", status_code=303)


@router.get("/sales/api/product/{product_id}")
async def get_product_json(product_id: int):
    prod = await core_client.get_product(product_id)
    if not prod or (isinstance(prod, dict) and "error" in prod):
        return JSONResponse(status_code=404, content={"error": True, "message": "Товар не найден"})
    return JSONResponse(content=prod)

