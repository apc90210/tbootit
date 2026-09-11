from typing import Optional, Any
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


@router.post("/products/batch-action")
async def products_batch_action(request: Request):
    content_type = request.headers.get("content-type", "")
    action = None
    new_status = None
    new_location = None
    product_ids = []

    if "application/json" in content_type:
        body = await request.json()
        action = body.get("action")
        new_status = body.get("status") or body.get("new_status")
        new_location = body.get("storage_location") or body.get("new_location") or body.get("location")
        product_ids = [int(x) for x in body.get("product_ids", []) if str(x).isdigit()]
    else:
        form = await request.form()
        action = form.get("action")
        new_status = form.get("new_status") or form.get("status")
        new_location = form.get("new_location") or form.get("storage_location") or form.get("location")
        raw_ids = form.getlist("product_ids[]") or form.getlist("product_ids") or []
        if not raw_ids and form.get("ids"):
            raw_ids = str(form.get("ids")).split(",")
        product_ids = [int(str(x).strip()) for x in raw_ids if str(x).strip().isdigit()]

    is_ajax = "application/json" in request.headers.get("accept", "") or request.headers.get("x-requested-with") == "XMLHttpRequest"

    if not product_ids:
        err = "Не выбрано ни одного товара"
        if is_ajax:
            return JSONResponse({"error": True, "detail": err}, status_code=400)
        return RedirectResponse(f"/inventory/products?error={err}", status_code=303)

    status_names = {"draft": "Черновик", "in_stock": "В наличии", "reserved": "В резерве", "sold": "Продан", "archived": "В архиве", "written_off": "Списан"}
    loc_names = {"store": "Магазин", "workshop": "Мастерская", "archive": "Архив", "draft": "Черновик"}

    if action in ["apply_changes", "update_fields", "set_status", "set_location"]:
        if action == "set_status" and not new_status:
            err = "Не выбран статус"
            if is_ajax:
                return JSONResponse({"error": True, "detail": err}, status_code=400)
            return RedirectResponse(f"/inventory/products?error={err}", status_code=303)

        if action == "set_location" and not new_location:
            err = "Не указано место хранения"
            if is_ajax:
                return JSONResponse({"error": True, "detail": err}, status_code=400)
            return RedirectResponse(f"/inventory/products?error={err}", status_code=303)

        if not new_status and not new_location:
            err = "Не выбран статус или место хранения для применения"
            if is_ajax:
                return JSONResponse({"error": True, "detail": err}, status_code=400)
            return RedirectResponse(f"/inventory/products?error={err}", status_code=303)

        payload = {"product_ids": product_ids}
        msg_parts = []
        if new_status:
            payload["status"] = new_status
            msg_parts.append(f"статус «{status_names.get(new_status, new_status)}»")
        if new_location:
            payload["storage_location"] = new_location
            msg_parts.append(f"место «{loc_names.get(new_location, new_location)}»")

        payload["comment"] = f"Массовое обновление: {', '.join(msg_parts)}"
        res = await core_client.batch_update_products(payload)
        if is_ajax:
            return JSONResponse(res)

        import urllib.parse
        msg_str = f"Для {len(product_ids)} товаров успешно обновлено: {', '.join(msg_parts)}"
        encoded = urllib.parse.quote_plus(msg_str)
        return RedirectResponse(f"/inventory/products?msg={encoded}", status_code=303)


    elif action == "add_to_cart":
        cart = request.session.get("cart", [])
        added_count = 0
        skipped_count = 0
        for pid in product_ids:
            p_data = await core_client.get_product_details(pid)
            if not p_data or p_data.get("error"):
                skipped_count += 1
                continue
            p_status = p_data.get("status")
            p_loc = p_data.get("storage_location")
            p_qty = p_data.get("quantity", 0)
            if p_status in ['in_stock', 'reserved'] and p_loc == 'store' and p_qty > 0:
                p_title = p_data.get("title", f"Товар #{pid}")
                p_price = float(p_data.get("sale_price") or p_data.get("price") or 0.0)
                for item in cart:
                    if item.get("product_id") == pid:
                        item["quantity"] = item.get("quantity", 1) + 1
                        break
                else:
                    cart.append({
                        "product_id": pid,
                        "title": p_title,
                        "price": p_price,
                        "quantity": 1
                    })
                added_count += 1
            else:
                skipped_count += 1
        request.session["cart"] = cart
        if is_ajax:
            return JSONResponse({"success": True, "added": added_count, "skipped": skipped_count, "cart_total": len(cart)})
        return RedirectResponse("/inventory/cart", status_code=303)

    elif action == "print_price_tags":
        ids_str = ",".join(str(x) for x in product_ids)
        return RedirectResponse(f"/inventory/products/price-tags/batch?ids={ids_str}", status_code=303)

    else:
        err = f"Неизвестное действие: {action}"
        if is_ajax:
            return JSONResponse({"error": True, "detail": err}, status_code=400)
        return RedirectResponse(f"/inventory/products?error={err}", status_code=303)


