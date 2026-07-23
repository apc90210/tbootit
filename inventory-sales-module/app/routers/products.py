from typing import Optional
from fastapi import APIRouter, Request, Query, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.core_client import core_client
from app.barcode_utils import render_barcode_svg
import os

router = APIRouter()

# Get absolute path for templates
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    health = await core_client.health()
    return templates.TemplateResponse(
        request=request, name="index.html", context={
            "core_status": health.get("core_available", False)
        }
    )

@router.get("/products", response_class=HTMLResponse)
async def list_products(
    request: Request,
    location: str = Query(None),
    q: str = Query(None),
    status: str = Query(None),
    brand: str = Query(None),
    model: str = Query(None),
    category_id: str = Query(None),
    storage_location: str = Query(None),
    avito_ready: str = Query(None),
    site_ready: str = Query(None),
    sort: str = Query(None),
    limit: int = Query(50),
    offset: int = Query(0),
    msg: str = Query(None)
):
    params = {"limit": limit, "offset": offset}
    if q and q.strip(): params["q"] = q
    if status and status.strip(): params["status"] = status
    if brand and brand.strip(): params["brand"] = brand
    if model and model.strip(): params["model"] = model
    if category_id and category_id.strip(): params["category_id"] = int(category_id)
    if location and location.strip() and location != "all": params["storage_location"] = location
    elif storage_location and storage_location.strip(): params["storage_location"] = storage_location
    if avito_ready in ("true", "false", "True", "False"): params["avito_ready"] = avito_ready.lower() == "true"
    if site_ready in ("true", "false", "True", "False"): params["site_ready"] = site_ready.lower() == "true"
    if sort and sort.strip(): params["sort"] = sort
        
    data = await core_client.get_products(params)
    
    if data and isinstance(data, dict) and "error" in data:
        return templates.TemplateResponse(
            request=request, name="error.html", context={
                "message": "Ошибка Core API"
            }
        )
        
    filter_options_response = await core_client.get_product_filter_options(params)
    filter_options_error = False
    if filter_options_response and isinstance(filter_options_response, dict) and "error" in filter_options_response:
        filter_options_error = True
        filter_options_response = {}
        
    return templates.TemplateResponse(
        request=request, name="products.html", context={
            "products_data": data,
            "filter_options": filter_options_response,
            "filter_options_error": filter_options_error,
            "q": q or "",
            "status": status or "",
            "brand": brand or "",
            "model": model or "",
            "category_id": category_id or "",
            "location": location or "all",
            "storage_location": storage_location or "",
            "avito_ready": avito_ready or "",
            "site_ready": site_ready or "",
            "sort": sort or "",
            "limit": limit,
            "offset": offset,
            "msg": msg or ""
        }
    )

@router.post("/products/barcodes/generate-missing")
async def generate_missing_barcodes_endpoint(request: Request):
    res = await core_client.generate_missing_barcodes()
    msg = f"Сгенерировано штрихкодов: {res.get('generated', 0)}, пропущено: {res.get('skipped_existing', 0)}"
    return RedirectResponse(url=f"/products?msg={msg}", status_code=303)

@router.get("/products/{product_id}", response_class=HTMLResponse)
async def product_detail(request: Request, product_id: int):
    data = await core_client.get_product_details(product_id)
    
    if data and isinstance(data, dict) and "error" in data:
        if data.get("status_code") == 404:
            return templates.TemplateResponse(
                request=request, name="error.html", context={
                    "message": "Товар не найден"
                }
            )
        return templates.TemplateResponse(
            request=request, name="error.html", context={
                "message": "Ошибка Core API"
            }
        )

    barcode_svg = ""
    if data.get("barcode") or data.get("sku"):
        barcode_svg = render_barcode_svg(data.get("barcode") or data.get("sku"))

    return templates.TemplateResponse(
        request=request, name="product_detail.html", context={
            "product": data,
            "barcode_svg": barcode_svg
        }
    )

@router.post("/products/{product_id}/barcode/generate")
async def generate_single_barcode_endpoint(request: Request, product_id: int):
    res = await core_client.generate_product_barcode(product_id)
    return RedirectResponse(url=f"/products/{product_id}", status_code=303)

@router.post("/products/{product_id}/update")
async def update_product_endpoint(request: Request, product_id: int, storage_location: str = Form(None), quantity: int = Form(None)):
    payload = {}
    if storage_location is not None:
        payload["storage_location"] = storage_location
    if quantity is not None:
        payload["quantity"] = quantity
        
    res = await core_client.update_product(product_id, payload)
    if res and isinstance(res, dict) and "error" in res:
        return templates.TemplateResponse(
            request=request, name="error.html", context={"message": "Ошибка обновления товара"}
        )
    return RedirectResponse(url=f"/products/{product_id}", status_code=303)

@router.get("/products/{product_id}/price-tag/58x40", response_class=HTMLResponse)
@router.get("/products/{product_id}/price-tag", response_class=HTMLResponse)
async def price_tag_preview(
    request: Request,
    product_id: int,
    print_price: Optional[float] = Query(None),
    warranty_text: Optional[str] = Query(None),
    condition_text: Optional[str] = Query(None)
):
    data = await core_client.get_product_details(product_id)
    
    if data and isinstance(data, dict) and "error" in data:
        if data.get("status_code") == 404:
            return templates.TemplateResponse(
                request=request, name="error.html", context={
                    "message": "Товар не найден"
                }
            )
        return templates.TemplateResponse(
            request=request, name="error.html", context={
                "message": "Ошибка Core API"
            }
        )

    # Determine display price for print (without modifying Core DB Product.price)
    default_price = float(data.get("sale_price") or data.get("price") or 0.0)
    effective_print_price = print_price if print_price is not None else default_price
    effective_warranty = warranty_text if warranty_text is not None else "Гарантия 30 дней"
    effective_condition = condition_text if condition_text is not None else (data.get("condition") or "Б/У")

    bc_val = data.get("barcode") or data.get("sku") or str(product_id)
    barcode_svg = render_barcode_svg(bc_val)

    return templates.TemplateResponse(
        request=request, name="price_tag_preview.html", context={
            "product": data,
            "print_price": effective_print_price,
            "warranty_text": effective_warranty,
            "condition_text": effective_condition,
            "barcode_svg": barcode_svg,
            "barcode_value": bc_val
        }
    )
