from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Optional
from datetime import datetime, date, timedelta, time
from app import models, schemas
from app.database import get_db

router = APIRouter()

PAYMENT_METHODS_LABELS = {
    "cash": "Наличные",
    "card": "Безнал / карта",
    "bank_card": "Безнал / карта",
    "acquiring": "Безнал / карта",
    "transfer": "Перевод",
    "sbp": "СБП",
    "legal_entity_account": "Счёт юрлица",
    "mixed": "Смешанная оплата",
    "other": "Другое",
    "unspecified": "Не указано"
}

# Mapping from raw payment_method to money_summary key
PAYMENT_TO_SUMMARY_KEY = {
    "cash": "cash",
    "card": "card",
    "bank_card": "card",
    "acquiring": "card",
    "transfer": "transfer",
    "sbp": "sbp",
    "legal_entity_account": "legal_entity_account",
    "mixed": "other",
    "other": "other",
    "unspecified": "unspecified",
}

# Labels for money_summary keys (for the compact summary table)
SUMMARY_LABELS = {
    "cash": "Наличные",
    "card": "Безнал / карта",
    "transfer": "Перевод",
    "sbp": "СБП",
    "legal_entity_account": "Счёт юрлица",
    "other": "Другое",
    "unspecified": "Не указано",
}


