from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from app.routers import health, products, sales, settings as settings_router, cart, reports
from app.config import settings
import os

app = FastAPI(title="Inventory and Sales Module")

# Add session middleware for cart
app.add_middleware(SessionMiddleware, secret_key=settings.cart_session_secret)

# Static files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Include routers
app.include_router(health.router)
app.include_router(products.router)
app.include_router(sales.router)
app.include_router(settings_router.router)
app.include_router(cart.router)
app.include_router(reports.router)

# Include routers under /inventory prefix for direct route compatibility
app.include_router(products.router, prefix="/inventory")
app.include_router(sales.router, prefix="/inventory")
app.include_router(settings_router.router, prefix="/inventory")
app.include_router(cart.router, prefix="/inventory")
app.include_router(reports.router, prefix="/inventory")

@app.get("/", response_class=HTMLResponse)
async def root():
    return RedirectResponse(url="/inventory/products")
