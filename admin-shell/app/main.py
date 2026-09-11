from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, Response, JSONResponse, FileResponse, RedirectResponse
from starlette.background import BackgroundTask
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import json
import os
import httpx
import asyncio
import urllib.parse
import tempfile
from pathlib import Path

from app.auth_manager import AuthManager
from app import backup_service


app = FastAPI(title="Technoreboot Admin Shell")
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)
auth_manager = AuthManager()




CORE_API_URL = os.getenv("CORE_API_URL", "http://127.0.0.1:8000")
AVITO_MODULE_URL = os.getenv("AVITO_MODULE_URL", "http://127.0.0.1:8020")
AVITO_NOVNC_URL = os.getenv("AVITO_NOVNC_URL", "http://127.0.0.1:6080")
INVENTORY_MODULE_URL = os.getenv("INVENTORY_MODULE_URL", "http://127.0.0.1:8030")
REPAIRS_MODULE_URL = os.getenv("REPAIRS_MODULE_URL", "http://127.0.0.1:8040")


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    async with httpx.AsyncClient(trust_env=False) as client:
        try:
            stats_resp = await client.get(f"{CORE_API_URL}/api/admin/stats")
            stats = stats_resp.json() if stats_resp.status_code == 200 else {}
        except Exception:
            stats = {"error": "Core API offline"}
            
        try:
            params = dict(request.query_params)
            products_resp = await client.get(f"{CORE_API_URL}/api/products/", params=params)
            products = products_resp.json() if products_resp.status_code == 200 else []
        except Exception:
            products = []
            
        try:
            meta_resp = await client.get(f"{CORE_API_URL}/api/products/meta")
            product_meta = meta_resp.json() if meta_resp.status_code == 200 else {}
        except Exception:
            product_meta = {}

            
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
        "product_meta": product_meta,
        "current_query": dict(request.query_params),
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
    async with httpx.AsyncClient(trust_env=False) as client:
        try:
            resp = await client.post(f"{CORE_API_URL}/api/admin/seed")
            if resp.status_code == 200:
                return resp.json()
            raise HTTPException(status_code=resp.status_code, detail=f"Core API error: {resp.text}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Failed to connect to Core API: {str(e)}")

@app.patch("/admin-api/products/{product_id}/status")
async def proxy_product_status(product_id: int, status_update: StatusUpdate):
    async with httpx.AsyncClient(trust_env=False) as client:
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
    async with httpx.AsyncClient(trust_env=False) as client:
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
    async with httpx.AsyncClient(trust_env=False) as client:
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
    async with httpx.AsyncClient(trust_env=False) as client:
        try:
            resp = await client.post(f"{CORE_API_URL}/api/repairs/", json=data)
            if resp.status_code == 200:
                return resp.json()
            raise HTTPException(status_code=resp.status_code, detail=f"Core API error: {resp.text}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Failed to connect to Core API: {str(e)}")

@app.patch("/admin-api/repairs/{repair_id}/status")
async def proxy_repair_status(repair_id: int, status_update: StatusUpdate):
    async with httpx.AsyncClient(trust_env=False) as client:
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
    async with httpx.AsyncClient(trust_env=False) as client:
        try:
            resp = await client.post(f"{CORE_API_URL}/api/sales/", json=data)
            if resp.status_code == 200:
                return resp.json()
            raise HTTPException(status_code=resp.status_code, detail=f"Core API error: {resp.text}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Failed to connect to Core API: {str(e)}")

@app.post("/admin-api/dev-reset")
async def proxy_dev_reset():
    async with httpx.AsyncClient(trust_env=False) as client:
        try:
            resp = await client.post(f"{CORE_API_URL}/api/admin/dev-reset")
            if resp.status_code == 200:
                return resp.json()
            raise HTTPException(status_code=resp.status_code, detail=f"Core API error: {resp.text}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Failed to connect to Core API: {str(e)}")

@app.get("/admin-api/products/{product_id}/details")
async def proxy_product_details(product_id: int):
    async with httpx.AsyncClient(trust_env=False) as client:
        try:
            resp = await client.get(f"{CORE_API_URL}/api/products/{product_id}/details")
            if resp.status_code == 200:
                return resp.json()
            raise HTTPException(status_code=resp.status_code, detail=f"Core API error: {resp.text}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Failed to connect to Core API: {str(e)}")