@router.get("/products/price-tags/batch", response_class=HTMLResponse)
@router.post("/products/price-tags/batch", response_class=HTMLResponse)
async def price_tags_batch_preview(
    request: Request,
    ids: Optional[str] = Query(None),
    warranty_text: Optional[str] = Query(None),
    condition_text: Optional[str] = Query(None)
):
    if request.method == "POST":
        form = await request.form()
        if not ids:
            raw_ids = form.getlist("product_ids[]") or form.getlist("product_ids") or []
            if not raw_ids and form.get("ids"):
                raw_ids = str(form.get("ids")).split(",")
            ids = ",".join(str(x).strip() for x in raw_ids if str(x).strip().isdigit())
        if not warranty_text:
            warranty_text = form.get("warranty_text")
        if not condition_text:
            condition_text = form.get("condition_text")

    if not ids:
        return templates.TemplateResponse(
            request=request, name="error.html", context={"message": "Не указаны товары для печати ценников"}
        )

    product_ids = [int(x.strip()) for x in ids.split(",") if x.strip().isdigit()]
    if not product_ids:
        return templates.TemplateResponse(
            request=request, name="error.html", context={"message": "Список товаров для печати пуст"}
        )

    effective_warranty = warranty_text if warranty_text is not None else "Гарантия 30 дней"
    effective_condition = condition_text if condition_text is not None else "Б/У"

    tags = []
    for pid in product_ids:
        p_data = await core_client.get_product_details(pid)
        if not p_data or p_data.get("error"):
            continue

        p_price = float(p_data.get("sale_price") or p_data.get("price") or 0.0)
        bc_val = p_data.get("barcode") or p_data.get("sku") or str(pid)
        bc_svg = render_barcode_svg(bc_val)

        tags.append({
            "id": pid,
            "title": p_data.get("title", f"Товар #{pid}"),
            "sku": p_data.get("sku") or str(pid),
            "barcode_value": bc_val,
            "barcode_svg": bc_svg,
            "price": p_price,
            "formatted_price": "{:,.0f}".format(p_price).replace(",", " "),
            "warranty": effective_warranty,
            "condition": p_data.get("condition") or effective_condition
        })

    return templates.TemplateResponse(
        request=request, name="price_tag_batch.html", context={
            "tags": tags,
            "total_tags": len(tags),
            "warranty_text": effective_warranty,
            "condition_text": effective_condition,
            "ids_string": ids
        }
    )




def format_core_error(detail: Any) -> str:
    """Format Core API errors into clean, friendly Russian messages without raw Pydantic output or URLs."""
    if not detail:
        return "Ошибка обработки данных на сервере"

    if isinstance(detail, str):
        detail_clean = detail.strip()
        if (detail_clean.startswith("[") and detail_clean.endswith("]")) or "pydantic" in detail_clean.lower() or "float_type" in detail_clean:
            try:
                detail = json.loads(detail_clean)
            except Exception:
                import ast
                try:
                    parsed = ast.literal_eval(detail_clean)
                    if isinstance(parsed, (list, dict)):
                        detail = parsed
                except Exception:
                    pass

    if isinstance(detail, list):
        field_labels = {
            "sale_price": "Цена продажи",
            "price": "Цена продажи",
            "purchase_price": "Закупочная цена",
            "cost_price": "Закупочная цена",
            "title": "Название товара",
            "quantity": "Количество",
            "sku": "Артикул (SKU)",
            "barcode": "Штрихкод",
            "status": "Статус",
            "storage_location": "Место хранения",
            "category": "Категория",
        }
        messages = []
        for item in detail:
            if isinstance(item, dict):
                loc = item.get("loc", [])
                field = str(loc[-1]) if loc else ""
                err_type = str(item.get("type", ""))
                msg = str(item.get("msg", ""))
                label = field_labels.get(field, field or "Поле")

                if "float" in err_type or "int" in err_type or "number" in err_type or "valid number" in msg.lower():
                    messages.append(f"{label} должна быть корректным числом.")
                elif "missing" in err_type or "required" in msg.lower():
                    messages.append(f"{label} обязательно для заполнения.")
                elif "greater_than" in err_type:
                    messages.append(f"{label} должно быть больше нуля.")
                else:
                    import re
                    clean_msg = re.sub(r'https?://\S+', '', msg).strip()
                    messages.append(f"{label}: {clean_msg}")
            elif isinstance(item, str):
                messages.append(item)
        if messages:
            return "Не удалось сохранить товар: " + " ".join(messages)

    import re
    result = re.sub(r'https?://\S+', '', str(detail)).strip()
    return result


