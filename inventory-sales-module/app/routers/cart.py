from fastapi import APIRouter, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.core_client import core_client

router = APIRouter(prefix="/cart", tags=["cart"])
templates = Jinja2Templates(directory="app/templates")

def get_cart(request: Request):
    return request.session.get("cart", [])

def set_cart(request: Request, cart: list):
    request.session["cart"] = cart

@router.get("", response_class=HTMLResponse)
async def view_cart(request: Request):
    cart = get_cart(request)
    total_amount = sum(item["price"] * item["quantity"] for item in cart)
    
    return templates.TemplateResponse(
        request=request,
        name="cart.html",
        context={
            "request": request,
            "cart": cart,
            "total_amount": total_amount,
            "active_page": "sales"
        }
    )

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
