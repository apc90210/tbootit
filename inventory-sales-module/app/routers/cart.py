from typing import Optional
from fastapi import APIRouter, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.core_client import core_client
from app import schemas

router = APIRouter(prefix="/cart", tags=["cart"])
templates = Jinja2Templates(directory="app/templates")

def get_cart(request: Request):
    return request.session.get("cart", [])

def set_cart(request: Request, cart: list):
    request.session["cart"] = cart

@router.get("", response_class=HTMLResponse)
async def view_cart(request: Request, scanner_error: str = None):
    cart = get_cart(request)
    total_amount = sum(item["price"] * item["quantity"] for item in cart)
    
    return templates.TemplateResponse(
        request=request,
        name="cart.html",
        context={
            "request": request,
            "cart": cart,
            "total_amount": total_amount,
            "PAYMENT_METHODS": schemas.PAYMENT_METHODS,
            "active_page": "sales",
            "scanner_error": scanner_error or ""
        }
    )

@router.post("/scan")
async def scan_barcode_to_cart(request: Request, barcode: str = Form(...)):
    barcode_clean = barcode.strip()
    if not barcode_clean:
        return await view_cart(request, scanner_error="Пожалуйста, введите или отсканируйте штрихкод.")

    # Strictly query Core API by barcode ONLY (no fallback to SKU/ID search)
    res = await core_client.get_product_by_barcode(barcode_clean)
    
    if not res or not isinstance(res, dict) or res.get("error"):
        return await view_cart(request, scanner_error=f"Товар с таким штрихкодом не найден ({barcode_clean}).")

    product = res
    prod_status = product.get("status")
    prod_qty = product.get("quantity", 0)
    storage_loc = product.get("storage_location")
    title = product.get("title", f"Товар #{product.get('id')}")
    price = float(product.get("sale_price") or product.get("price") or 0.0)

    # Check status sellability
    if prod_status == "reserved":
        return await view_cart(request, scanner_error="Товар найден, но зарезервирован и недоступен для продажи.")
    if prod_status == "sold":
        return await view_cart(request, scanner_error="Товар уже продан и недоступен для продажи.")
    if prod_status == "draft":
        return await view_cart(request, scanner_error="Товар ещё не готов к продаже.")
    if prod_status not in ["in_stock", "available"]:
        return await view_cart(request, scanner_error=f"Товар '{title}' недоступен для продажи (статус: {prod_status}).")

    # Check quantity
    if prod_qty <= 0:
        return await view_cart(request, scanner_error="Товар найден, но отсутствует в остатках.")

    # Check location
    if storage_loc and storage_loc not in ["store", "склад", "магазин", "витрина"]:
        return await view_cart(request, scanner_error=f"Товар находится в локации '{storage_loc}' и недоступен для продажи из магазина.")

    # Product is valid and available -> add to cart
    cart = get_cart(request)
    product_id = product["id"]
    for item in cart:
        if item["product_id"] == product_id:
            item["quantity"] += 1
            break
    else:
        cart.append({
            "product_id": product_id,
            "title": title,
            "price": price,
            "quantity": 1
        })
        
    set_cart(request, cart)
    return RedirectResponse(url="/cart", status_code=303)

