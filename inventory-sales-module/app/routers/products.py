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
    limit: int = Query(50),
    offset: int = Query(0)
):
    params = {"limit": limit, "offset": offset}
    if q:
        params["q"] = q
    if status:
        params["status"] = status
        
    data = await core_client.get_products(params)
    
    if data and isinstance(data, dict) and "error" in data:
        return templates.TemplateResponse(
            request=request, name="error.html", context={
                "message": "Ошибка Core API"
            }
        )
        
    return templates.TemplateResponse(
        request=request, name="products.html", context={
            "products_data": data,
            "q": q or "",
            "status": status or "",
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
