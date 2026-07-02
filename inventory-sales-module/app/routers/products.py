from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.core_client import core_client
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
    q: str = Query(None),
    status: str = Query(None),
    brand: str = Query(None),
    model: str = Query(None),
    category_id: int = Query(None),
    storage_location: str = Query(None),
    avito_ready: str = Query(None),
    site_ready: str = Query(None),
    sort: str = Query(None),
    limit: int = Query(50),
    offset: int = Query(0)
):
    params = {"limit": limit, "offset": offset}
    if q: params["q"] = q
    if status: params["status"] = status
    if brand: params["brand"] = brand
    if model: params["model"] = model
    if category_id: params["category_id"] = category_id
    if storage_location: params["storage_location"] = storage_location
    if avito_ready in ("true", "false", "True", "False"): params["avito_ready"] = avito_ready.lower() == "true"
    if site_ready in ("true", "false", "True", "False"): params["site_ready"] = site_ready.lower() == "true"
    if sort: params["sort"] = sort
        
    data = await core_client.get_products(params)
    
    if data and isinstance(data, dict) and "error" in data:
        return templates.TemplateResponse(
            request=request, name="error.html", context={
                "message": "Ошибка Core API"
            }
        )
        
    filter_options_response = await core_client.get_product_filter_options()
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
            "storage_location": storage_location or "",
            "avito_ready": avito_ready or "",
            "site_ready": site_ready or "",
            "sort": sort or "",
            "limit": limit,
            "offset": offset
        }
    )

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

    return templates.TemplateResponse(
        request=request, name="product_detail.html", context={
            "product": data
        }
    )
