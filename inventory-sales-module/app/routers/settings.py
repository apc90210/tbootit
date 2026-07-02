from fastapi import APIRouter, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.core_client import core_client

router = APIRouter(prefix="/settings", tags=["settings"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/organization", response_class=HTMLResponse)
async def organization_settings_page(request: Request):
    try:
        response = await core_client.get_organization_settings()
        settings_data = response if not response.get("error") else {}
    except Exception as e:
        settings_data = {}

    return templates.TemplateResponse(
        request=request,
        name="settings_organization.html",
        context={
            "request": request,
            "settings": settings_data,
            "active_page": "settings"
        }
    )

@router.post("/organization")
async def update_organization_settings(
    request: Request,
    organization_name: str = Form(...),
    inn: str = Form(...),
    address: str = Form(...),
    phone: str = Form(...),
    default_customer_label: str = Form("Частное лицо")
):
    payload = {
        "organization_name": organization_name,
        "inn": inn,
        "address": address,
        "phone": phone,
        "default_customer_label": default_customer_label
    }
    
    try:
        await core_client.update_organization_settings(payload)
    except Exception as e:
        # Handle error (flash message etc in real app, simple redirect for MVP)
        pass
    
    return RedirectResponse(url="/settings/organization", status_code=status.HTTP_303_SEE_OTHER)
