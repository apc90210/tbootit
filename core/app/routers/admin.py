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
    from app.routers.product_cards import import_json as do_import
    from app.schemas import ProductCardJSONPayload

    seed_cards = [
        {
            "source": "seed", "schema_version": "1.0", "operation": "create_or_update",
            "product": {"sku": "LAP001", "title": "Ноутбук Lenovo ThinkPad T480", "category_path": ["Ноутбуки"],
                        "brand": "Lenovo", "model": "ThinkPad T480", "condition": "БУ, рабочий",
                        "description": "Надежный офисный ноутбук Lenovo ThinkPad T480. Core i5-8250U, 8GB RAM, SSD 256GB.",
                        "purchase_price": 12000, "sale_price": 21000, "min_price": 19000,
                        "quantity": 5, "storage_location": "Склад 1", "notes": "Проверить батарею"},
            "avito": {"title": "Ноутбук Lenovo ThinkPad T480, Core i5, 8 ГБ, SSD",
                      "description": "Продается надежный Lenovo ThinkPad T480. Core i5, 8 ГБ RAM, SSD 256 ГБ. БУ, рабочий.",
                      "category_path": ["Электроника", "Ноутбуки"], "goods_type": "Ноутбук",
                      "condition": "Б/у", "price": 21000, "seller_type": "company",
                      "contact_name": "Техноребут",
                      "parameters": {"Производитель": "Lenovo", "Модель": "ThinkPad T480",
                                     "Процессор": "Intel Core i5-8250U", "RAM": "8 ГБ",
                                     "Накопитель": "SSD 256 ГБ", "Диагональ": "14\"", "Состояние": "Б/у"}},
            "site": {"title": "Ноутбук Lenovo ThinkPad T480", "description": "Проверенный БУ ноутбук для работы.", "publish_ready": False}
        },
        {
            "source": "seed", "schema_version": "1.0", "operation": "create_or_update",
            "product": {"sku": "PRN001", "title": "Принтер HP LaserJet 2055dn", "category_path": ["Принтеры"],
                        "brand": "HP", "model": "LaserJet 2055dn", "condition": "БУ, рабочий",
                        "description": "Сетевой лазерный принтер HP LaserJet 2055dn с дуплексом.",
                        "purchase_price": 3000, "sale_price": 5500, "min_price": 5000,
                        "quantity": 2, "storage_location": "Склад 1"},
            "avito": {"title": "Лазерный принтер HP LaserJet 2055dn, сеть, дуплекс",
                      "description": "Рабочий лазерный принтер HP LaserJet 2055dn с сетевым подключением и дуплексной печатью.",
                      "goods_type": "Принтер", "condition": "Б/у", "price": 5500, "seller_type": "company",
                      "contact_name": "Техноребут",
                      "parameters": {"Производитель": "HP", "Модель": "LaserJet 2055dn",
                                     "Тип": "Лазерный", "Сеть": "Да", "Дуплекс": "Да"}},
            "site": {"title": "Принтер HP LaserJet 2055dn", "description": "Надежный сетевой принтер.", "publish_ready": False}
        },
        {
            "source": "seed", "schema_version": "1.0", "operation": "create_or_update",
            "product": {"sku": "MON001", "title": "Монитор Dell P2419H", "category_path": ["Мониторы"],
                        "brand": "Dell", "model": "P2419H", "condition": "БУ, хорошее",
                        "description": "24-дюймовый IPS монитор Dell P2419H, Full HD, USB-хаб.",
                        "purchase_price": 5500, "sale_price": 9000, "min_price": 8000,
                        "quantity": 3, "storage_location": "Витрина"},
            "avito": {"title": "Монитор Dell P2419H, 24\", IPS, Full HD",
                      "description": "Монитор Dell P2419H 24 дюйма IPS Full HD. С USB-хабом, в хорошем состоянии.",
                      "goods_type": "Монитор", "condition": "Б/у", "price": 9000, "seller_type": "company",
                      "contact_name": "Техноребут",
                      "parameters": {"Производитель": "Dell", "Модель": "P2419H",
                                     "Диагональ": "24\"", "Матрица": "IPS", "Разрешение": "1920x1080"}},
            "site": {"title": "Монитор Dell P2419H 24\" IPS", "description": "IPS монитор для работы.", "publish_ready": True}
        },
        {
            "source": "seed", "schema_version": "1.0", "operation": "create_or_update",
            "product": {"sku": "CMP001", "title": "SSD Kingston 480 ГБ", "category_path": ["Комплектующие"],
                        "brand": "Kingston", "model": "A400 480GB", "condition": "Б/у, рабочий",
                        "description": "SSD-накопитель Kingston A400 480 ГБ, 2.5 дюйма, SATA.",
                        "purchase_price": 1800, "sale_price": 3200, "min_price": 2800,
                        "quantity": 10, "storage_location": "Склад 1"},
            "avito": {"title": "SSD Kingston A400 480 ГБ",
                      "description": "SSD накопитель Kingston A400 480 ГБ, форм-фактор 2.5\", интерфейс SATA III.",
                      "goods_type": "SSD накопитель", "condition": "Б/у", "price": 3200, "seller_type": "company",
                      "contact_name": "Техноребут",
                      "parameters": {"Производитель": "Kingston", "Модель": "A400", "Объём": "480 ГБ",
                                     "Интерфейс": "SATA III", "Форм-фактор": "2.5\""}},
            "site": {"title": "SSD Kingston A400 480 ГБ", "description": "Проверенный SSD от Kingston.", "publish_ready": True}
        },
        {
            "source": "seed", "schema_version": "1.0", "operation": "create_or_update",
            "product": {"sku": "PER001", "title": "Клавиатура Logitech K120", "category_path": ["Периферия"],
                        "brand": "Logitech", "model": "K120", "condition": "Новая",
                        "description": "Проводная клавиатура Logitech K120, USB, русская раскладка.",
                        "purchase_price": 500, "sale_price": 900, "min_price": 750,
                        "quantity": 15, "storage_location": "Витрина"},
            "avito": {"title": "Клавиатура Logitech K120, USB, новая",
                      "description": "Новая проводная клавиатура Logitech K120. USB, русская раскладка.",
                      "goods_type": "Клавиатура", "condition": "Новое", "price": 900, "seller_type": "company",
                      "contact_name": "Техноребут",
                      "parameters": {"Производитель": "Logitech", "Модель": "K120",
                                     "Тип": "Проводная", "Интерфейс": "USB", "Состояние": "Новая"}},
            "site": {"title": "Клавиатура Logitech K120", "description": "Новая проводная клавиатура Logitech K120.", "publish_ready": True}
        }
    ]

    from app.routers.customers import log_audit
    imported = 0
    for card_data in seed_cards:
        try:
            payload = ProductCardJSONPayload(**card_data)
            do_import(payload, db)
            imported += 1
        except Exception as e:
            print(f"Seed import error for {card_data['product']['sku']}: {e}")

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
        {"customer_phone": "+7 900 000-00-01", "title": "Принтер HP LaserJet 2055dn", "serial": "SN-PRN-01", "problem": "не захватывает бумагу", "status": "diagnostics"},
        {"customer_phone": "+7 900 000-00-02", "title": "Ноутбук Lenovo ThinkPad T480", "serial": "SN-LAP-02", "problem": "требуется замена клавиатуры", "status": "waiting_parts"}
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

    log_audit(db, "system", 0, "seed", comment=f"Database seeded: {imported} cards imported")
    db.commit()
    return {"message": f"Seed successful: {imported} product cards imported"}

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
