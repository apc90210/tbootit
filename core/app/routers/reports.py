from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime, date, timedelta, time
from app import models, schemas
from app.database import get_db

router = APIRouter()

PAYMENT_METHODS_LABELS = {
    "cash": "Наличные",
    "card": "Карта / эквайринг",
    "transfer": "Перевод",
    "sbp": "СБП",
    "legal_entity_account": "Счёт юрлица",
    "mixed": "Смешанная оплата",
    "other": "Другое",
    "unspecified": "Не указано"
}

def get_date_range(period: str, date_from: Optional[str] = None, date_to: Optional[str] = None):
    now = datetime.now()
    today = now.date()
    
    start_dt = None
    end_dt = None
    
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
        if not date_from or not date_to:
            raise HTTPException(status_code=400, detail="date_from and date_to are required for custom period")
        try:
            start_date = datetime.strptime(date_from, "%Y-%m-%d").date()
            end_date = datetime.strptime(date_to, "%Y-%m-%d").date()
            start_dt = datetime.combine(start_date, time.min)
            end_dt = datetime.combine(end_date, time.max)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        raise HTTPException(status_code=400, detail="Invalid period")
        
    return start_dt, end_dt

@router.get("/sales", response_model=schemas.SalesReportResponse)
def get_sales_report(
    period: str = Query("today", description="today, week, month, year, custom"),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: Session = Depends(get_db)
):
    start_dt, end_dt = get_date_range(period, date_from, date_to)
    
    sales_query = db.query(models.Sale).filter(
        models.Sale.created_at >= start_dt,
        models.Sale.created_at <= end_dt
    ).order_by(models.Sale.created_at.desc())
    
    sales_list = sales_query.all()
    
    total_amount = 0.0
    sales_count = len(sales_list)
    items_count = 0
    
    payment_breakdown_dict = {}
    report_sales = []
    
    for sale in sales_list:
        total_amount += sale.total_amount
        sale_items_count = len(sale.items)
        items_count += sale_items_count
        
        pm = sale.payment_method if sale.payment_method else "unspecified"
        pm_label = PAYMENT_METHODS_LABELS.get(pm, pm)
        
        if pm not in payment_breakdown_dict:
            payment_breakdown_dict[pm] = {
                "payment_method": pm,
                "label": pm_label,
                "amount": 0.0,
                "sales_count": 0
            }
        payment_breakdown_dict[pm]["amount"] += sale.total_amount
        payment_breakdown_dict[pm]["sales_count"] += 1
        
        report_sales.append(
            schemas.ReportSaleItem(
                id=sale.id,
                created_at=sale.created_at,
                total_amount=sale.total_amount,
                items_count=sale_items_count,
                payment_method=pm,
                payment_method_label=pm_label,
                comment=sale.comment
            )
        )
        
    payment_breakdown = list(payment_breakdown_dict.values())
    
    # Sort breakdown by amount descending
    payment_breakdown.sort(key=lambda x: x["amount"], reverse=True)
    
    return schemas.SalesReportResponse(
        period=period,
        date_from=start_dt.date().isoformat(),
        date_to=end_dt.date().isoformat(),
        total_amount=total_amount,
        sales_count=sales_count,
        items_count=items_count,
        payment_breakdown=[schemas.PaymentBreakdown(**pb) for pb in payment_breakdown],
        sales=report_sales
    )