@app.get("/admin-api/products/{product_id}/avito-attributes")
async def proxy_product_avito_attributes(product_id: int):
    async with httpx.AsyncClient(trust_env=False) as client:
        try:
            resp = await client.get(f"{CORE_API_URL}/api/v1/products/{product_id}/avito-attributes")
            if resp.status_code == 200:
                return resp.json()
            raise HTTPException(status_code=resp.status_code, detail=f"Core API error: {resp.text}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Failed to connect to Core API: {str(e)}")

@app.get("/admin-api/avito/categories/{category_id}/schema")
async def proxy_avito_category_schema(category_id: int):
    async with httpx.AsyncClient(trust_env=False) as client:
        try:
            resp = await client.get(f"{CORE_API_URL}/api/v1/avito/categories/{category_id}/schema")
            if resp.status_code == 200:
                return resp.json()
            raise HTTPException(status_code=resp.status_code, detail=f"Core API error: {resp.text}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Failed to connect to Core API: {str(e)}")

@app.post("/admin-api/products/{product_id}/stock-adjustment")
async def proxy_stock_adjustment(product_id: int, request: Request):
    data = await request.json()
    async with httpx.AsyncClient(trust_env=False) as client:
        try:
            resp = await client.post(f"{CORE_API_URL}/api/products/{product_id}/stock-adjustment", json=data)
            if resp.status_code == 200:
                return resp.json()
            raise HTTPException(status_code=resp.status_code, detail=f"Core API error: {resp.text}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Failed to connect to Core API: {str(e)}")

@app.patch("/admin-api/products/{product_id}/site-publication")
async def proxy_site_publication(product_id: int, request: Request):
    data = await request.json()
    async with httpx.AsyncClient(trust_env=False) as client:
        try:
            resp = await client.patch(f"{CORE_API_URL}/api/products/{product_id}/site-publication", json=data)
            if resp.status_code == 200:
                return resp.json()
            raise HTTPException(status_code=resp.status_code, detail=f"Core API error: {resp.text}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Failed to connect to Core API: {str(e)}")

@app.patch("/admin-api/products/{product_id}/avito-publication")
async def proxy_avito_publication(product_id: int, request: Request):
    data = await request.json()
    async with httpx.AsyncClient(trust_env=False) as client:
        try:
            resp = await client.patch(f"{CORE_API_URL}/api/products/{product_id}/avito-publication", json=data)
            if resp.status_code == 200:
                return resp.json()
            raise HTTPException(status_code=resp.status_code, detail=f"Core API error: {resp.text}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Failed to connect to Core API: {str(e)}")

@app.post("/admin-api/product-cards/validate-json")
async def proxy_validate_json(request: Request):
    data = await request.json()
    async with httpx.AsyncClient(trust_env=False) as client:
        try:
            resp = await client.post(f"{CORE_API_URL}/api/product-cards/validate-json", json=data)
            return resp.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Failed to connect to Core API: {str(e)}")

@app.post("/admin-api/product-cards/import-json")
async def proxy_import_json(request: Request):
    data = await request.json()
    async with httpx.AsyncClient(trust_env=False) as client:
        try:
            resp = await client.post(f"{CORE_API_URL}/api/product-cards/import-json", json=data)
            return resp.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Failed to connect to Core API: {str(e)}")

@app.get("/admin-api/product-cards/imports")
async def proxy_imports_list():
    async with httpx.AsyncClient(trust_env=False) as client:
        try:
            resp = await client.get(f"{CORE_API_URL}/api/product-cards/imports")
            if resp.status_code == 200:
                return resp.json()
            raise HTTPException(status_code=resp.status_code, detail=f"Core API error: {resp.text}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Failed to connect to Core API: {str(e)}")

# =====================================================================
# AVITO INTEGRATED SETTINGS & ZERO-CLI OWNER UI ROUTES
# =====================================================================

@app.get("/avito", response_class=HTMLResponse)
async def avito_dashboard(request: Request):
    async with httpx.AsyncClient(trust_env=False) as client:
        try:
            prof_resp = await client.get(f"{AVITO_MODULE_URL}/accounts/api/profiles")
            profiles = prof_resp.json() if prof_resp.status_code == 200 else []
        except Exception:
            profiles = []

        try:
            runs_resp = await client.get(f"{AVITO_MODULE_URL}/health")
            runs = []
        except Exception:
            runs = []

    auth_count = sum(1 for p in profiles if p.get("auth_status") == "authorized")
    return templates.TemplateResponse("avito.html", {
        "request": request,
        "profiles": profiles,
        "authorized_count": auth_count,
        "runs": runs
    })

