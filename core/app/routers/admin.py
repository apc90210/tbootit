from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import inspect
from app.database import get_db, engine
from app import models
import json

router = APIRouter()

@router.get("/db/schema")
def get_db_schema():
    inspector = inspect(engine)
    schema = {}
    for table_name in inspector.get_table_names():
        columns = inspector.get_columns(table_name)
        schema[table_name] = [{"name": col["name"], "type": str(col["type"])} for col in columns]
    return schema

@router.get("/db/tables")
def get_db_tables():
    inspector = inspect(engine)
    return {"tables": inspector.get_table_names()}

@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    return {
        "products": db.query(models.Product).count(),
        "customers": db.query(models.Customer).count(),
        "repairs": db.query(models.RepairOrder).count(),
        "sales": db.query(models.Sale).count(),
    }

@router.get("/audit-log")
def get_audit_log(db: Session = Depends(get_db)):
    return db.query(models.AuditLog).order_by(models.AuditLog.created_at.desc()).limit(100).all()

@router.post("/seed")
def seed_data(db: Session = Depends(get_db)):
    # Simple seed for MVP
    cat = models.Category(name="Laptops", slug="laptops", description="Portable computers")
    db.add(cat)
    db.commit()
    
    prod = models.Product(sku="LAP001", title="Thinkpad T480", category_id=cat.id, status="in_stock")
    db.add(prod)
    db.commit()
    
    from app.routers.customers import log_audit
    log_audit(db, "system", 0, "seed", comment="Database seeded with dummy data")
    db.commit()
    return {"message": "Seed successful"}

@router.post("/backup")
def trigger_backup():
    return {"message": "Backup triggered (stub)"}

@router.post("/dev-reset")
def dev_reset(db: Session = Depends(get_db)):
    # Dev-only: drops and recreates
    from app.database import Base
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return {"message": "Dev reset complete"}
