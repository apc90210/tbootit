from typing import Optional
from fastapi import APIRouter, Request, Query, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.core_client import core_client
from app.schemas import SELLABLE_STATUSES, PAYMENT_METHODS, STATUS_LABELS, SALE_STATUS_LABELS
import os

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


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
        },
    )



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

    return templates.TemplateResponse(
        request=request,
        name="sales_detail.html",
        context={
            "sale": sale,
            "payment_methods": PAYMENT_METHODS,
            "sale_status_labels": SALE_STATUS_LABELS,
        },
    )

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
