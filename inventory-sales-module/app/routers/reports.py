from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.core_client import core_client
from typing import Optional

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")

@router.get("/reports/sales", response_class=HTMLResponse)
async def sales_report(
    request: Request,
    period: str = Query("today"),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
):
    report_data = await core_client.get_sales_report(period=period, date_from=date_from, date_to=date_to)
    
    return templates.TemplateResponse(
        request,
        "reports_sales.html",
        {
            "report_data": report_data,
            "period": period,
            "date_from": date_from,
            "date_to": date_to
        }
    )
