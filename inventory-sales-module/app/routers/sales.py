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


@router.get("/sales/new", response_class=HTMLResponse)
async def sale_new(
    request: Request,
    product_id: int = Query(...),
):
    """Sale form — fetches product from Core and renders form."""
    product = await core_client.get_product_details(product_id)

    if product and isinstance(product, dict) and "error" in product:
        if product.get("status_code") == 404:
            return templates.TemplateResponse(
                request=request,
                name="error.html",
                context={"message": "Товар не найден"},
            )
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"message": "Ошибка Core API"},
        )

    product_status = product.get("status", "")
    can_sell = product_status in SELLABLE_STATUSES

    return templates.TemplateResponse(
        request=request,
        name="sales_new.html",
        context={
            "product": product,
            "can_sell": can_sell,
            "payment_methods": PAYMENT_METHODS,
            "status_labels": STATUS_LABELS,
        },
    )


@router.post("/sales/create", response_class=HTMLResponse)
async def sale_create(
    request: Request,
    product_id: int = Form(...),
    price: float = Form(...),
    quantity: int = Form(1),
    payment_method: str = Form(...),
    warranty_days: int = Form(30),
    no_warranty: bool = Form(False),
    notes: str = Form(""),
):
    """Create sale via Core API."""
    # Validate payment method
    if payment_method not in PAYMENT_METHODS:
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"message": "Некорректный способ оплаты"},
        )
        
    if quantity < 1:
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"message": "Количество должно быть больше 0"},
        )
        
    if price < 0:
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"message": "Цена продажи не может быть отрицательной"},
        )

    # Fetch product to set title in sale item
    product = await core_client.get_product(product_id)
    if product and isinstance(product, dict) and "error" in product:
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"message": "Товар не найден"},
        )

    warranty_enabled = not no_warranty

    result = await core_client.create_sale(
        product_id=product_id,
        price=price,
        quantity=quantity,
        payment_method=payment_method,
        notes=notes or None,
        warranty_days=warranty_days,
        warranty_enabled=warranty_enabled,
    )

    if result and isinstance(result, dict) and "error" in result:
        # Translate common Core errors to Russian
        detail = result.get("detail", "")
        if "Cannot sell product" in str(detail):
            message = "Товар нельзя продать в текущем статусе"
        elif "not found" in str(detail).lower():
            message = "Товар не найден"
        elif "Invalid payment method" in str(detail):
            message = "Некорректный способ оплаты"
        elif "already" in str(detail).lower():
            message = "Товар уже продан"
        else:
            message = f"Ошибка Core API: {result}"

        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"message": message},
        )

    sale_id = result.get("id")
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

    # We also need the item details if we want to show product details,
    # but the sale response contains items.
    
    return templates.TemplateResponse(
        request=request,
        name="sale_receipt_preview.html",
        context={
            "sale": sale,
            "payment_methods": PAYMENT_METHODS,
        },
    )