@router.post("/add")
@router.post("/add/{path_product_id}")
async def add_to_cart(
    request: Request,
    path_product_id: Optional[int] = None,
    product_id: Optional[int] = Form(None),
    title: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    quantity: int = Form(1)
):
    target_id = path_product_id or product_id
    if not target_id:
        return await view_cart(request, scanner_error="Не указан ID товара.")
    
    # Fetch Core product details if title or price is missing
    if title is None or price is None:
        product_res = await core_client.get_product(target_id)
        if not product_res or not isinstance(product_res, dict) or product_res.get("error"):
            return await view_cart(request, scanner_error=f"Товар #{target_id} не найден.")
        
        prod_status = product_res.get("status")
        prod_qty = product_res.get("quantity", 0)
        storage_loc = product_res.get("storage_location")
        
        if prod_status == "reserved":
            return await view_cart(request, scanner_error="Товар найден, но зарезервирован и недоступен для продажи.")
        if prod_status == "sold":
            return await view_cart(request, scanner_error="Товар уже продан.")
        if prod_status == "draft":
            return await view_cart(request, scanner_error="Товар ещё не готов к продаже.")
        if prod_status not in ["in_stock", "available"]:
            return await view_cart(request, scanner_error=f"Товар недоступен для продажи (статус: {prod_status}).")
        if prod_qty <= 0:
            return await view_cart(request, scanner_error="Товар отсутствует в остатках.")
        if storage_loc and storage_loc not in ["store", "склад", "магазин", "витрина"]:
            return await view_cart(request, scanner_error=f"Товар находится в локации '{storage_loc}' и недоступен для продажи из магазина.")
        
        title = title or product_res.get("title", f"Товар #{target_id}")
        raw_price = product_res.get("sale_price") if product_res.get("sale_price") is not None else product_res.get("price")
        price = price if price is not None else float(raw_price or 0.0)

    cart = get_cart(request)
    for item in cart:
        if item["product_id"] == target_id:
            item["quantity"] += max(1, quantity)
            break
    else:
        cart.append({
            "product_id": target_id,
            "title": title,
            "price": max(0.0, float(price)),
            "quantity": max(1, quantity)
        })
        
    set_cart(request, cart)
    return RedirectResponse(url="/cart", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/update")
async def update_cart_item(
    request: Request,
    product_id: int = Form(...),
    quantity: int = Form(...),
    price: float = Form(...)
):
    cart = get_cart(request)
    for item in cart:
        if item["product_id"] == product_id:
            item["quantity"] = max(1, quantity)
            item["price"] = max(0.0, price)
            break
            
    set_cart(request, cart)
    return RedirectResponse(url="/cart", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/remove")
async def remove_cart_item(
    request: Request,
    product_id: int = Form(...)
):
    cart = [item for item in get_cart(request) if item["product_id"] != product_id]
    set_cart(request, cart)
    return RedirectResponse(url="/cart", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/clear")
async def clear_cart(request: Request):
    set_cart(request, [])
    return RedirectResponse(url="/cart", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/checkout")
async def checkout_cart(
    request: Request,
    payment_method: str = Form("cash"),
    notes: str = Form(""),
    warranty_enabled: str = Form("off"),
    warranty_days: int = Form(30)
):
    cart = get_cart(request)
    if not cart:
        return RedirectResponse(url="/cart", status_code=status.HTTP_303_SEE_OTHER)
        
    total_amount = sum(item["price"] * item["quantity"] for item in cart)
    is_warranty_active = warranty_enabled in ["on", "true", "1", "True"]
    
    payload = {
        "customer_id": None,
        "total_amount": total_amount,
        "payment_method": payment_method,
        "comment": notes or "",
        "warranty_enabled": is_warranty_active,
        "warranty_days": warranty_days if is_warranty_active else None,
        "items": [
            {
                "product_id": item["product_id"],
                "title": item["title"],
                "price": float(item["price"]),
                "quantity": int(item["quantity"])
            }
            for item in cart
        ]
    }
    
    try:
        sale_data = await core_client.create_sale(payload)
        if sale_data and isinstance(sale_data, dict) and sale_data.get("error"):
            err_msg = sale_data.get("detail") or "Ошибка оформления продажи в Core API"
            return await view_cart(request, scanner_error=f"Ошибка создания продажи: {err_msg}")
        
        sale_id = sale_data.get("id")
        if not sale_id:
            return await view_cart(request, scanner_error="Core API не вернул ID продажи.")
        
        # Clear cart ONLY on SUCCESS
        set_cart(request, [])
        return RedirectResponse(url=f"/sales/{sale_id}", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        return await view_cart(request, scanner_error=f"Сбой системы при оформлении продажи: {str(e)}")