@app.get("/avito/accounts", response_class=HTMLResponse)
async def avito_accounts_page(request: Request):
    async with httpx.AsyncClient(trust_env=False) as client:
        try:
            prof_resp = await client.get(f"{AVITO_MODULE_URL}/accounts/api/profiles")
            profiles = prof_resp.json() if prof_resp.status_code == 200 else []
        except Exception:
            profiles = []

    return templates.TemplateResponse("avito_accounts.html", {
        "request": request,
        "profiles": profiles
    })

@app.get("/avito/accounts/{account_key}/browser", response_class=HTMLResponse)
async def avito_browser_page(account_key: str, request: Request):
    async with httpx.AsyncClient(trust_env=False) as client:
        try:
            prof_resp = await client.get(f"{AVITO_MODULE_URL}/accounts/api/profiles")
            profiles = prof_resp.json() if prof_resp.status_code == 200 else []
            profile = next((p for p in profiles if p.get("account_key") == account_key), None)
            if not profile:
                return templates.TemplateResponse("avito_profile_not_found.html", {
                    "request": request,
                    "account_key": account_key
                }, status_code=404)
        except Exception:
            return templates.TemplateResponse("avito_profile_not_found.html", {
                "request": request,
                "account_key": account_key
            }, status_code=404)

    return templates.TemplateResponse("avito_browser.html", {
        "request": request,
        "profile": profile
    })

@app.get("/avito/probe", response_class=HTMLResponse)
async def avito_probe_page(request: Request, account: str = None):
    async with httpx.AsyncClient(trust_env=False) as client:
        try:
            prof_resp = await client.get(f"{AVITO_MODULE_URL}/accounts/api/profiles")
            profiles = prof_resp.json() if prof_resp.status_code == 200 else []
        except Exception:
            profiles = []

    selected_account = account or (profiles[0]["account_key"] if profiles else "")
    return templates.TemplateResponse("avito_probe.html", {
        "request": request,
        "profiles": profiles,
        "selected_account": selected_account
    })

@app.get("/avito/health")
async def avito_health_proxy():
    async with httpx.AsyncClient(trust_env=False) as client:
        try:
            resp = await client.get(f"{AVITO_MODULE_URL}/health/details", timeout=5)
            if resp.status_code == 200:
                return resp.json()
            return {"module": "error", "core": "error", "browser_runtime": "error", "xvfb": "error", "vnc": "error", "novnc": "error", "chromium": "error", "profile_storage": "error"}
        except Exception:
            return {"module": "offline", "core": "offline", "browser_runtime": "offline", "xvfb": "offline", "vnc": "offline", "novnc": "offline", "chromium": "offline", "profile_storage": "offline"}

# --- Avito API Proxies ---

@app.get("/admin-api/avito/profiles")
async def proxy_get_profiles():
    async with httpx.AsyncClient(trust_env=False) as client:
        resp = await client.get(f"{AVITO_MODULE_URL}/accounts/api/profiles")
        return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")

@app.post("/admin-api/avito/profiles")
async def proxy_create_profile(request: Request):
    data = await request.json()
    async with httpx.AsyncClient(trust_env=False) as client:
        resp = await client.post(f"{AVITO_MODULE_URL}/accounts/api/profiles", json=data)
        return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")

@app.delete("/admin-api/avito/profiles/{account_key}")
async def proxy_delete_profile(account_key: str):
    async with httpx.AsyncClient(trust_env=False) as client:
        resp = await client.delete(f"{AVITO_MODULE_URL}/accounts/api/profiles/{account_key}")
        return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")

@app.post("/admin-api/avito/profiles/{account_key}/launch-browser")
async def proxy_launch_browser(account_key: str):
    async with httpx.AsyncClient(trust_env=False) as client:
        resp = await client.post(f"{AVITO_MODULE_URL}/accounts/api/profiles/{account_key}/launch-browser")
        return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")

@app.post("/admin-api/avito/profiles/{account_key}/stop-browser")
async def proxy_stop_browser(account_key: str):
    async with httpx.AsyncClient(trust_env=False) as client:
        resp = await client.post(f"{AVITO_MODULE_URL}/accounts/api/profiles/{account_key}/stop-browser")
        return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")

@app.get("/admin-api/avito/profiles/{account_key}/browser-status")
async def proxy_browser_status(account_key: str):
    async with httpx.AsyncClient(trust_env=False) as client:
        resp = await client.get(f"{AVITO_MODULE_URL}/accounts/api/profiles/{account_key}/browser-status")
        return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")

