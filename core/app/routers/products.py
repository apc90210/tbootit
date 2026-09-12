from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, case
from typing import List, Optional, Dict, Any
from app.database import get_db
from app import models, schemas
from app.routers.customers import log_audit
from app.services.barcodes import generate_barcode_for_product, generate_missing_barcodes
from app.services.product_json_service import generate_canonical_sku
from app.services.avito_schema_service import upsert_avito_category_schema, upsert_product_avito_attributes
import json

router = APIRouter()

STANDARD_CATEGORY_CHARACTERISTICS: Dict[str, List[str]] = {
    "Ноутбуки": [
        "Процессор", "Оперативная память", "Объем накопителя", "Тип накопителя",
        "Видеокарта", "Диагональ экрана", "Разрешение экрана", "Операционная система"
    ],
    "Системные блоки": [
        "Процессор", "Оперативная память", "Объем накопителя", "Видеокарта",
        "Материнская плата", "Блок питания", "Корпус"
    ],
    "Принтеры и МФУ": [
        "Тип устройства", "Технология печати", "Цветность печати", "Максимальный формат",
        "Двусторонняя печать", "Интерфейсы", "Wi-Fi"
    ],
    "Мониторы": [
        "Диагональ", "Разрешение", "Тип матрицы", "Частота обновления", "Разъемы"
    ],
    "Комплектующие": [
        "Тип комплектующего", "Сокет", "Тип памяти", "Объем", "Форм-фактор"
    ],
    "Оргтехника": [
        "Тип устройства", "Назначение", "Интерфейсы"
    ]
}

VALID_TRANSITIONS: Dict[str, List[str]] = {
    "draft": ["in_stock", "archived"],
    "imported": ["in_stock", "archived", "reserved", "sold", "written_off"],
    "in_stock": ["reserved", "sold", "written_off", "archived", "draft"],
    "reserved": ["in_stock", "sold", "archived"],
    "sold": ["archived"],
    "written_off": ["archived"],
    "archived": ["in_stock"]
}

def log_product_event(db: Session, product_id: int, event_type: str, old_value=None, new_value=None, comment=None):
    old_val_str = json.dumps(old_value, default=str) if old_value else None
    new_val_str = json.dumps(new_value, default=str) if new_value else None
    ev = models.ProductEvent(
        product_id=product_id,
        event_type=event_type,
        old_value=old_val_str,
        new_value=new_val_str,
        comment=comment
    )
    db.add(ev)
    return ev

