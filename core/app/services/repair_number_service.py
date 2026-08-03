import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from app import models

def generate_repair_number(db: Session, accepted_at: datetime.datetime = None) -> str:
    """
    Generates a unique repair order number in format R-YYYYMMDD-XXXX.
    Guaranteed unique by checking existing database records.
    """
    dt = accepted_at or datetime.datetime.utcnow()
    date_str = dt.strftime("%Y%m%d")
    prefix = f"R-{date_str}-"

    # Query existing max repair number with prefix
    existing_numbers = db.query(models.RepairOrder.number).filter(
        models.RepairOrder.number.like(f"{prefix}%")
    ).all()

    max_counter = 0
    for (num,) in existing_numbers:
        if num and num.startswith(prefix):
            suffix = num[len(prefix):]
            if suffix.isdigit():
                max_counter = max(max_counter, int(suffix))

    counter = max_counter + 1
    candidate = f"{prefix}{counter:04d}"

    # Fallback collision check
    while db.query(models.RepairOrder).filter(models.RepairOrder.number == candidate).first() is not None:
        counter += 1
        candidate = f"{prefix}{counter:04d}"

    return candidate
