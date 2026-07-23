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

    # Query core API for product
    res = await core_client.get_product_by_barcode(barcode_clean)
    
    product = None
    if res and isinstance(res, dict) and not res.get("error"):
        product = res
    else:
        # Fallback to general search query
        search_res = await core_client.get_products({"q": barcode_clean, "limit": 1})
        if search_res and isinstance(search_res, dict) and not search_res.get("error") and search_res.get("items"):
            product = search_res["items"][0]

    if not product:
        return await view_cart(request, scanner_error=f"Товар со штрихкодом '{barcode_clean}' не найден.")

    # Check product status and location
    prod_status = product.get("status")
    prod_qty = product.get("quantity", 0)
    title = product.get("title", f"Товар #{product.get('id')}")
    price = float(product.get("sale_price") or product.get("price") or 0.0)

    if prod_status not in ["in_stock", "reserved"] or prod_qty <= 0:
        status_labels = {
            "sold": "Продан",
            "reserved": "В резерве",
            "draft": "Черновик",
            "in_repair": "В ремонте",
            "written_off": "Списан"
        }
        st_lbl = status_labels.get(prod_status, prod_status)
        return await view_cart(
            request,
            scanner_error=f"Товар '{title}' найден (ID #{product.get('id')}), но сейчас недоступен для продажи (статус: {st_lbl}, остаток: {prod_qty} шт.)."
        )

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
    return RedirectResponse(url="/cart", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/add")
async def add_to_cart(
    request: Request,
    product_id: int = Form(...),
    title: str = Form(...),
    price: float = Form(...)
):
    cart = get_cart(request)
    
    # Check if item already in cart
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
    
    payload = {
        "customer_id": None,
        "total_amount": total_amount,
        "payment_method": payment_method,
        "comment": notes,
        "warranty_enabled": warranty_enabled == "on",
        "warranty_days": warranty_days if warranty_enabled == "on" else 0,
        "items": cart
    }
    
    try:
        sale_data = await core_client.create_sale(payload)
        if sale_data and isinstance(sale_data, dict) and sale_data.get("error"):
            # If error creating sale, just redirect back
            return RedirectResponse(url="/cart", status_code=status.HTTP_303_SEE_OTHER)
        
        sale_id = sale_data.get("id")
        
        # Clear cart
        set_cart(request, [])
        return RedirectResponse(url=f"/sales/{sale_id}", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        # MVP: simply redirect back to cart if fails
        return RedirectResponse(url="/cart", status_code=status.HTTP_303_SEE_OTHER)
