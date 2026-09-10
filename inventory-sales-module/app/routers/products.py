from typing import Optional
from fastapi import APIRouter, Request, Query, Form, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.core_client import core_client
from app.barcode_utils import render_barcode_svg
import os
import json

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
        
    cart = request.session.get("cart", [])
    cart_items_count = sum(item.get("quantity", 1) for item in cart if isinstance(item, dict))
    cart_quantities_by_product_id = {
        int(item["product_id"]): int(item.get("quantity", 1))
        for item in cart
        if isinstance(item, dict) and "product_id" in item
    }
    cart_product_ids = set(cart_quantities_by_product_id.keys())

    return templates.TemplateResponse(
        request=request, name="products.html", context={
            "products_data": data,
            "cart_items_count": cart_items_count,
            "cart_quantities_by_product_id": cart_quantities_by_product_id,
            "cart_product_ids": cart_product_ids,
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
    return RedirectResponse(url=f"/inventory/products?msg={msg}", status_code=303)


def _extract_product_payload(form_data):
    title = str(form_data.get("title") or "").strip()
    category = str(form_data.get("category") or "").strip()
    if category == "__custom__":
        category = str(form_data.get("category_custom") or "").strip()
    brand = str(form_data.get("brand") or "").strip() or None
    model = str(form_data.get("model") or "").strip() or None
    condition = str(form_data.get("condition") or "").strip() or None

    try:
        price = float(form_data.get("price") or 0.0)
    except (ValueError, TypeError):
        price = 0.0

    sale_price_raw = form_data.get("sale_price")
    sale_price = None
    if sale_price_raw is not None and str(sale_price_raw).strip():
        try:
            sale_price = float(sale_price_raw)
        except (ValueError, TypeError):
            sale_price = None

    cost_price_raw = form_data.get("cost_price")
    cost_price = None
    if cost_price_raw is not None and str(cost_price_raw).strip():
        try:
            cost_price = float(cost_price_raw)
        except (ValueError, TypeError):
            cost_price = None

    try:
        quantity = int(form_data.get("quantity") or 0)
    except (ValueError, TypeError):
        quantity = 0

    status = str(form_data.get("status") or "in_stock").strip()
    storage_location = str(form_data.get("storage_location") or "store").strip()
    sku = str(form_data.get("sku") or "").strip() or None
    barcode = str(form_data.get("barcode") or "").strip() or None
    description = str(form_data.get("description") or "").strip() or None

    characteristics = {}
    for k, v in form_data.items():
        if k.startswith("char_"):
            char_name = k[5:].strip()
            char_val = str(v).strip()
            if char_name and char_val:
                characteristics[char_name] = char_val

    custom_names = form_data.getlist("custom_char_name[]")
    custom_vals = form_data.getlist("custom_char_val[]")
    for cn, cv in zip(custom_names, custom_vals):
        cn_str = str(cn).strip()
        cv_str = str(cv).strip()
        if cn_str and cv_str:
            characteristics[cn_str] = cv_str

    return {
        "title": title,
        "category": category or None,
        "brand": brand,
        "model": model,
        "condition": condition,
        "price": price,
        "sale_price": sale_price,
        "cost_price": cost_price,
        "quantity": quantity,
        "status": status,
        "storage_location": storage_location,
        "sku": sku,
        "barcode": barcode,
        "description": description,
        "characteristics": characteristics,
    }


def _validate_product_payload(payload):
    if not payload.get("title"):
        return "Название товара обязательно для заполнения"
    if payload.get("price", 0) < 0:
        return "Базовая цена не может быть отрицательной"
    if payload.get("sale_price") is not None and payload["sale_price"] < 0:
        return "Цена продажи не может быть отрицательной"
    if payload.get("cost_price") is not None and payload["cost_price"] < 0:
        return "Себестоимость не может быть отрицательной"
    if payload.get("quantity", 0) < 0:
        return "Количество не может быть отрицательным"
    return None


def _prepare_editor_context(request: Request, is_new: bool, product: dict, meta: dict, msg: Optional[str] = None, error: Optional[str] = None) -> dict:
    chars = product.get("characteristics") or product.get("avito_characteristics") or {}
    initial_characteristics_json = json.dumps(chars, ensure_ascii=False)
    schemas = meta.get("standard_characteristics") or meta.get("category_characteristics") or {}
    category_schemas_json = json.dumps(schemas, ensure_ascii=False)
    return {
        "request": request,
        "is_new": is_new,
        "product": product,
        "meta": meta,
        "initial_characteristics_json": initial_characteristics_json,
        "category_schemas_json": category_schemas_json,
        "msg": msg,
        "error": error,
    }


@router.get("/products/new", response_class=HTMLResponse)
async def new_product_form(request: Request):
    meta = await core_client.get_editor_meta()
    ctx = _prepare_editor_context(request, is_new=True, product={}, meta=meta, msg=request.query_params.get("msg"), error=request.query_params.get("error"))
    return templates.TemplateResponse(request=request, name="product_edit.html", context=ctx)


@router.post("/products/new", response_class=HTMLResponse)
async def create_product_endpoint(request: Request):
    form_data = await request.form()
    payload = _extract_product_payload(form_data)
    err = _validate_product_payload(payload)
    if err:
        meta = await core_client.get_editor_meta()
        ctx = _prepare_editor_context(request, is_new=True, product=payload, meta=meta, error=err)
        return templates.TemplateResponse(request=request, name="product_edit.html", context=ctx, status_code=400)

    res = await core_client.create_product(payload)
    if res and isinstance(res, dict) and res.get("error"):
        meta = await core_client.get_editor_meta()
        detail = res.get("detail") or "Ошибка создания товара"
        ctx = _prepare_editor_context(request, is_new=True, product=payload, meta=meta, error=detail)
        return templates.TemplateResponse(request=request, name="product_edit.html", context=ctx, status_code=400)

    new_id = res.get("id")
    return RedirectResponse(url=f"/inventory/products/{new_id}/edit?msg=Товар+успешно+создан", status_code=303)


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

    cart = request.session.get("cart", [])
    cart_items_count = sum(item.get("quantity", 1) for item in cart if isinstance(item, dict))
    cart_quantities_by_product_id = {
        int(item["product_id"]): int(item.get("quantity", 1))
        for item in cart
        if isinstance(item, dict) and "product_id" in item
    }
    cart_product_ids = set(cart_quantities_by_product_id.keys())

    return templates.TemplateResponse(
        request=request, name="product_detail.html", context={
            "product": data,
            "barcode_svg": barcode_svg,
            "cart_items_count": cart_items_count,
            "cart_quantities_by_product_id": cart_quantities_by_product_id,
            "cart_product_ids": cart_product_ids
        }
    )

@router.post("/products/{product_id}/barcode/generate")
async def generate_single_barcode_endpoint(request: Request, product_id: int):
    res = await core_client.generate_product_barcode(product_id)
    return RedirectResponse(url=f"/inventory/products/{product_id}", status_code=303)

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
    return RedirectResponse(url=f"/inventory/products/{product_id}", status_code=303)


@router.get("/products/{product_id}/edit", response_class=HTMLResponse)
async def edit_product_form(request: Request, product_id: int):
    product = await core_client.get_product_details(product_id)
    if product and isinstance(product, dict) and product.get("error"):
        return templates.TemplateResponse(
            request=request, name="error.html", context={"message": "Товар не найден"}
        )
    meta = await core_client.get_editor_meta()
    ctx = _prepare_editor_context(request, is_new=False, product=product, meta=meta, msg=request.query_params.get("msg"), error=request.query_params.get("error"))
    return templates.TemplateResponse(request=request, name="product_edit.html", context=ctx)


@router.post("/products/{product_id}/edit", response_class=HTMLResponse)
async def update_product_full_endpoint(request: Request, product_id: int):
    form_data = await request.form()
    payload = _extract_product_payload(form_data)
    err = _validate_product_payload(payload)
    if err:
        meta = await core_client.get_editor_meta()
        existing = await core_client.get_product_details(product_id)
        product_view = dict(payload)
        product_view["id"] = product_id
        if existing and isinstance(existing, dict):
            product_view["photos"] = existing.get("photos", [])
        ctx = _prepare_editor_context(request, is_new=False, product=product_view, meta=meta, error=err)
        return templates.TemplateResponse(request=request, name="product_edit.html", context=ctx, status_code=400)

    res = await core_client.full_update_product(product_id, payload)
    if res and isinstance(res, dict) and res.get("error"):
        meta = await core_client.get_editor_meta()
        existing = await core_client.get_product_details(product_id)
        product_view = dict(payload)
        product_view["id"] = product_id
        if existing and isinstance(existing, dict):
            product_view["photos"] = existing.get("photos", [])
        detail = res.get("detail") or "Ошибка обновления товара"
        ctx = _prepare_editor_context(request, is_new=False, product=product_view, meta=meta, error=detail)
        return templates.TemplateResponse(request=request, name="product_edit.html", context=ctx, status_code=400)

    return RedirectResponse(url=f"/inventory/products/{product_id}/edit?msg=Изменения+успешно+сохранены", status_code=303)


@router.post("/products/{product_id}/photos/upload")
async def upload_photos_endpoint(request: Request, product_id: int):
    form = await request.form()
    files = form.getlist("files")
    files_data = []
    for f in files:
        if hasattr(f, "filename") and f.filename:
            content = await f.read()
            files_data.append((f.filename, content, getattr(f, "content_type", "application/octet-stream")))

    is_ajax = "application/json" in request.headers.get("accept", "") or request.headers.get("x-requested-with") == "XMLHttpRequest"
    if not files_data:
        if is_ajax:
            return JSONResponse({"error": True, "detail": "Файлы не выбраны"}, status_code=400)
        return RedirectResponse(f"/inventory/products/{product_id}/edit?error=Файлы+не+выбраны", status_code=303)

    res = await core_client.upload_product_photos_batch(product_id, files_data)
    if is_ajax:
        if res.get("error"):
            return JSONResponse(res, status_code=res.get("status_code", 400))
        return JSONResponse(res)

    if res.get("error"):
        err_msg = res.get("detail") or "Ошибка загрузки файлов"
        return RedirectResponse(f"/inventory/products/{product_id}/edit?error={err_msg}", status_code=303)
    return RedirectResponse(f"/inventory/products/{product_id}/edit?msg=Фотографии+успешно+загружены", status_code=303)


@router.post("/products/{product_id}/photos/{photo_id}/make-main")
async def make_main_photo_endpoint(request: Request, product_id: int, photo_id: int):
    res = await core_client.make_product_photo_main(product_id, photo_id)
    is_ajax = "application/json" in request.headers.get("accept", "") or request.headers.get("x-requested-with") == "XMLHttpRequest"
    if is_ajax:
        if isinstance(res, dict) and res.get("error"):
            return JSONResponse(res, status_code=res.get("status_code", 400))
        return JSONResponse(res if isinstance(res, (dict, list)) else {"success": True})
    return RedirectResponse(f"/inventory/products/{product_id}/edit?msg=Главное+фото+обновлено", status_code=303)


@router.post("/products/{product_id}/photos/{photo_id}/delete")
async def delete_photo_endpoint(request: Request, product_id: int, photo_id: int):
    res = await core_client.delete_product_photo(product_id, photo_id)
    is_ajax = "application/json" in request.headers.get("accept", "") or request.headers.get("x-requested-with") == "XMLHttpRequest"
    if is_ajax:
        if isinstance(res, dict) and res.get("error"):
            return JSONResponse(res, status_code=res.get("status_code", 400))
        return JSONResponse(res if isinstance(res, (dict, list)) else {"success": True})
    return RedirectResponse(f"/inventory/products/{product_id}/edit?msg=Фотография+удалена", status_code=303)


@router.post("/products/{product_id}/photos/reorder")
async def reorder_photos_endpoint(request: Request, product_id: int):
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        body = await request.json()
        photo_ids = body.get("photo_ids", [])
    else:
        form = await request.form()
        photo_ids_raw = form.getlist("photo_ids[]") or form.getlist("photo_ids")
        photo_ids = [int(x) for x in photo_ids_raw if str(x).isdigit()]

    res = await core_client.reorder_product_photos(product_id, photo_ids)
    is_ajax = "application/json" in request.headers.get("accept", "") or request.headers.get("x-requested-with") == "XMLHttpRequest"
    if is_ajax:
        if isinstance(res, dict) and res.get("error"):
            return JSONResponse(res, status_code=res.get("status_code", 400))
        return JSONResponse(res if isinstance(res, (dict, list)) else {"success": True})
    return RedirectResponse(f"/inventory/products/{product_id}/edit?msg=Порядок+фото+обновлен", status_code=303)


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
