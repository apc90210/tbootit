from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.core_client import core_client
from typing import Optional

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


def clean_param(value):
    """Treat empty strings as None."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


# Default empty report data structure used when Core returns an error
DEFAULT_REPORT_DATA = {
    "period": "today",
    "date_from": "",
    "date_to": "",
    "total_amount": 0.0,
    "sales_count": 0,
    "items_count": 0,
    "payment_breakdown": [],
    "money_summary": {
        "cash": 0.0,
        "card": 0.0,
        "transfer": 0.0,
        "sbp": 0.0,
        "legal_entity_account": 0.0,
        "other": 0.0,
        "unspecified": 0.0,
        "total": 0.0,
    },
    "payment_labels": {
        "cash": "Наличные",
        "card": "Безнал / карта",
        "transfer": "Перевод",
        "sbp": "СБП",
        "legal_entity_account": "Счёт юрлица",
        "other": "Другое",
        "unspecified": "Не указано",
    },
    "sales": []
}


@router.get("/reports/sales", response_class=HTMLResponse)
async def sales_report(
    request: Request,
    period: Optional[str] = Query(None),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
):
    # Sanitize parameters
    period = clean_param(period)
    date_from = clean_param(date_from)
    date_to = clean_param(date_to)
    
    from datetime import date
    today = date.today()

    if date_from or date_to:
        period = "custom"
    elif not period:
        period = "custom"
        date_from = date(today.year, 1, 1).isoformat()
        date_to = today.isoformat()

    # If custom period with empty dates, fall back to year-to-date
    if period == "custom" and not date_from and not date_to:
        date_from = date(today.year, 1, 1).isoformat()
        date_to = today.isoformat()
    
    error_message = None
    report_data = await core_client.get_sales_report(period=period, date_from=date_from, date_to=date_to)
    
    # Handle Core API errors gracefully
    if isinstance(report_data, dict) and report_data.get("error"):
        error_message = report_data.get("detail") or report_data.get("details") or "Ошибка получения данных от сервера"
        report_data = dict(DEFAULT_REPORT_DATA)
        report_data["period"] = period
    
    # Ensure money_summary exists even if old API version didn't return it
    if "money_summary" not in report_data:
        report_data["money_summary"] = dict(DEFAULT_REPORT_DATA["money_summary"])
    if "payment_labels" not in report_data:
        report_data["payment_labels"] = dict(DEFAULT_REPORT_DATA["payment_labels"])
    
    # Synchronize date_from and date_to template values with effective dates from report_data (e.g. for quick filters)
    rep_date_from = report_data.get("date_from") if isinstance(report_data, dict) else getattr(report_data, "date_from", "")
    rep_date_to = report_data.get("date_to") if isinstance(report_data, dict) else getattr(report_data, "date_to", "")

    effective_date_from = date_from or rep_date_from or ""
    effective_date_to = date_to or rep_date_to or ""

    return templates.TemplateResponse(
        request,
        "reports_sales.html",
        {
            "report_data": report_data,
            "period": period,
            "date_from": effective_date_from,
            "date_to": effective_date_to,
            "error_message": error_message
        }
    )