@app.post("/admin-api/avito/profiles/{account_key}/check-auth")
async def proxy_check_auth(account_key: str):
    async with httpx.AsyncClient(trust_env=False) as client:
        resp = await client.post(f"{AVITO_MODULE_URL}/accounts/api/profiles/{account_key}/check-auth")
        return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")

@app.get("/admin-api/avito/profiles/{account_key}/discover")
async def proxy_discover(account_key: str, scope: str = "active"):
    async with httpx.AsyncClient(trust_env=False) as client:
        resp = await client.get(f"{AVITO_MODULE_URL}/accounts/api/profiles/{account_key}/discover?scope={scope}")
        return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")

@app.get("/admin-api/avito/profiles/{account_key}/preview/{item_id}")
async def proxy_preview(account_key: str, item_id: str):
    async with httpx.AsyncClient(trust_env=False) as client:
        resp = await client.get(f"{AVITO_MODULE_URL}/accounts/api/profiles/{account_key}/preview/{item_id}")
        return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")

@app.post("/admin-api/avito/profiles/{account_key}/probe-import")
async def proxy_probe_import(account_key: str, request: Request):
    data = await request.json()
    async with httpx.AsyncClient(trust_env=False) as client:
        resp = await client.post(f"{AVITO_MODULE_URL}/accounts/api/profiles/{account_key}/probe-import", json=data)
        return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")

@app.post("/admin-api/avito/profiles/{account_key}/verify-probe")
async def proxy_verify_probe(account_key: str):
    async with httpx.AsyncClient(trust_env=False) as client:
        resp = await client.post(f"{AVITO_MODULE_URL}/accounts/api/profiles/{account_key}/verify-probe")
        return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")

@app.post("/admin-api/avito/profiles/{account_key}/import")
async def proxy_start_import(account_key: str, request: Request):
    data = await request.form()
    async with httpx.AsyncClient(trust_env=False) as client:
        resp = await client.post(f"{AVITO_MODULE_URL}/accounts/api/profiles/{account_key}/import", data=data)
        return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")

# --- Extension Bridge Proxy Routes ---

@app.get("/avito/extension", response_class=HTMLResponse)
async def avito_extension_page(request: Request):
    async with httpx.AsyncClient(trust_env=False) as client:
        try:
            status_resp = await client.get(f"{AVITO_MODULE_URL}/extension/api/status")
            status_data = status_resp.json() if status_resp.status_code == 200 else {"online": False}
        except Exception:
            status_data = {"online": False}

        try:
            ingest_resp = await client.get(f"{AVITO_MODULE_URL}/extension/api/last-ingest")
            last_ingest = ingest_resp.json() if ingest_resp.status_code == 200 else None
        except Exception:
            last_ingest = None

    return templates.TemplateResponse("avito_extension.html", {
        "request": request,
        "extension_status": status_data,
        "last_ingest": last_ingest
    })

@app.get("/avito/extension/download")
async def download_extension_zip():
    version = "0.2.53"
    try:
        for manifest_candidate in [
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "chrome-extension", "technoreboot-avito", "manifest.json")),
            "/chrome-extension/technoreboot-avito/manifest.json"
        ]:
            if os.path.exists(manifest_candidate):
                with open(manifest_candidate, "r", encoding="utf-8") as f:
                    version = json.load(f).get("version", version)
                break
    except Exception:
        pass
    filename = f"technoreboot-avito-extension-{version}.zip"
    candidate_paths = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), filename)),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "technoreboot-avito-extension.zip")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "app", filename)),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "app", "technoreboot-avito-extension.zip")),
        os.path.abspath(f"/app/{filename}"),
        os.path.abspath(f"/app/app/{filename}"),
        os.path.abspath(f"dist/{filename}"),
        os.path.abspath(f"admin-shell/app/{filename}"),
    ]
    zip_path = None
    for p in candidate_paths:
        if os.path.exists(p):
            zip_path = p
            break
    if not zip_path or not os.path.exists(zip_path):
        raise HTTPException(status_code=404, detail="Файл расширения не найден.")
    
    return FileResponse(
        zip_path,
        filename=filename,
        media_type="application/zip",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"}
    )