@router.get("/", response_model=schemas.ProductListResponse)
def get_products(
    q: Optional[str] = None,
    status: Optional[str] = None,
    source: Optional[str] = None,
    category_id: Optional[int] = None,
    brand: Optional[str] = None,
    model: Optional[str] = None,
    storage_location: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    avito_ready: Optional[bool] = None,
    site_ready: Optional[bool] = None,
    sort: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(models.Product)
    
    if q:
        q_clean = q.strip()
        conditions = [
            models.Product.title.ilike(f"%{q_clean}%"),
            models.Product.sku.ilike(f"%{q_clean}%"),
            models.Product.barcode.ilike(f"%{q_clean}%"),
            models.Product.brand.ilike(f"%{q_clean}%"),
            models.Product.model.ilike(f"%{q_clean}%"),
            models.Product.serial_number.ilike(f"%{q_clean}%")
        ]
        if q_clean.isdigit():
            conditions.append(models.Product.id == int(q_clean))
        query = query.filter(or_(*conditions))
    if status:
        query = query.filter(models.Product.status == status)
    if source:
        query = query.filter(models.Product.source_type == source)
    if category_id:
        query = query.filter(models.Product.category_id == category_id)
    if brand:
        query = query.filter(models.Product.brand.ilike(f"%{brand}%"))
    if model:
        query = query.filter(models.Product.model.ilike(f"%{model}%"))
    if storage_location:
        query = query.filter(models.Product.storage_location.ilike(f"%{storage_location}%"))
    if min_price is not None:
        query = query.filter(models.Product.sale_price >= min_price)
    if max_price is not None:
        query = query.filter(models.Product.sale_price <= max_price)
    if avito_ready is not None:
        if avito_ready:
            query = query.filter(models.Product.avito_title != None, models.Product.avito_description != None)
        else:
            query = query.filter(or_(models.Product.avito_title == None, models.Product.avito_description == None))
    if site_ready is not None:
        if site_ready:
            query = query.filter(models.Product.site_title != None, models.Product.site_description != None)
        else:
            query = query.filter(or_(models.Product.site_title == None, models.Product.site_description == None))
            
    if q:
        q_clean = q.strip()
        query = query.order_by(
            case((models.Product.barcode == q_clean, 0), (models.Product.sku == q_clean, 1), else_=2)
        )

    if sort == "price_asc":
        query = query.order_by(models.Product.sale_price.asc())
    elif sort == "price_desc":
        query = query.order_by(models.Product.sale_price.desc())
    elif sort == "created_asc":
        query = query.order_by(models.Product.created_at.asc())
    elif sort == "created_desc":
        query = query.order_by(models.Product.created_at.desc())
    else:
        query = query.order_by(models.Product.id.desc())
        
    total = query.count()
    items = query.offset(offset).limit(limit).all()
    
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@router.get("/filter-options")
def get_product_filter_options(
    q: Optional[str] = None,
    category_id: Optional[int] = None,
    brand: Optional[str] = None,
    model: Optional[str] = None,
    status: Optional[str] = None,
    storage_location: Optional[str] = None,
    avito_ready: Optional[bool] = None,
    site_ready: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    # Approach A: dependent facets per level
    
    # Base query for calculating dependent facets
    base_query = db.query(models.Product)
    if q:
        base_query = base_query.filter(
            or_(
                models.Product.title.ilike(f"%{q}%"),
                models.Product.sku.ilike(f"%{q}%"),
                models.Product.brand.ilike(f"%{q}%"),
                models.Product.model.ilike(f"%{q}%"),
                models.Product.serial_number.ilike(f"%{q}%")
            )
        )

    # 1. Categories - calculated without category/brand/model/status/storage/avito/site
    cat_query = base_query
    categories = [{"id": cid, "name": n, "count": c} for cid, n, c in 
                  db.query(models.Category.id, models.Category.name, func.count(models.Product.id))
                  .join(models.Product, models.Category.id == models.Product.category_id)
                  .filter(models.Product.id.in_(cat_query.with_entities(models.Product.id)))
                  .group_by(models.Category.id, models.Category.name)
                  .order_by(models.Category.name).all()]

    # Apply category_id for next levels
    q_cat = base_query
    if category_id:
        q_cat = q_cat.filter(models.Product.category_id == category_id)

    # 2. Brands - calculated with category
    brands = [{"value": b, "count": c} for b, c in 
              db.query(models.Product.brand, func.count(models.Product.id))
              .filter(models.Product.brand != None, models.Product.brand != "")
              .filter(models.Product.id.in_(q_cat.with_entities(models.Product.id)))
              .group_by(models.Product.brand)
              .order_by(models.Product.brand).all()]

    # Apply brand for next levels
    q_brand = q_cat
    if brand:
        q_brand = q_brand.filter(models.Product.brand.ilike(f"%{brand}%"))

    # 3. Models - calculated with category + brand
    models_list = [{"value": m, "count": c} for m, c in 
                   db.query(models.Product.model, func.count(models.Product.id))
                   .filter(models.Product.model != None, models.Product.model != "")
                   .filter(models.Product.id.in_(q_brand.with_entities(models.Product.id)))
                   .group_by(models.Product.model)
                   .order_by(models.Product.model).all()]

    # Apply model for next levels
    q_model = q_brand
    if model:
        q_model = q_model.filter(models.Product.model.ilike(f"%{model}%"))

    # 4. Statuses - calculated with category + brand + model
    status_labels = {
        "draft": "Черновик",
        "in_stock": "В наличии",
        "reserved": "Зарезервирован",
        "sold": "Продан",
        "in_repair": "В ремонте",
        "for_parts": "На запчасти",
        "written_off": "Списан",
        "published_site": "На сайте",
        "published_avito": "На Авито"
    }
    statuses = [{"value": s, "label": status_labels.get(s, s), "count": c} for s, c in 
                db.query(models.Product.status, func.count(models.Product.id))
                .filter(models.Product.status != None, models.Product.status != "")
                .filter(models.Product.id.in_(q_model.with_entities(models.Product.id)))
                .group_by(models.Product.status)
                .order_by(models.Product.status).all()]

    # Apply status for next levels
    q_status = q_model
    if status:
        q_status = q_status.filter(models.Product.status == status)

    # 5. Storage locations - calculated with category + brand + model + status
    storage_locations = [{"value": loc, "count": c} for loc, c in 
                         db.query(models.Product.storage_location, func.count(models.Product.id))
                         .filter(models.Product.storage_location != None, models.Product.storage_location != "")
                         .filter(models.Product.id.in_(q_status.with_entities(models.Product.id)))
                         .group_by(models.Product.storage_location)
                         .order_by(models.Product.storage_location).all()]

    # Apply storage_location
    q_storage = q_status
    if storage_location:
        q_storage = q_storage.filter(models.Product.storage_location.ilike(f"%{storage_location}%"))

    # 6. Avito & Site ready - calculated with all previous filters
    total_count = q_storage.count()
    avito_ready_count = q_storage.filter(models.Product.avito_title != None, models.Product.avito_description != None).count()
    site_ready_count = q_storage.filter(models.Product.site_title != None, models.Product.site_description != None).count()
    
    return {
        "selected": {
            "q": q,
            "category_id": category_id,
            "brand": brand,
            "model": model,
            "status": status,
            "storage_location": storage_location,
            "avito_ready": avito_ready,
            "site_ready": site_ready
        },
        "order": [
            "categories",
            "brands",
            "models",
            "statuses",
            "storage_locations",
            "avito_ready",
            "site_ready"
        ],
        "brands": brands,
        "models": models_list,
        "statuses": statuses,
        "storage_locations": storage_locations,
        "categories": categories,
        "avito_ready": [
            {"value": "true", "label": "Готово к Авито", "count": avito_ready_count},
            {"value": "false", "label": "Не готово к Авито", "count": total_count - avito_ready_count}
        ] if total_count > 0 else [],
        "site_ready": [
            {"value": "true", "label": "Готово к сайту", "count": site_ready_count},
            {"value": "false", "label": "Не готово к сайту", "count": total_count - site_ready_count}
        ] if total_count > 0 else []
    }

@router.get("/meta")
def get_meta(db: Session = Depends(get_db)):
    statuses = {
        "draft": "Черновик",
        "in_stock": "В наличии",
        "reserved": "Зарезервирован",
        "sold": "Продан",
        "in_repair": "В ремонте",
        "for_parts": "На запчасти",
        "written_off": "Списан",
        "published_site": "На сайте",
        "published_avito": "На Авито"
    }
    repair_statuses = {
        "new": "Новая заявка",
        "accepted": "Принято",
        "diagnostics": "Диагностика",
        "waiting_parts": "Ожидание запчастей",
        "in_progress": "В работе",
        "ready": "Готово",
        "issued": "Выдано",
        "cancelled": "Отменено"
    }
    brands = [r[0] for r in db.query(models.Product.brand).filter(models.Product.brand != None).distinct()]
    locations = [r[0] for r in db.query(models.Product.storage_location).filter(models.Product.storage_location != None).distinct()]
    
    return {
        "product_statuses": statuses,
        "repair_statuses": repair_statuses,
        "brands": brands,
        "storage_locations": locations
    }

@router.get("/editor-meta")
def get_editor_meta(db: Session = Depends(get_db)):
    db_categories = [r[0] for r in db.query(models.Category.name).distinct().all() if r[0]]
    all_categories = list(STANDARD_CATEGORY_CHARACTERISTICS.keys())
    for c in db_categories:
        if c not in all_categories:
            all_categories.append(c)

    return {
        "categories": all_categories,
        "standard_characteristics": STANDARD_CATEGORY_CHARACTERISTICS,
        "category_characteristics": STANDARD_CATEGORY_CHARACTERISTICS,
        "conditions": ["Б/у", "Новое", "На запчасти", "Отличное"],
        "statuses": {
            "in_stock": "В наличии",
            "draft": "Черновик",
            "reserved": "Зарезервирован",
            "sold": "Продан",
            "in_repair": "В ремонте",
            "for_parts": "На запчасти",
            "written_off": "Списан"
        },
        "storage_locations": {
            "store": "Магазин",
            "workshop": "Мастерская",
            "archive": "Архив",
            "draft": "Черновик"
        }
    }

@router.get("/json/schema")
def get_products_json_schema(db: Session = Depends(get_db)):
    from app.services.product_json_service import generate_ai_prompt
    return {
        "format": "technoreboot-products",
        "version": 1,
        "ai_prompt": generate_ai_prompt(db)
    }

@router.post("/json/import")
def import_products_json(payload: dict, db: Session = Depends(get_db)):
    from app.services.product_json_service import import_canonical_products
    result = import_canonical_products(db, payload)
    if not result.get("success", False):
        raise HTTPException(status_code=400, detail={
            "message": "Ошибка валидации структуры JSON",
            "errors": result.get("errors", [])
        })
    return result

@router.get("/json/export")
def export_products_json(ids: Optional[str] = None, db: Session = Depends(get_db)):
    from app.services.product_json_service import export_canonical_products
    product_ids = None
    if ids:
        product_ids = [int(i.strip()) for i in ids.split(",") if i.strip().isdigit()]
    return export_canonical_products(db, product_ids)

@router.post("/json/export")
def export_products_json_post(payload: Optional[dict] = None, db: Session = Depends(get_db)):
    from app.services.product_json_service import export_canonical_products
    product_ids = None
    if payload and isinstance(payload, dict):
        raw_ids = payload.get("ids")
        if isinstance(raw_ids, list):
            product_ids = [int(x) for x in raw_ids if str(x).isdigit()]
        elif isinstance(raw_ids, str):
            product_ids = [int(i.strip()) for i in raw_ids.split(",") if i.strip().isdigit()]
    return export_canonical_products(db, product_ids)


@router.post("/", response_model=schemas.Product)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    # 1. Field validation
    if not product.title or not product.title.strip():
        raise HTTPException(status_code=400, detail="Название товара не может быть пустым")
    if product.sale_price is not None and product.sale_price < 0:
        raise HTTPException(status_code=400, detail="Цена продажи должна быть неотрицательной")
    if product.purchase_price is not None and product.purchase_price < 0:
        raise HTTPException(status_code=400, detail="Закупочная цена должна быть неотрицательной")
    if product.quantity is not None and product.quantity < 0:
        raise HTTPException(status_code=400, detail="Количество должно быть неотрицательным")

    # 2. SKU check / generation
    sku = (product.sku or "").strip()
    if not sku:
        new_sku = generate_canonical_sku()
        while db.query(models.Product).filter(models.Product.sku == new_sku).first():
            new_sku = generate_canonical_sku()
        sku = new_sku
    else:
        existing_sku = db.query(models.Product).filter(models.Product.sku == sku).first()
        if existing_sku:
            raise HTTPException(status_code=409, detail=f"Товар с артикулом '{sku}' уже существует")

    # 3. Barcode check
    if product.barcode and product.barcode.strip():
        bc_clean = product.barcode.strip()
        existing = db.query(models.Product).filter(models.Product.barcode == bc_clean).first()
        if existing:
            raise HTTPException(status_code=409, detail="Barcode already exists")

    # 4. Extract extra non-column fields
    data = product.model_dump()
    cat_name = (data.pop("category", None) or "").strip()
    chars = data.pop("characteristics", None) or {}
    data.pop("main_photo_url", None)

    data["sku"] = sku
    if "barcode" in data and data["barcode"]:
        data["barcode"] = data["barcode"].strip()

    db_product = models.Product(**data)

    # 5. Resolve category if provided
    avito_cat = None
    if cat_name:
        cat = db.query(models.Category).filter(models.Category.name == cat_name).first()
        if not cat:
            cat_slug = cat_name.lower().replace(" ", "-").replace("/", "-")
            cat = models.Category(name=cat_name, slug=cat_slug)
            db.add(cat)
            db.flush()
        db_product.category_id = cat.id

        avito_cat = upsert_avito_category_schema(
            db=db,
            category_name=cat_name,
            category_path=cat_name,
            characteristics=chars
        )
        if avito_cat:
            db_product.avito_category_id = avito_cat.id

    # 6. Characteristics
    if chars:
        db_product.avito_params_json = json.dumps(chars, ensure_ascii=False)
        db_product.source_attributes_json = json.dumps(chars, ensure_ascii=False)

    db.add(db_product)
    db.flush()

    if chars and db_product.avito_category_id:
        upsert_product_avito_attributes(
            db=db,
            product_id=db_product.id,
            category_id=db_product.avito_category_id,
            characteristics=chars
        )

    db.commit()
    db.refresh(db_product)

    log_audit(db, "product", db_product.id, "create", new_value=product.model_dump())
    log_product_event(db, db_product.id, "create", comment="Product created")

    if db_product.quantity and db_product.quantity > 0:
        mov = models.StockMovement(
            product_id=db_product.id,
            movement_type="initial",
            quantity_delta=db_product.quantity,
            old_quantity=0,
            new_quantity=db_product.quantity,
            reason="initial_stock"
        )
        db.add(mov)

    db.commit()
    return db_product

@router.get("/{product_id}/details", response_model=schemas.ProductDetails)
def get_product_details(product_id: int, db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    photos = db.query(models.ProductPhoto).filter(models.ProductPhoto.product_id == product_id).order_by(models.ProductPhoto.sort_order).all()
    events = db.query(models.ProductEvent).filter(models.ProductEvent.product_id == product_id).order_by(models.ProductEvent.created_at.desc()).all()
    movements = db.query(models.StockMovement).filter(models.StockMovement.product_id == product_id).order_by(models.StockMovement.created_at.desc()).all()
    
    margin = None
    if db_product.sale_price and db_product.purchase_price:
        margin = db_product.sale_price - db_product.purchase_price
        
    available = (db_product.quantity or 0) - (db_product.reserved_quantity or 0)
    
    # Avito Category and Characteristics
    avito_cat_name = db_product.avito_category.name if db_product.avito_category else db_product.avito_category_path
    avito_characteristics = {}
    if db_product.avito_params_json:
        try:
            legacy_p = json.loads(db_product.avito_params_json)
            if isinstance(legacy_p, dict):
                avito_characteristics.update(legacy_p)
        except Exception:
            pass
    if db_product.source_attributes_json:
        try:
            src_p = json.loads(db_product.source_attributes_json)
            if isinstance(src_p, dict):
                avito_characteristics.update(src_p)
        except Exception:
            pass
    if db_product.avito_attribute_values:
        for val_row in db_product.avito_attribute_values:
            if val_row.definition and val_row.definition.name:
                avito_characteristics[val_row.definition.name] = val_row.value or val_row.raw_value

    # Source Avito Link from ProductExternalListing
    ext_listing = db.query(models.ProductExternalListing).filter(
        models.ProductExternalListing.product_id == product_id,
        models.ProductExternalListing.marketplace == "avito"
    ).first()
    
    raw_source_url = ext_listing.external_url if ext_listing and ext_listing.external_url else None
    avito_source_url = None
    if raw_source_url and isinstance(raw_source_url, str):
        url_clean = raw_source_url.strip()
        if url_clean.startswith("https://") or url_clean.startswith("http://"):
            try:
                import urllib.parse
                parsed = urllib.parse.urlparse(url_clean)
                if parsed.hostname and (parsed.hostname == "avito.ru" or parsed.hostname.endswith(".avito.ru")):
                    avito_source_url = url_clean
            except Exception:
                pass

    # We must convert to dict first because we need to add fields not present in the DB model directly, or use model_validate/dump
    p_dict = {c.name: getattr(db_product, c.name) for c in db_product.__table__.columns}
    p_dict["price"] = db_product.sale_price
    p_dict["margin"] = margin
    p_dict["available_quantity"] = available
    p_dict["has_photos"] = len(photos) > 0
    p_dict["avito_ready"] = bool(db_product.avito_title and db_product.avito_description and db_product.avito_price if hasattr(db_product, 'avito_price') else True)
    p_dict["site_ready"] = bool(db_product.site_title and db_product.site_description)
    p_dict["photos"] = photos
    p_dict["events"] = events
    p_dict["stock_movements"] = movements
    p_dict["avito_category_name"] = avito_cat_name
    p_dict["avito_characteristics"] = avito_characteristics
    p_dict["characteristics"] = avito_characteristics
    p_dict["avito_source_url"] = avito_source_url
    
    return p_dict

@router.get("/{product_id}", response_model=schemas.Product)
def get_product(product_id: int, db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product

@router.put("/{product_id}", response_model=schemas.Product)
def full_update_product(product_id: int, product: schemas.ProductFullUpdate, db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Товар не найден")

    # 1. Validation
    if not product.title or not product.title.strip():
        raise HTTPException(status_code=400, detail="Название товара не может быть пустым")
    if product.sale_price is not None and product.sale_price < 0:
        raise HTTPException(status_code=400, detail="Цена продажи должна быть неотрицательной")
    if product.purchase_price is not None and product.purchase_price < 0:
        raise HTTPException(status_code=400, detail="Закупочная цена должна быть неотрицательной")
    if product.quantity is not None and product.quantity < 0:
        raise HTTPException(status_code=400, detail="Количество должно быть неотрицательным")

    # 2. SKU uniqueness check
    if product.sku and product.sku.strip():
        sku_clean = product.sku.strip()
        existing_sku = db.query(models.Product).filter(
            models.Product.sku == sku_clean,
            models.Product.id != product_id
        ).first()
        if existing_sku:
            raise HTTPException(status_code=409, detail=f"Товар с артикулом '{sku_clean}' уже существует")
        db_product.sku = sku_clean

    # 3. Barcode uniqueness check
    if product.barcode and product.barcode.strip():
        bc_clean = product.barcode.strip()
        existing_bc = db.query(models.Product).filter(
            models.Product.barcode == bc_clean,
            models.Product.id != product_id
        ).first()
        if existing_bc:
            raise HTTPException(status_code=409, detail="Barcode already exists")
        db_product.barcode = bc_clean
    elif product.barcode is not None and not product.barcode.strip():
        db_product.barcode = None

    # 4. Update basic fields
    old_data = {c.name: getattr(db_product, c.name) for c in db_product.__table__.columns}
    old_quantity = db_product.quantity or 0
    old_status = db_product.status

    db_product.title = product.title.strip()
    db_product.brand = product.brand.strip() if product.brand else None
    db_product.model = product.model.strip() if product.model else None
    db_product.serial_number = product.serial_number.strip() if product.serial_number else None
    db_product.condition = product.condition.strip() if product.condition else None
    db_product.description = product.description
    if product.purchase_price is not None:
        db_product.purchase_price = product.purchase_price
    if product.sale_price is not None:
        db_product.sale_price = product.sale_price
    if product.storage_location:
        db_product.storage_location = product.storage_location

    # 5. Quantity & Stock Movement
    new_quantity = product.quantity if product.quantity is not None else old_quantity
    if new_quantity != old_quantity:
        db_product.quantity = new_quantity
        delta = new_quantity - old_quantity
        mov = models.StockMovement(
            product_id=product_id,
            movement_type="manual_adjustment",
            quantity_delta=delta,
            old_quantity=old_quantity,
            new_quantity=new_quantity,
            reason="editor_update",
            comment="Количество изменено в редакторе товара"
        )
        db.add(mov)

    # 6. Status update
    if product.status and product.status != old_status:
        allowed = VALID_TRANSITIONS.get(old_status, [])
        if product.status not in allowed:
            raise HTTPException(status_code=400, detail=f"Invalid transition from {old_status} to {product.status}")
        db_product.status = product.status
        log_product_event(db, product_id, "update_status", old_value=old_status, new_value=product.status, comment="Статус изменен в редакторе")

    # 7. Category resolution
    cat_name = (product.category or "").strip()
    if cat_name:
        cat = db.query(models.Category).filter(models.Category.name == cat_name).first()
        if not cat:
            cat_slug = cat_name.lower().replace(" ", "-").replace("/", "-")
            cat = models.Category(name=cat_name, slug=cat_slug)
            db.add(cat)
            db.flush()
        db_product.category_id = cat.id

        avito_cat = upsert_avito_category_schema(db, category_name=cat_name, category_path=cat_name, characteristics=product.characteristics)
        if avito_cat:
            db_product.avito_category_id = avito_cat.id
    elif product.category_id:
        db_product.category_id = product.category_id

    # 8. Characteristics
    if product.characteristics is not None:
        db_product.avito_params_json = json.dumps(product.characteristics, ensure_ascii=False)
        db_product.source_attributes_json = json.dumps(product.characteristics, ensure_ascii=False)

        cat_for_attr = db_product.avito_category_id
        if not cat_for_attr and db_product.category:
            avito_cat = upsert_avito_category_schema(db, category_name=db_product.category.name, category_path=db_product.category.name, characteristics=product.characteristics)
            if avito_cat:
                cat_for_attr = avito_cat.id
                db_product.avito_category_id = cat_for_attr

        if cat_for_attr:
            upsert_product_avito_attributes(db, db_product.id, cat_for_attr, product.characteristics)

    db.commit()
    db.refresh(db_product)

    new_data = {c.name: getattr(db_product, c.name) for c in db_product.__table__.columns}
    log_audit(db, "product", db_product.id, "full_update", old_value=old_data, new_value=new_data)
    log_product_event(db, db_product.id, "full_update", old_value=old_data, new_value=new_data, comment="Товар полностью обновлен через редактор")
    db.commit()
    return db_product

@router.patch("/{product_id}", response_model=schemas.Product)
def update_product(product_id: int, product: schemas.ProductUpdate, db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if product.sale_price is not None and product.sale_price < 0:
        raise HTTPException(status_code=400, detail="Price must be non-negative")
    if product.purchase_price is not None and product.purchase_price < 0:
        raise HTTPException(status_code=400, detail="Price must be non-negative")
    if product.title is not None and len(product.title.strip()) == 0:
        raise HTTPException(status_code=400, detail="Title cannot be empty")
        
    if product.status is not None:
        raise HTTPException(status_code=400, detail="Use /status endpoint to update status")
    
    old_data = {c.name: getattr(db_product, c.name) for c in db_product.__table__.columns}
    update_data = product.model_dump(exclude_unset=True)
    if "status" in update_data:
        del update_data["status"]
        
    for key, value in update_data.items():
        setattr(db_product, key, value)
        
    db.commit()
    db.refresh(db_product)
    
    new_data = {c.name: getattr(db_product, c.name) for c in db_product.__table__.columns}
    log_audit(db, "product", db_product.id, "update", old_value=old_data, new_value=new_data)
    log_product_event(db, db_product.id, "update", old_value=old_data, new_value=new_data, comment="Product updated")
    db.commit()
    return db_product

@router.post("/{product_id}/status", response_model=schemas.Product)
@router.patch("/{product_id}/status", response_model=schemas.Product)
def update_product_status(product_id: int, status_update: schemas.ProductStatusUpdate, db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    old_status = db_product.status or "draft"
    new_status = status_update.status
    
    allowed = VALID_TRANSITIONS.get(old_status, [])
    if new_status not in allowed and old_status != new_status:
        raise HTTPException(status_code=400, detail=f"Invalid transition from {old_status} to {new_status}")
    
    db_product.status = new_status
    db.commit()
    db.refresh(db_product)
    
    log_audit(db, "product", db_product.id, "update_status", old_value={"status": old_status}, new_value={"status": new_status})
    log_product_event(db, db_product.id, "update_status", old_value=old_status, new_value=new_status, comment=status_update.reason or "Status changed")
    db.commit()
    return db_product

@router.get("/{product_id}/events", response_model=List[schemas.ProductEvent])
def get_product_events(product_id: int, db: Session = Depends(get_db)):
    return db.query(models.ProductEvent).filter(models.ProductEvent.product_id == product_id).order_by(models.ProductEvent.created_at.desc()).all()

@router.post("/{product_id}/events", response_model=schemas.ProductEvent)
def create_product_event(product_id: int, event: schemas.ProductEventCreate, db: Session = Depends(get_db)):
    ev = log_product_event(db, product_id, event.event_type, event.old_value, event.new_value, event.comment)
    db.commit()
    db.refresh(ev)
    return ev

@router.post("/{product_id}/stock-adjustment", response_model=schemas.Product)
def adjust_stock(product_id: int, adj: schemas.StockAdjustment, db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    old_q = db_product.quantity or 0
    new_q = old_q + adj.quantity_delta
    db_product.quantity = new_q
    
    mov = models.StockMovement(
        product_id=product_id,
        movement_type="manual_adjustment",
        quantity_delta=adj.quantity_delta,
        old_quantity=old_q,
        new_quantity=new_q,
        reason=adj.reason,
        comment=adj.comment
    )
    db.add(mov)
    
    log_product_event(db, product_id, "stock_adjustment", old_value=old_q, new_value=new_q, comment=adj.comment)
    log_audit(db, "product", product_id, "stock_adjustment", old_value={"quantity": old_q}, new_value={"quantity": new_q}, comment=adj.comment)
    
    db.commit()
    db.refresh(db_product)
    return db_product

@router.patch("/{product_id}/site-publication", response_model=schemas.Product)
def site_publication(product_id: int, pub: schemas.SitePublication, db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    db_product.is_published_site = pub.is_published_site
    if pub.site_title is not None:
        db_product.site_title = pub.site_title
    if pub.site_description is not None:
        db_product.site_description = pub.site_description
        
    log_product_event(db, product_id, "site_publication_prep", new_value=pub.model_dump(), comment="Prepared for site")
    db.commit()
    db.refresh(db_product)
    return db_product

@router.patch("/{product_id}/avito-publication", response_model=schemas.Product)
def avito_publication(product_id: int, pub: schemas.AvitoPublication, db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    db_product.is_published_avito = pub.is_published_avito
    if pub.avito_title is not None:
        db_product.avito_title = pub.avito_title
    if pub.avito_description is not None:
        db_product.avito_description = pub.avito_description
        
    log_product_event(db, product_id, "avito_publication_prep", new_value=pub.model_dump(), comment="Prepared for Avito")
    db.commit()
    db.refresh(db_product)
    return db_product

@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    old_status = db_product.status
    db_product.status = "written_off"
    db.commit()
    
    log_audit(db, "product", db_product.id, "delete_soft", old_value={"status": old_status}, new_value={"status": "written_off"})
    log_product_event(db, product_id, "delete_soft", old_value=old_status, new_value="written_off", comment="Product softly deleted (written_off)")
    db.commit()
    return {"message": "Product softly deleted (written_off)"}

@router.get("/by-barcode/{barcode}", response_model=schemas.Product)
def get_product_by_barcode(barcode: str, db: Session = Depends(get_db)):
    barcode_clean = barcode.strip()
    product = db.query(models.Product).filter(models.Product.barcode == barcode_clean).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Товар с таким штрихкодом не найден ({barcode_clean}).")
    return product

@router.post("/barcodes/generate-missing", response_model=schemas.BarcodeBulkGenerateResponse)
def generate_missing_barcodes_endpoint(db: Session = Depends(get_db)):
    res = generate_missing_barcodes(db, actor="operator")
    return res

@router.post("/{product_id}/barcode/generate", response_model=schemas.BarcodeGenerateResponse)
def generate_barcode_endpoint(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    res = generate_barcode_for_product(db, product, actor="operator")
    return res

@router.post("/batch", response_model=schemas.ProductBatchResponse)
def batch_update_products(batch_req: schemas.ProductBatchRequest, db: Session = Depends(get_db)):
    if not batch_req.product_ids:
        return schemas.ProductBatchResponse(
            success=True,
            updated_count=0,
            product_ids=[],
            message="Список товаров пуст"
        )

    products = db.query(models.Product).filter(models.Product.id.in_(batch_req.product_ids)).all()
    updated_ids = []

    for product in products:
        old_status = product.status
        old_location = product.storage_location
        changed = False

        if batch_req.status and batch_req.status.strip():
            target_status = batch_req.status.strip()
            allowed = VALID_TRANSITIONS.get(product.status, [])
            if product.status != target_status and target_status in allowed:
                product.status = target_status
                log_audit(db, "product", product.id, "batch_update_status", old_value={"status": old_status}, new_value={"status": target_status})
                log_product_event(db, product.id, "batch_update_status", old_value=old_status, new_value=target_status, comment=batch_req.comment or "Массовое изменение статуса")
                changed = True

        if batch_req.storage_location and batch_req.storage_location.strip():
            target_loc = batch_req.storage_location.strip()
            if product.storage_location != target_loc:
                product.storage_location = target_loc
                log_audit(db, "product", product.id, "batch_update_location", old_value={"storage_location": old_location}, new_value={"storage_location": target_loc})
                log_product_event(db, product.id, "batch_update_location", old_value=old_location, new_value=target_loc, comment=batch_req.comment or "Массовое изменение места хранения")
                changed = True

        if changed or batch_req.action == "touch":
            updated_ids.append(product.id)

    db.commit()

    return schemas.ProductBatchResponse(
        success=True,
        updated_count=len(updated_ids),
        product_ids=updated_ids,
        message=f"Успешно обновлено {len(updated_ids)} товаров"
    )