def _extract_product_payload(form_data, existing_product=None):
    title = str(form_data.get("title") or "").strip()
    if not title and existing_product:
        title = str(existing_product.get("title") or "").strip()

    category = str(form_data.get("category") or "").strip()
    if category == "__custom__":
        category = str(form_data.get("category_custom") or "").strip()
    if not category and existing_product:
        category = str(existing_product.get("category") or "").strip()

    brand = str(form_data.get("brand") or "").strip() or None
    if not brand and existing_product:
        brand = existing_product.get("brand")

    model = str(form_data.get("model") or "").strip() or None
    if not model and existing_product:
        model = existing_product.get("model")

    condition = str(form_data.get("condition") or "").strip() or None
    if not condition and existing_product:
        condition = existing_product.get("condition")

    # Sale price: accept sale_price or price, normalize comma to dot
    sale_price_raw = form_data.get("sale_price")
    if sale_price_raw is None:
        sale_price_raw = form_data.get("price")

    sale_price = None
    if sale_price_raw is not None and str(sale_price_raw).strip():
        val_str = str(sale_price_raw).replace(",", ".").strip()
        try:
            sale_price = float(val_str)
        except (ValueError, TypeError):
            sale_price = -999.0  # Parsing error sentinel
    elif sale_price_raw is None and existing_product is not None:
        sale_price = existing_product.get("sale_price")
        if sale_price is None:
            sale_price = existing_product.get("price")

    # Cost / Purchase price
    cost_price_raw = form_data.get("cost_price")
    if cost_price_raw is None:
        cost_price_raw = form_data.get("purchase_price")

    cost_price = None
    if cost_price_raw is not None and str(cost_price_raw).strip():
        val_cost = str(cost_price_raw).replace(",", ".").strip()
        try:
            cost_price = float(val_cost)
        except (ValueError, TypeError):
            cost_price = -999.0
    elif cost_price_raw is None and existing_product is not None:
        cost_price = existing_product.get("purchase_price")
        if cost_price is None:
            cost_price = existing_product.get("cost_price")

    quantity_raw = form_data.get("quantity")
    if quantity_raw is not None and str(quantity_raw).strip():
        try:
            quantity = int(quantity_raw)
        except (ValueError, TypeError):
            quantity = -1
    elif quantity_raw is None and existing_product is not None:
        quantity = existing_product.get("quantity", 0)
    else:
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

    if not characteristics and existing_product and existing_product.get("characteristics"):
        characteristics = dict(existing_product.get("characteristics"))

    return {
        "title": title,
        "category": category or None,
        "brand": brand,
        "model": model,
        "condition": condition,
        "sale_price": sale_price,
        "price": sale_price,
        "purchase_price": cost_price,
        "cost_price": cost_price,
        "quantity": quantity,
        "status": status,
        "storage_location": storage_location,
        "sku": sku,
        "barcode": barcode,
        "description": description,
        "characteristics": characteristics,
    }


def _validate_product_payload(payload, is_new=False, existing_product=None):
    if not payload.get("title") or not str(payload.get("title")).strip():
        return "Название товара обязательно для заполнения"

    sale_price = payload.get("sale_price")
    if sale_price is None or sale_price == -999.0:
        if not is_new and existing_product and existing_product.get("sale_price") is None and sale_price is None:
            pass
        else:
            return "Укажите корректную цену продажи."
    elif sale_price < 0:
        return "Цена продажи не может быть отрицательной."

    cost_price = payload.get("cost_price")
    if cost_price is not None and cost_price < 0:
        return "Закупочная цена должна быть неотрицательной."

    qty = payload.get("quantity")
    if qty is None or qty < 0:
        return "Количество должно быть неотрицательным целым числом."

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
    err = _validate_product_payload(payload, is_new=True)
    if err:
        meta = await core_client.get_editor_meta()
        ctx = _prepare_editor_context(request, is_new=True, product=payload, meta=meta, error=err)
        return templates.TemplateResponse(request=request, name="product_edit.html", context=ctx, status_code=400)

    res = await core_client.create_product(payload)
    if res and isinstance(res, dict) and res.get("error"):
        meta = await core_client.get_editor_meta()
        detail = format_core_error(res.get("detail") or res.get("details") or "Ошибка создания товара")
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
    existing = await core_client.get_product_details(product_id)
    existing_dict = existing if existing and isinstance(existing, dict) and not existing.get("error") else None
    payload = _extract_product_payload(form_data, existing_product=existing_dict)
    err = _validate_product_payload(payload, is_new=False, existing_product=existing_dict)
    if err:
        meta = await core_client.get_editor_meta()
        product_view = dict(payload)
        product_view["id"] = product_id
        if existing_dict:
            product_view["photos"] = existing_dict.get("photos", [])
        ctx = _prepare_editor_context(request, is_new=False, product=product_view, meta=meta, error=err)
        return templates.TemplateResponse(request=request, name="product_edit.html", context=ctx, status_code=400)

    res = await core_client.full_update_product(product_id, payload)
    if res and isinstance(res, dict) and res.get("error"):
        meta = await core_client.get_editor_meta()
        product_view = dict(payload)
        product_view["id"] = product_id
        if existing_dict:
            product_view["photos"] = existing_dict.get("photos", [])
        detail = format_core_error(res.get("detail") or res.get("details") or "Ошибка обновления товара")
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