@app.api_route("/admin-api/avito-extension/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_avito_extension_api(path: str, request: Request):
    target_url = f"{AVITO_MODULE_URL}/extension/api/{path}"
    query = str(request.query_params)
    if query:
        target_url = f"{target_url}?{query}"
    headers = dict(request.headers)
    headers.pop("host", None)
    body = await request.body()
    try:
        async with httpx.AsyncClient(trust_env=False, timeout=60.0) as client:
            resp = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body if body else None
            )
            media_type = resp.headers.get("content-type", "application/json")
            if resp.status_code >= 400 and "application/json" not in media_type:
                text_content = resp.text.strip()
                return JSONResponse(
                    status_code=resp.status_code,
                    content={
                        "ok": False,
                        "status": "failed",
                        "detail": f"Модуль Avito вернул ошибку {resp.status_code}: {text_content or 'Internal Server Error'}"
                    }
                )
            return Response(content=resp.content, status_code=resp.status_code, media_type=media_type)
    except httpx.TimeoutException as e:
        return JSONResponse(
            status_code=504,
            content={"ok": False, "status": "failed", "detail": f"Превышено время ожидания ответа от модуля Avito (60с): {str(e)}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "status": "failed", "detail": f"Ошибка проксирования запроса к модулю Avito: {str(e)}"}
        )

# --- noVNC Static Asset & WebSocket Proxies ---

@app.get("/avito/novnc/{path:path}")
async def proxy_novnc_static(path: str):
    async with httpx.AsyncClient(trust_env=False) as client:
        try:
            target_url = f"{AVITO_NOVNC_URL.rstrip('/')}/{path}"
            resp = await client.get(target_url, timeout=10)
            return Response(
                content=resp.content,
                status_code=resp.status_code,
                headers=dict(resp.headers)
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"noVNC proxy error: {str(e)}")

@app.websocket("/avito/novnc/websockify")
async def novnc_websocket_proxy(websocket: WebSocket):
    sec_proto = websocket.headers.get("sec-websocket-protocol")
    subprotocols = []
    selected_subprotocol = None
    if sec_proto:
        subprotocols = [p.strip() for p in sec_proto.split(",") if p.strip()]
        if "binary" in subprotocols:
            selected_subprotocol = "binary"
        elif subprotocols:
            selected_subprotocol = subprotocols[0]

    await websocket.accept(subprotocol=selected_subprotocol)

    import websockets
    target_host = AVITO_NOVNC_URL.replace("http://", "ws://").replace("https://", "wss://")
    target_url = f"{target_host.rstrip('/')}/websockify"

    try:
        async with websockets.connect(target_url, subprotocols=subprotocols if subprotocols else None) as target_ws:
            async def client_to_target():
                try:
                    while True:
                        msg = await websocket.receive()
                        if msg.get("type") == "websocket.disconnect":
                            break
                        if "bytes" in msg and msg["bytes"] is not None:
                            await target_ws.send(msg["bytes"])
                        elif "text" in msg and msg["text"] is not None:
                            await target_ws.send(msg["text"])
                except Exception:
                    pass
                finally:
                    try:
                        await target_ws.close()
                    except Exception:
                        pass

            async def target_to_client():
                try:
                    async for msg in target_ws:
                        if isinstance(msg, bytes):
                            await websocket.send_bytes(msg)
                        elif isinstance(msg, str):
                            await websocket.send_text(msg)
                except Exception:
                    pass
                finally:
                    try:
                        await websocket.close()
                    except Exception:
                        pass

            await asyncio.gather(client_to_target(), target_to_client(), return_exceptions=True)
    except Exception as e:
        try:
            await websocket.close(code=1011, reason=str(e))
        except Exception:
            pass


# =====================================================================
# SAME-ORIGIN REVERSE PROXY FOR INVENTORY-SALES MODULE
# =====================================================================

import re

def rewrite_location_header(loc: str, prefix: str) -> str:
    if not loc:
        return loc
    path = re.sub(r'^https?://[^/]+', '', loc)
    if not path.startswith('/'):
        path = '/' + path
    for p in ["/inventory", "/repairs", "/avito"]:
        if path == p or path.startswith(p + "/"):
            return path
    prefix_clean = prefix.rstrip('/')
    return f"{prefix_clean}{path}"

async def _proxy_request(request: Request, target_base_url: str, path: str, prefix: str):
    """Generic HTTP reverse proxy handler with header and location rewriting."""
    target_url = f"{target_base_url.rstrip('/')}/{path}"
    query = str(request.query_params)
    if query:
        target_url = f"{target_url}?{query}"

    headers = dict(request.headers)
    headers.pop("host", None)
    headers["x-forwarded-host"] = request.headers.get("host", "localhost:8011")
    headers["x-forwarded-port"] = "8011"
    headers["x-forwarded-proto"] = request.url.scheme or "http"
    headers["x-forwarded-prefix"] = prefix

    body = await request.body()
    method = request.method

    async with httpx.AsyncClient(trust_env=False, timeout=30.0, follow_redirects=False) as client:
        resp = await client.request(
            method=method,
            url=target_url,
            headers=headers,
            content=body if body else None,
        )

    # Rewrite Location header for redirects
    resp_headers = dict(resp.headers)
    if "location" in resp_headers:
        resp_headers["location"] = rewrite_location_header(resp_headers["location"], prefix)

    # Remove hop-by-hop headers
    for h in ["transfer-encoding", "content-encoding", "content-length"]:
        resp_headers.pop(h, None)

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=resp_headers,
    )


