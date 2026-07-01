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

        try:
            repairs_resp = await client.get(f"{CORE_API_URL}/api/repairs/")
            repairs = repairs_resp.json() if repairs_resp.status_code == 200 else []
        except Exception:
            repairs = []

        try:
            sales_resp = await client.get(f"{CORE_API_URL}/api/sales/")
            sales = sales_resp.json() if sales_resp.status_code == 200 else []
        except Exception:
            sales = []

        try:
            schema_resp = await client.get(f"{CORE_API_URL}/api/admin/db/schema")
            db_schema = schema_resp.json() if schema_resp.status_code == 200 else {}
        except Exception:
            db_schema = {}

        try:
            audit_resp = await client.get(f"{CORE_API_URL}/api/admin/audit-log")
            audit_log = audit_resp.json() if audit_resp.status_code == 200 else []
        except Exception:
            audit_log = []

    return templates.TemplateResponse("index.html", {
        "request": request, 
        "stats": stats, 
        "products": products,
        "customers": customers,
        "repairs": repairs,
        "sales": sales,
        "db_schema": db_schema,
        "audit_log": audit_log,
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

@app.post("/admin-api/products")
async def proxy_create_product(request: Request):
    data = await request.json()
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{CORE_API_URL}/api/products/", json=data)
            if resp.status_code == 200:
                return resp.json()
            raise HTTPException(status_code=resp.status_code, detail=f"Core API error: {resp.text}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Failed to connect to Core API: {str(e)}")

@app.post("/admin-api/customers")
async def proxy_create_customer(request: Request):
    data = await request.json()
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{CORE_API_URL}/api/customers/", json=data)
            if resp.status_code == 200:
                return resp.json()
            raise HTTPException(status_code=resp.status_code, detail=f"Core API error: {resp.text}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Failed to connect to Core API: {str(e)}")

@app.post("/admin-api/repairs")
async def proxy_create_repair(request: Request):
    data = await request.json()
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{CORE_API_URL}/api/repairs/", json=data)
            if resp.status_code == 200:
                return resp.json()
            raise HTTPException(status_code=resp.status_code, detail=f"Core API error: {resp.text}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Failed to connect to Core API: {str(e)}")

@app.patch("/admin-api/repairs/{repair_id}/status")
async def proxy_repair_status(repair_id: int, status_update: StatusUpdate):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.patch(
                f"{CORE_API_URL}/api/repairs/{repair_id}/status",
                json=status_update.model_dump()
            )
            if resp.status_code == 200:
                return resp.json()
            raise HTTPException(status_code=resp.status_code, detail=f"Core API error: {resp.text}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Failed to connect to Core API: {str(e)}")

@app.post("/admin-api/sales")
async def proxy_create_sale(request: Request):
    data = await request.json()
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{CORE_API_URL}/api/sales/", json=data)
            if resp.status_code == 200:
                return resp.json()
            raise HTTPException(status_code=resp.status_code, detail=f"Core API error: {resp.text}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Failed to connect to Core API: {str(e)}")

@app.post("/admin-api/dev-reset")
async def proxy_dev_reset():
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{CORE_API_URL}/api/admin/dev-reset")
            if resp.status_code == 200:
                return resp.json()
            raise HTTPException(status_code=resp.status_code, detail=f"Core API error: {resp.text}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Failed to connect to Core API: {str(e)}")
