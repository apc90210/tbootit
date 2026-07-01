from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os
import httpx

app = FastAPI(title="Technoreboot Admin Shell")
templates = Jinja2Templates(directory="app/templates")

CORE_API_URL = os.getenv("CORE_API_URL", "http://127.0.0.1:8000")

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    async with httpx.AsyncClient() as client:
        try:
            stats_resp = await client.get(f"{CORE_API_URL}/api/admin/stats")
            stats = stats_resp.json() if stats_resp.status_code == 200 else {}
        except Exception:
            stats = {"error": "Core API offline"}
            
        try:
            products_resp = await client.get(f"{CORE_API_URL}/api/products/")
            products = products_resp.json() if products_resp.status_code == 200 else []
        except Exception:
            products = []
            
        try:
            customers_resp = await client.get(f"{CORE_API_URL}/api/customers/")
            customers = customers_resp.json() if customers_resp.status_code == 200 else []
        except Exception:
            customers = []

    return templates.TemplateResponse("index.html", {
        "request": request, 
        "stats": stats, 
        "products": products,
        "customers": customers,
        "core_url": CORE_API_URL
    })
