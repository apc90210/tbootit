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
):
    """List of recent sales (MVP)."""
    params = {"limit": limit, "offset": offset}
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
            "payment_methods": PAYMENT_METHODS,
            "sale_status_labels": SALE_STATUS_LABELS,
        },
    )



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
    # We also need the item details if we want to show product details,
    # but the sale response contains items.
    
    return templates.TemplateResponse(
        request=request,
        name="sale_receipt_preview.html",
        context={
            "sale": sale,
            "payment_methods": PAYMENT_METHODS,
            "org_settings": org_settings,
        },
    )

@router.post("/sales/{sale_id}/cancel")
async def cancel_sale_endpoint(request: Request, sale_id: int, reason: str = Form(...)):
    res = await core_client.cancel_sale(sale_id, reason)
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
    if sale.get("status") != "completed":
        return templates.TemplateResponse(
            request=request, name="error.html", context={"message": "Переоформить можно только завершенную продажу"}
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