@app.api_route("/inventory/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_inventory(request: Request, path: str):
    return await _proxy_request(request, INVENTORY_MODULE_URL, path, "/inventory")


@app.api_route("/repairs/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_repairs(request: Request, path: str):
    return await _proxy_request(request, REPAIRS_MODULE_URL, path, "/repairs")


@app.api_route("/media/{path:path}", methods=["GET", "HEAD"])
async def proxy_media(request: Request, path: str):
    return await _proxy_request(request, CORE_API_URL, f"media/{path}", "/media")


@app.get("/products/json", response_class=HTMLResponse)
async def products_json_page(request: Request):
    """
    Dedicated Web page for Product JSON Import, Export, and AI Prompt Generator.
    """
    schema_data = {}
    products_list = []
    async with httpx.AsyncClient(trust_env=False) as client:
        try:
            resp = await client.get(f"{CORE_API_URL}/api/products/json/schema", timeout=10.0)
            if resp.status_code == 200:
                schema_data = resp.json()
        except Exception:
            schema_data = {}

        try:
            resp_prod = await client.get(f"{CORE_API_URL}/api/products/", params={"limit": 1000}, timeout=15.0)
            if resp_prod.status_code == 200:
                prod_json = resp_prod.json()
                products_list = prod_json.get("items", []) if isinstance(prod_json, dict) else prod_json
        except Exception:
            products_list = []

    ai_prompt = schema_data.get("ai_prompt", "")
    return templates.TemplateResponse("products_json.html", {
        "request": request,
        "ai_prompt": ai_prompt,
        "schema_data": schema_data,
        "products": products_list,
        "core_url": CORE_API_URL,
    })



@app.get("/products/new")
async def redirect_products_new_shortcut():
    return RedirectResponse(url="/inventory/products/new", status_code=302)


@app.get("/products/{product_id}/edit")
async def redirect_products_edit_shortcut(product_id: int):
    return RedirectResponse(url=f"/inventory/products/{product_id}/edit", status_code=302)


@app.get("/products/{product_id}")
async def redirect_products_detail_shortcut(product_id: int):
    return RedirectResponse(url=f"/inventory/products/{product_id}", status_code=302)


@app.get("/products")
async def redirect_products_list_shortcut():
    return RedirectResponse(url="/inventory/products", status_code=302)


# ============================================================================
# Stage 07A-R1: Minimal Certificate Access Gateway & Admin Routes
# ============================================================================

class CreateCertRequest(BaseModel):
    name: str


@app.get("/internal-auth/verify")
async def internal_auth_verify(request: Request):
    """
    Internal mTLS validation subrequest invoked by Nginx gateway.
    Verifies client certificate against Technoreboot CA and registry status.
    """
    verify_status = request.headers.get("x-client-cert-verify")
    client_serial = request.headers.get("x-client-cert-serial")
    client_fingerprint = request.headers.get("x-client-cert-fingerprint")
    request_uri = request.headers.get("x-original-uri", "/")

    ok, status_code, msg, cert = auth_manager.verify_request(
        verify_status=verify_status,
        client_serial=client_serial,
        client_fingerprint=client_fingerprint,
        request_uri=request_uri,
    )

    if not ok:
        raise HTTPException(status_code=status_code, detail=msg)

    return JSONResponse(
        content={
            "status": "ok",
            "cert_id": cert["id"] if cert else None,
            "name": cert["name"] if cert else None,
            "is_owner": cert["is_owner"] if cert else False,
        },
        headers={
            "X-Auth-Subject": urllib.parse.quote(str(cert["name"])) if cert else "",
            "X-Auth-Is-Owner": "1" if (cert and cert.get("is_owner")) else "0",
        },
    )


def _require_owner(request: Request):
    client_serial = request.headers.get("x-client-cert-serial")
    if not client_serial:
        raise HTTPException(status_code=403, detail="Owner certificate required")
    ok, code, msg, cert = auth_manager.verify_request(
        request.headers.get("x-client-cert-verify", "SUCCESS"),
        client_serial,
        request.headers.get("x-client-cert-fingerprint"),
        request.url.path,
    )
    if not ok or not (cert and cert.get("is_owner")):
        raise HTTPException(status_code=403, detail="Owner certificate required")
    return cert


@app.get("/certificates", response_class=HTMLResponse)
async def certificates_page(request: Request):
    """
    Minimal Certificate Management Admin Page (OWNER only).
    """
    _require_owner(request)
    certs = auth_manager.list_certificates()
    return templates.TemplateResponse("certificates.html", {
        "request": request,
        "certificates": certs,
    })


@app.get("/admin-api/certificates")
async def api_list_certificates(request: Request):
    """List all registered certificates (OWNER only)."""
    _require_owner(request)
    return auth_manager.list_certificates()


@app.post("/admin-api/certificates")
async def api_create_certificate(req: CreateCertRequest, request: Request):
    """Issue a new USER certificate (OWNER only)."""
    _require_owner(request)
    try:
        created = auth_manager.create_user_certificate(req.name)
        return created
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/admin-api/certificates/{cert_id}/revoke")
async def api_revoke_certificate(cert_id: str, request: Request):
    """Revoke an active USER certificate (OWNER only; rejects revoking OWNER)."""
    _require_owner(request)
    try:
        updated = auth_manager.revoke_certificate(cert_id)
        return updated
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/admin-api/certificates/{cert_id}/download")
async def api_download_certificate(cert_id: str, request: Request):
    """Download .p12 archive for a certificate (OWNER only)."""
    _require_owner(request)

    try:
        path, filename = auth_manager.get_p12_path(cert_id)
        return FileResponse(
            path=path,
            filename=filename,
            media_type="application/x-pkcs12",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/admin-api/certificates/{cert_id}/password.txt")
async def api_download_certificate_password(cert_id: str, request: Request):
    """Download .txt password file for a freshly created certificate (OWNER only)."""
    _require_owner(request)
    password = auth_manager.get_temp_user_password(cert_id)
    if not password:
        raise HTTPException(status_code=404, detail="Одноразовый пароль более недоступен")
    return Response(
        content=f"{password}\n",
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{cert_id}_password.txt"'}
    )


# ============================================================================
# Stage 07B-R2: Web Backup and Restore (OWNER only)
# ============================================================================

@app.get("/backups", response_class=HTMLResponse)
async def backups_page(request: Request):
    """Web Backup and Restore Admin Page (OWNER only)."""
    _require_owner(request)
    return templates.TemplateResponse("backups.html", {"request": request})


@app.post("/admin-api/backups/download")
async def api_download_backup(request: Request):
    """Create and download full system backup archive (OWNER only)."""
    _require_owner(request)
    try:
        backup_zip, manifest = backup_service.create_backup()

        def _cleanup(file_path: str):
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception:
                pass

        return FileResponse(
            path=str(backup_zip),
            filename=backup_zip.name,
            media_type="application/zip",
            background=BackgroundTask(_cleanup, str(backup_zip)),
            headers={"Content-Disposition": f'attachment; filename="{backup_zip.name}"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка создания резервной копии: {e}")


@app.post("/admin-api/backups/restore")
async def api_restore_backup(request: Request, backup_file: UploadFile = File(None)):
    """Upload and restore full system backup archive (OWNER only)."""
    _require_owner(request)
    if not backup_file or not backup_file.filename:
        return JSONResponse(status_code=400, content={"status": "error", "message": "Файл резервной копии не передан"})

    temp_zip = Path(tempfile.gettempdir()) / f"upload_restore_{os.getpid()}_{backup_file.filename}"
    try:
        with open(temp_zip, "wb") as f:
            while chunk := await backup_file.read(1024 * 1024):
                f.write(chunk)

        success, msg = backup_service.restore_backup(temp_zip)
        if not success:
            return JSONResponse(status_code=400, content={"status": "error", "message": msg})

        return JSONResponse(content={"status": "ok", "message": msg})
    except Exception as e:
        return JSONResponse(status_code=400, content={"status": "error", "message": f"Ошибка восстановления: {e}"})
    finally:
        if temp_zip.is_file():
            try:
                temp_zip.unlink()
            except Exception:
                pass


# ============================================================================
# Stage 07C-R1: Product Canonical JSON Import / Export & AI Prompt Generator
# ============================================================================

@app.get("/admin-api/products/json/prompt.txt")
async def api_download_products_ai_prompt():
    """Download AI Prompt as a plain text file."""
    prompt_text = ""
    async with httpx.AsyncClient(trust_env=False) as client:
        try:
            resp = await client.get(f"{CORE_API_URL}/api/products/json/schema", timeout=10.0)
            if resp.status_code == 200:
                prompt_text = resp.json().get("ai_prompt", "")
        except Exception:
            prompt_text = ""

    if not prompt_text:
        prompt_text = "Промпт временно недоступен или Core API офлайн."

    return Response(
        content=prompt_text,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="technoreboot_ai_prompt.txt"'}
    )


@app.post("/admin-api/products/json/import")
async def api_proxy_products_json_import(
    request: Request,
    file: Optional[UploadFile] = File(None),
    json_text: Optional[str] = Form(None)
):
    """
    Proxy JSON product import to Core API.
    Accepts:
    1. Uploaded file (multipart/form-data)
    2. Form field `json_text` (multipart/form-data or form-urlencoded)
    3. Raw JSON body (application/json)
    """
    content_type = request.headers.get("content-type", "")
    payload_data = None

    if "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
        if file and file.filename:
            try:
                raw_bytes = await file.read()
                payload_data = json.loads(raw_bytes.decode("utf-8-sig"))
            except Exception as e:
                return JSONResponse(
                    status_code=400,
                    content={"status": "error", "message": f"Ошибка чтения загруженного JSON-файла: {e}"}
                )
        elif json_text:
            try:
                payload_data = json.loads(json_text)
            except Exception as e:
                return JSONResponse(
                    status_code=400,
                    content={"status": "error", "message": f"Ошибка разбора JSON из текста: {e}"}
                )
        else:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Файл или текст JSON не переданы"}
            )
    else:
        # Expect raw application/json body
        try:
            payload_data = await request.json()
        except Exception as e:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": f"Некорректный JSON в теле запроса: {e}"}
            )

    if not payload_data:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Пустые данные JSON для импорта"}
        )

    async with httpx.AsyncClient(trust_env=False) as client:
        try:
            resp = await client.post(
                f"{CORE_API_URL}/api/products/json/import",
                json=payload_data,
                timeout=60.0
            )
            return JSONResponse(status_code=resp.status_code, content=resp.json())
        except httpx.RequestError as e:
            return JSONResponse(
                status_code=503,
                content={"status": "error", "message": f"Ошибка соединения с Core API: {str(e)}"}
            )


@app.api_route("/admin-api/products/json/export", methods=["GET", "POST"])
async def api_proxy_products_json_export(request: Request, ids: Optional[str] = None):
    """
    Proxy JSON product export to Core API.
    Streams back JSON attachment named TECHNOREBOOT_PRODUCTS_YYYY-MM-DD_HHMMSS.json.
    Supports GET with query param ?ids=1,2,3 or POST with JSON body {"ids": [1, 2, 3]}.
    """
    product_ids_str = ids
    if request.method == "POST":
        try:
            body = await request.json()
            if isinstance(body, dict) and "ids" in body:
                raw_ids = body["ids"]
                if isinstance(raw_ids, list):
                    product_ids_str = ",".join(str(x) for x in raw_ids if str(x).isdigit())
                elif isinstance(raw_ids, str):
                    product_ids_str = raw_ids
        except Exception:
            pass

    params = {}
    if product_ids_str:
        params["ids"] = product_ids_str

    async with httpx.AsyncClient(trust_env=False) as client:
        try:
            resp = await client.get(
                f"{CORE_API_URL}/api/products/json/export",
                params=params,
                timeout=60.0
            )
            if resp.status_code == 200:
                now_str = datetime.now().strftime("%Y-%m-%d_%H%M%S")
                filename = f"TECHNOREBOOT_PRODUCTS_{now_str}.json"
                return Response(
                    content=resp.content,
                    media_type="application/json; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'}
                )
            else:
                try:
                    err_payload = resp.json()
                except Exception:
                    err_payload = {"status": "error", "message": resp.text or f"Ошибка Core API ({resp.status_code})"}
                return JSONResponse(status_code=resp.status_code, content=err_payload)
        except httpx.RequestError as e:
            return JSONResponse(
                status_code=503,
                content={"status": "error", "message": f"Ошибка соединения с Core API: {str(e)}"}
            )


