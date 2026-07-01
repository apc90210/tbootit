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
    # Seed Categories
    categories_data = [
        {"name": "Ноутбуки", "slug": "laptops", "desc": "Portable computers"},
        {"name": "Принтеры", "slug": "printers", "desc": "Printing devices"},
        {"name": "Мониторы", "slug": "monitors", "desc": "Displays"},
        {"name": "Комплектующие", "slug": "components", "desc": "PC parts"}
    ]
    categories = {}
    for cd in categories_data:
        cat = db.query(models.Category).filter(models.Category.slug == cd["slug"]).first()
        if not cat:
            cat = models.Category(name=cd["name"], slug=cd["slug"], description=cd["desc"])
            db.add(cat)
            db.commit()
            db.refresh(cat)
        categories[cd["slug"]] = cat
    
    # Seed Products
    products_data = [
        {"sku": "LAP001", "title": "Lenovo ThinkPad T480", "cat": "laptops", "status": "in_stock"},
        {"sku": "PRN001", "title": "HP LaserJet 2055dn", "cat": "printers", "status": "in_stock"},
        {"sku": "MON001", "title": "Dell P2419H", "cat": "monitors", "status": "in_stock"},
        {"sku": "CMP001", "title": "Kingston SSD 480GB", "cat": "components", "status": "in_stock"},
        {"sku": "CMP002", "title": "Logitech K120", "cat": "components", "status": "in_stock"}
    ]
    products = {}
    for pd in products_data:
        prod = db.query(models.Product).filter(models.Product.sku == pd["sku"]).first()
        if not prod:
            prod = models.Product(sku=pd["sku"], title=pd["title"], category_id=categories[pd["cat"]].id, status=pd["status"])
            db.add(prod)
            db.commit()
            db.refresh(prod)
        products[pd["sku"]] = prod

    # Seed Customers
    customers_data = [
        {"name": "Иван Тестовый", "phone": "+7 900 000-00-01", "email": "ivan@test.local"},
        {"name": "Мария Проверочная", "phone": "+7 900 000-00-02", "email": "maria@test.local"},
        {"name": "ООО Ромашка", "phone": "+7 900 000-00-03", "email": "romashka@test.local"}
    ]
    customers = {}
    for cud in customers_data:
        cust = db.query(models.Customer).filter(models.Customer.phone == cud["phone"]).first()
        if not cust:
            cust = models.Customer(name=cud["name"], phone=cud["phone"], email=cud["email"])
            db.add(cust)
            db.commit()
            db.refresh(cust)
        customers[cud["phone"]] = cust

    # Seed Repairs
    repairs_data = [
        {"customer_phone": "+7 900 000-00-01", "title": "HP LaserJet 2055dn", "serial": "SN-PRN-01", "problem": "не захватывает бумагу", "status": "diagnostics"},
        {"customer_phone": "+7 900 000-00-02", "title": "Lenovo ThinkPad T480", "serial": "SN-LAP-02", "problem": "замена клавиатуры", "status": "waiting_parts"}
    ]
    for rd in repairs_data:
        cust = customers.get(rd["customer_phone"])
        if cust:
            rep = db.query(models.RepairOrder).filter(
                models.RepairOrder.customer_id == cust.id, 
                models.RepairOrder.device_serial == rd["serial"]
            ).first()
            if not rep:
                rep = models.RepairOrder(
                    customer_id=cust.id, 
                    device_title=rd["title"], 
                    device_serial=rd["serial"],
                    problem_description=rd["problem"],
                    status=rd["status"]
                )
                db.add(rep)
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
