from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
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

class StatusUpdate(BaseModel):
    status: str

@app.post("/admin-api/seed")
async def proxy_seed():
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{CORE_API_URL}/api/admin/seed")
            if resp.status_code == 200:
                return resp.json()
            raise HTTPException(status_code=resp.status_code, detail=f"Core API error: {resp.text}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Failed to connect to Core API: {str(e)}")

@app.patch("/admin-api/products/{product_id}/status")
async def proxy_product_status(product_id: int, status_update: StatusUpdate):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.patch(
                f"{CORE_API_URL}/api/products/{product_id}/status",
                json=status_update.model_dump()
            )
            if resp.status_code == 200:
                return resp.json()
            raise HTTPException(status_code=resp.status_code, detail=f"Core API error: {resp.text}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Failed to connect to Core API: {str(e)}")
