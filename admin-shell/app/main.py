from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, Response, JSONResponse, FileResponse, RedirectResponse
from pydantic import BaseModel
import os
import httpx
import asyncio

app = FastAPI(title="Technoreboot Admin Shell")
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)



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
    version = "0.2.15"
    filename = f"technoreboot-avito-extension-{version}.zip"
    zip_path = os.path.abspath(os.path.join(os.path.dirname(__file__), filename))
    if not os.path.exists(zip_path):
        zip_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "technoreboot-avito-extension.zip"))
    if not os.path.exists(zip_path):
        zip_path = os.path.abspath(f"dist/{filename}")
    if not os.path.exists(zip_path):
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
            return Response(content=resp.content, status_code=resp.status_code, media_type=resp.headers.get("content-type", "application/json"))
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


@app.get("/products/{product_id}")
async def redirect_products_detail_shortcut(product_id: int):
    return RedirectResponse(url=f"/inventory/products/{product_id}", status_code=302)


@app.get("/products")
async def redirect_products_list_shortcut():
    return RedirectResponse(url="/inventory/products", status_code=302)