def clean_param(value):
    """Treat empty strings as None."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def parse_date_or_none(value):
    """Parse a date string or return None. Raises HTTPException on invalid format."""
    value = clean_param(value)
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise HTTPException(status_code=400, detail="Некорректная дата. Используйте формат YYYY-MM-DD")


def get_date_range(period: str, date_from: Optional[str] = None, date_to: Optional[str] = None):
    now = datetime.now()
    today = now.date()
    
    # Clean params
    period = clean_param(period) or "today"
    date_from = clean_param(date_from)
    date_to = clean_param(date_to)
    
    start_dt = None
    end_dt = None
    
    # If custom period but dates are empty, fall back to today
    if period == "custom" and not date_from and not date_to:
        period = "today"
    
    if period == "today":
        start_dt = datetime.combine(today, time.min)
        end_dt = datetime.combine(today, time.max)
    elif period == "week":
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        start_dt = datetime.combine(start_of_week, time.min)
        end_dt = datetime.combine(end_of_week, time.max)
    elif period == "month":
        start_of_month = today.replace(day=1)
        # next month first day minus 1 day
        next_month = start_of_month.replace(day=28) + timedelta(days=4)
        end_of_month = next_month - timedelta(days=next_month.day)
        start_dt = datetime.combine(start_of_month, time.min)
        end_dt = datetime.combine(end_of_month, time.max)
    elif period == "year":
        start_of_year = today.replace(month=1, day=1)
        end_of_year = today.replace(month=12, day=31)
        start_dt = datetime.combine(start_of_year, time.min)
        end_dt = datetime.combine(end_of_year, time.max)
    elif period == "custom":
        parsed_from = parse_date_or_none(date_from)
        parsed_to = parse_date_or_none(date_to)
        
        if not parsed_from and not parsed_to:
            # Both empty — fall back to today (shouldn't reach here, caught above)
            start_dt = datetime.combine(today, time.min)
            end_dt = datetime.combine(today, time.max)
        elif parsed_from and not parsed_to:
            # Only start date — use same date as end
            start_dt = datetime.combine(parsed_from, time.min)
            end_dt = datetime.combine(parsed_from, time.max)
        elif not parsed_from and parsed_to:
            # Only end date — use same date as start
            start_dt = datetime.combine(parsed_to, time.min)
            end_dt = datetime.combine(parsed_to, time.max)
        else:
            start_dt = datetime.combine(parsed_from, time.min)
            end_dt = datetime.combine(parsed_to, time.max)
    else:
        # Unknown period — fall back to today rather than 400
        start_dt = datetime.combine(today, time.min)
        end_dt = datetime.combine(today, time.max)
        period = "today"
        
    return start_dt, end_dt, period

@router.get("/sales", response_model=schemas.SalesReportResponse)
def get_sales_report(
    period: str = Query("today", description="today, week, month, year, custom"),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: Session = Depends(get_db)
):
    start_dt, end_dt, effective_period = get_date_range(period, date_from, date_to)
    
    sales_query = db.query(models.Sale).filter(
        models.Sale.created_at >= start_dt,
        models.Sale.created_at <= end_dt,
        or_(models.Sale.status == "completed", models.Sale.status == None)
    ).order_by(models.Sale.created_at.desc())
    
    sales_list = sales_query.all()
    
    total_amount = 0.0
    sales_count = len(sales_list)
    items_count = 0
    
    payment_breakdown_dict = {}
    report_sales = []
    
    # Initialize money summary with all zeros
    money_summary_dict = {
        "cash": 0.0,
        "card": 0.0,
        "transfer": 0.0,
        "sbp": 0.0,
        "legal_entity_account": 0.0,
        "other": 0.0,
        "unspecified": 0.0,
    }
    
    granularity = "month" if effective_period == "year" else "day"
    rows_dict = {}
    
    if granularity == "day":
        current_dt = start_dt.date()
        end_date = end_dt.date()
        while current_dt <= end_date:
            key = current_dt.isoformat()
            label = current_dt.strftime("%d.%m.%Y")
            rows_dict[key] = {
                "period_key": key,
                "label": label,
                "cash": 0.0,
                "card": 0.0,
                "transfer": 0.0,
                "sbp": 0.0,
                "legal_entity_account": 0.0,
                "other": 0.0,
                "unspecified": 0.0,
                "total": 0.0
            }
            current_dt += timedelta(days=1)
    else:
        current_dt = start_dt.date().replace(day=1)
        end_date = end_dt.date().replace(day=1)
        month_names = {
            1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
            5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
            9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
        }
        while current_dt <= end_date:
            key = current_dt.strftime("%Y-%m")
            label = f"{month_names[current_dt.month]} {current_dt.year}"
            rows_dict[key] = {
                "period_key": key,
                "label": label,
                "cash": 0.0,
                "card": 0.0,
                "transfer": 0.0,
                "sbp": 0.0,
                "legal_entity_account": 0.0,
                "other": 0.0,
                "unspecified": 0.0,
                "total": 0.0
            }
            if current_dt.month == 12:
                current_dt = current_dt.replace(year=current_dt.year + 1, month=1)
            else:
                current_dt = current_dt.replace(month=current_dt.month + 1)
    
    for sale in sales_list:
        total_amount += sale.total_amount
        sale_items_count = len(sale.items)
        items_count += sale_items_count
        
        # Normalize payment method
        raw_pm = sale.payment_method if sale.payment_method else "unspecified"
        raw_pm = raw_pm.strip() if raw_pm else "unspecified"
        if not raw_pm:
            raw_pm = "unspecified"
        
        pm_label = PAYMENT_METHODS_LABELS.get(raw_pm, PAYMENT_METHODS_LABELS.get("other", raw_pm))
        summary_key = PAYMENT_TO_SUMMARY_KEY.get(raw_pm, "other")
        
        if raw_pm not in payment_breakdown_dict:
            payment_breakdown_dict[raw_pm] = {
                "payment_method": raw_pm,
                "label": pm_label,
                "amount": 0.0,
                "sales_count": 0
            }
        payment_breakdown_dict[raw_pm]["amount"] += sale.total_amount
        payment_breakdown_dict[raw_pm]["sales_count"] += 1
        
        # Accumulate money summary
        money_summary_dict[summary_key] += sale.total_amount
        
        # Accumulate to row
        row_key = sale.created_at.date().isoformat() if granularity == "day" else sale.created_at.strftime("%Y-%m")
        if row_key in rows_dict:
            rows_dict[row_key][summary_key] += sale.total_amount
            rows_dict[row_key]["total"] += sale.total_amount
        
        report_sales.append(
            schemas.ReportSaleItem(
                id=sale.id,
                created_at=sale.created_at,
                total_amount=sale.total_amount,
                items_count=sale_items_count,
                payment_method=raw_pm,
                payment_method_label=pm_label,
                comment=sale.comment
            )
        )
        
    payment_breakdown = list(payment_breakdown_dict.values())
    
    # Sort breakdown by amount descending
    payment_breakdown.sort(key=lambda x: x["amount"], reverse=True)
    
    # Build money summary
    money_summary_dict["total"] = total_amount
    money_summary_total = schemas.MoneySummary(**money_summary_dict)
    
    money_summary_rows = [schemas.MoneySummaryRow(**row) for row in rows_dict.values()]
    
    return schemas.SalesReportResponse(
        period=effective_period,
        date_from=start_dt.date().isoformat(),
        date_to=end_dt.date().isoformat(),
        total_amount=total_amount,
        sales_count=sales_count,
        items_count=items_count,
        payment_breakdown=[schemas.PaymentBreakdown(**pb) for pb in payment_breakdown],
        money_summary=money_summary_total,
        money_summary_rows=money_summary_rows,
        money_summary_total=money_summary_total,
        money_summary_granularity=granularity,
        payment_labels=SUMMARY_LABELS,
        sales=report_sales
    )
