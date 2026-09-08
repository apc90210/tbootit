import json
import uuid
import datetime
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app import models
from app.services.avito_schema_service import upsert_avito_category_schema, upsert_product_avito_attributes

CANONICAL_FORMAT = "technoreboot-products"
CANONICAL_VERSION = 1

def generate_canonical_sku() -> str:
    """Generate a clean unique SKU for imported products without SKU."""
    return f"PRD-{uuid.uuid4().hex[:8].upper()}"

def generate_ai_prompt(db: Optional[Session] = None) -> str:
    """
    Returns the authoritative AI prompt instructing external LLMs (ChatGPT, Gemini, etc.)
    to produce valid JSON strictly conforming to the Technoreboot canonical schema.
    """
    prompt = """Ты — интеллектуальный ассистент по каталогизации электроники для системы «ТехноРебут».
Твоя задача — преобразовать свободное описание одного или нескольких товаров в строго валидный JSON по каноническому стандарту Technoreboot.

### ПРАВИЛА И ТРЕБОВАНИЯ:
1. Выводи ТОЛЬКО валидный JSON. Никаких блоков Markdown (не используй ```json ... ```), никаких пояснений до или после JSON.
2. Кодировка UTF-8. Все цены и количества должны быть ЧИСЛАМИ (number), а не строками.
3. Формат структуры строго:
{
  "format": "technoreboot-products",
  "version": 1,
  "products": [
    ... список товаров ...
  ]
}
4. Основные поля каждого товара (products[i]):
   - "title" (строка, ОБЯЗАТЕЛЬНО): Понятное название товара (например: "Ноутбук Lenovo ThinkPad T480 14\"").
   - "category" (строка): Категория товара (одна из: "Ноутбуки", "Системные блоки", "Принтеры и МФУ", "Мониторы", "Комплектующие", "Оргтехника").
   - "brand" (строка): Производитель / бренд (например: "Lenovo", "HP", "Intel", "Asus").
   - "model" (строка): Модель устройства (например: "ThinkPad T480", "LaserJet Pro M404dn").
   - "price" (число): Розничная цена продажи в рублях (например: 25000.0).
   - "purchase_price" (число или null): Закупочная цена, если известна (иначе null).
   - "condition" (строка): Состояние ("Новое", "Б/у", "На запчасти" или "Отличное"). По умолчанию "Б/у".
   - "status" (строка): Статус ("in_stock" или "draft"). По умолчанию "in_stock".
   - "quantity" (число): Количество на складе (целое число, по умолчанию 1).
   - "description" (строка): Полное подробное описание товара для покупателя.
   - "storage_location" (строка): Место хранения (например: "Склад 1", "Витрина").
   - "barcode" (строка): Штрихкод (если известен, иначе пустая строка "").
   - "characteristics" (объект ключ-значение): Категорийные характеристики (см. ниже).
   - "photos" (массив строк): Ссылки на фото (если нет — передавай пустой массив []).

5. ПРАВИЛО КАТЕГОРИЙНЫХ ХАРАКТЕРИСТИК ("characteristics"):
   - Заполняй только реальные факты из текста. НЕ ВЫДУМЫВАЙ характеристики, которых нет в описании!
   - Характеристики адаптированы для площадки Avito:
     * Для категории "Ноутбуки":
       "Процессор", "Оперативная память", "Объем накопителя", "Тип накопителя", "Видеокарта", "Диагональ экрана", "Разрешение экрана", "Операционная система"
     * Для категории "Системные блоки":
       "Процессор", "Оперативная память", "Объем накопителя", "Видеокарта", "Материнская плата", "Блок питания", "Корпус"
     * Для категории "Принтеры и МФУ":
       "Тип устройства", "Технология печати", "Цветность печати", "Максимальный формат", "Двусторонняя печать", "Интерфейсы", "Wi-Fi"
     * Для категории "Мониторы":
       "Диагональ", "Разрешение", "Тип матрицы", "Частота обновления", "Разъемы"
     * Для категории "Комплектующие":
       Указывай релевантные параметры компонента (например: "Сокет", "Тип памяти", "Объем", "Форм-фактор").

### ПРИМЕР 1: ОДИН ТОВАР (Ноутбук)
{
  "format": "technoreboot-products",
  "version": 1,
  "products": [
    {
      "title": "Ноутбук Lenovo ThinkPad T480 14\\"",
      "category": "Ноутбуки",
      "brand": "Lenovo",
      "model": "ThinkPad T480",
      "price": 28000.0,
      "purchase_price": 18000.0,
      "condition": "Б/у",
      "status": "in_stock",
      "quantity": 1,
      "description": "Надежный корпоративный ноутбук в отличном техническом состоянии. Аккумулятор держит до 5 часов. Зарядное устройство в комплекте.",
      "storage_location": "Склад 1",
      "barcode": "",
      "characteristics": {
        "Процессор": "Intel Core i5-8250U",
        "Оперативная память": "16 ГБ",
        "Объем накопителя": "512 ГБ",
        "Тип накопителя": "SSD",
        "Видеокарта": "Intel UHD Graphics 620",
        "Диагональ экрана": "14\\"",
        "Разрешение экрана": "1920x1080 Full HD",
        "Операционная система": "Windows 10 Pro"
      },
      "photos": []
    }
  ]
}

### ПРИМЕР 2: НЕСКОЛЬКО ТОВАРОВ (Системный блок и МФУ)
{
  "format": "technoreboot-products",
  "version": 1,
  "products": [
    {
      "title": "Игровой ПК Core i5-10400F / GTX 1660 Super",
      "category": "Системные блоки",
      "brand": "TechnoReboot Custom",
      "model": "TR-Gaming-10400",
      "price": 42000.0,
      "purchase_price": 29000.0,
      "condition": "Б/у",
      "status": "in_stock",
      "quantity": 1,
      "description": "Сбалансированный игровой компьютер для CS2, Dota 2, GTA V и танков. Полностью обслужен, заменена термопаста.",
      "storage_location": "Витрина",
      "barcode": "",
      "characteristics": {
        "Процессор": "Intel Core i5-10400F",
        "Оперативная память": "16 ГБ DDR4",
        "Объем накопителя": "SSD 500 ГБ",
        "Видеокарта": "NVIDIA GeForce GTX 1660 Super 6GB",
        "Материнская плата": "ASUS PRIME B460M-A",
        "Блок питания": "Cougar 600W",
        "Корпус": "Zalman i3"
      },
      "photos": []
    },
    {
      "title": "Лазерное МФУ HP LaserJet Pro MFP M428dw",
      "category": "Принтеры и МФУ",
      "brand": "HP",
      "model": "LaserJet Pro MFP M428dw",
      "price": 31500.0,
      "purchase_price": 20000.0,
      "condition": "Б/у",
      "status": "in_stock",
      "quantity": 1,
      "description": "Скоростное МФУ для офиса: принтер, сканер, копир. Поддержка двусторонней печати и Wi-Fi. Картридж заправлен.",
      "storage_location": "Склад 1",
      "barcode": "",
      "characteristics": {
        "Тип устройства": "МФУ",
        "Технология печати": "Лазерная",
        "Цветность печати": "Черно-белая",
        "Максимальный формат": "A4",
        "Двусторонняя печать": "Да (автоматическая)",
        "Интерфейсы": "USB, Ethernet, Wi-Fi",
        "Wi-Fi": "Да"
      },
      "photos": []
    }
  ]
}
"""
    return prompt.strip()

def normalize_payload(raw_data: Any) -> Tuple[bool, List[str], List[Dict[str, Any]]]:
    """
    Normalizes any supported input structure into a list of product dictionaries.
    Supports:
    1. Canonical Technoreboot JSON: {"format": "technoreboot-products", "version": 1, "products": [...]}
    2. Legacy Single Card JSON: {"source": "...", "product": {...}, "avito": {...}}
    3. Plain array of product dictionaries: [{...}, {...}]
    """
    errors: List[str] = []
    products: List[Dict[str, Any]] = []

    if isinstance(raw_data, str):
        try:
            raw_data = json.loads(raw_data)
        except Exception as e:
            return False, [f"Некорректный JSON синтаксис: {str(e)}"], []

    if not isinstance(raw_data, (dict, list)):
        return False, ["Формат JSON должен быть объектом или массивом товаров."], []

    # 1. Canonical structure
    if isinstance(raw_data, dict) and raw_data.get("format") == CANONICAL_FORMAT:
        version = raw_data.get("version")
        if version != CANONICAL_VERSION:
            return False, [f"Неподдерживаемая версия формата: {version} (ожидается {CANONICAL_VERSION})"], []
        prod_list = raw_data.get("products")
        if not isinstance(prod_list, list):
            return False, ["Поле 'products' должно быть массивом товаров."], []
        if len(prod_list) == 0:
            return False, ["Массив 'products' пуст. Добавьте хотя бы один товар."], []
        products = prod_list

    # 2. Legacy single-card format
    elif isinstance(raw_data, dict) and "product" in raw_data and isinstance(raw_data["product"], dict):
        p_sec = raw_data["product"]
        av_sec = raw_data.get("avito") or {}
        chars = {}
        if isinstance(av_sec, dict) and isinstance(av_sec.get("parameters"), dict):
            chars = av_sec.get("parameters") or {}

        cat_name = "Без категории"
        if p_sec.get("category_path") and isinstance(p_sec["category_path"], list) and len(p_sec["category_path"]) > 0:
            cat_name = p_sec["category_path"][-1]

        normalized_p = {
            "sku": p_sec.get("sku"),
            "title": p_sec.get("title"),
            "category": cat_name,
            "brand": p_sec.get("brand"),
            "model": p_sec.get("model"),
            "price": p_sec.get("sale_price") if p_sec.get("sale_price") is not None else av_sec.get("price"),
            "purchase_price": p_sec.get("purchase_price"),
            "condition": p_sec.get("condition") or "Б/у",
            "status": "draft",
            "quantity": p_sec.get("quantity", 1),
            "description": p_sec.get("description") or av_sec.get("description", ""),
            "storage_location": p_sec.get("storage_location"),
            "barcode": p_sec.get("barcode"),
            "characteristics": chars,
            "photos": av_sec.get("photos") or []
        }
        products = [normalized_p]

    # 3. Direct array of products
    elif isinstance(raw_data, list):
        if len(raw_data) == 0:
            return False, ["Массив товаров пуст."], []
        products = raw_data

    # 4. Single product object
    elif isinstance(raw_data, dict) and ("title" in raw_data or "price" in raw_data):
        products = [raw_data]

    else:
        return False, ["Не распознан формат JSON. Ожидается канонический формат Technoreboot или список товаров."], []

    return True, [], products

def validate_product_record(p: Any, index: int) -> Tuple[bool, List[str]]:
    """Validates an individual product dictionary."""
    errors = []
    if not isinstance(p, dict):
        return False, [f"Товар #{index + 1}: запись должна быть объектом JSON."]

    title = p.get("title")
    if not title or not isinstance(title, str) or not title.strip():
        errors.append(f"Товар #{index + 1}: отсутствует обязательное название 'title'.")

    price = p.get("price")
    if price is not None:
        try:
            val_price = float(price)
            if val_price < 0:
                errors.append(f"Товар #{index + 1}: цена 'price' не может быть отрицательной ({price}).")
        except (ValueError, TypeError):
            errors.append(f"Товар #{index + 1}: поле 'price' должно быть числом, получено '{price}'.")

    purchase_price = p.get("purchase_price")
    if purchase_price is not None:
        try:
            float(purchase_price)
        except (ValueError, TypeError):
            errors.append(f"Товар #{index + 1}: поле 'purchase_price' должно быть числом, получено '{purchase_price}'.")

    chars = p.get("characteristics")
    if chars is not None and not isinstance(chars, dict):
        errors.append(f"Товар #{index + 1}: поле 'characteristics' должно быть объектом ключ-значение.")

    photos = p.get("photos")
    if photos is not None and not isinstance(photos, list):
        errors.append(f"Товар #{index + 1}: поле 'photos' должно быть массивом строк.")

    return len(errors) == 0, errors

def import_canonical_products(db: Session, payload_data: Any) -> Dict[str, Any]:
    """
    Validates and imports products from canonical or normalized JSON into the database.
    Enforces the safe Duplicate / Update Policy:
    - If 'id' is provided and product exists -> UPDATE.
    - If 'id' is provided and NOT found -> ERROR/SKIP.
    - If 'id' is NOT provided and 'sku' exists in DB -> SKIP (avoids accidental overwrite).
    - If 'id' is NOT provided and 'sku' is new/empty -> CREATE (generates SKU if needed).
    """
    valid_format, format_errors, products = normalize_payload(payload_data)
    if not valid_format:
        return {
            "success": False,
            "created_count": 0,
            "updated_count": 0,
            "skipped_count": 0,
            "errors": format_errors,
            "imported_product_ids": []
        }

    created_count = 0
    updated_count = 0
    skipped_count = 0
    errors: List[str] = []
    imported_ids: List[int] = []
    now = datetime.datetime.now(datetime.timezone.utc)

    for idx, p in enumerate(products):
        is_valid, record_errors = validate_product_record(p, idx)
        if not is_valid:
            errors.extend(record_errors)
            skipped_count += 1
            continue

        prod_id = p.get("id")
        sku = (p.get("sku") or "").strip()
        product = None
        operation = "created"

        # Case 1: Target internal ID provided
        if prod_id is not None:
            try:
                prod_id_int = int(prod_id)
            except (ValueError, TypeError):
                errors.append(f"Товар #{idx + 1}: Некорректный ID товара '{prod_id}'.")
                skipped_count += 1
                continue

            product = db.query(models.Product).filter(models.Product.id == prod_id_int).first()
            if not product:
                errors.append(f"Товар #{idx + 1}: Товар с ID {prod_id_int} не найден в базе данных.")
                skipped_count += 1
                continue
            operation = "updated"

        # Case 2: No internal ID provided
        else:
            if sku:
                existing_sku = db.query(models.Product).filter(models.Product.sku == sku).first()
                if existing_sku:
                    errors.append(f"Товар #{idx + 1}: Товар с артикулом '{sku}' уже существует (укажите 'id' для обновления).")
                    skipped_count += 1
                    continue
                product = models.Product(sku=sku)
                db.add(product)
                db.flush()
            else:
                new_sku = generate_canonical_sku()
                # Ensure unique SKU
                while db.query(models.Product).filter(models.Product.sku == new_sku).first():
                    new_sku = generate_canonical_sku()
                product = models.Product(sku=new_sku)
                db.add(product)
                db.flush()

        # Update product standard fields
        product.title = str(p.get("title") or "").strip()
        if p.get("brand") is not None:
            product.brand = str(p.get("brand")).strip()
        if p.get("model") is not None:
            product.model = str(p.get("model")).strip()
        if p.get("description") is not None:
            product.description = str(p.get("description"))
        if p.get("price") is not None:
            product.sale_price = float(p.get("price"))
        if p.get("purchase_price") is not None:
            product.purchase_price = float(p.get("purchase_price"))
        if p.get("condition") is not None:
            product.condition = str(p.get("condition"))
        if p.get("status") is not None:
            product.status = str(p.get("status"))
        elif operation == "created":
            product.status = "in_stock"
        if p.get("quantity") is not None:
            product.quantity = int(p.get("quantity"))
        if p.get("storage_location") is not None:
            product.storage_location = str(p.get("storage_location"))
        if p.get("barcode") is not None:
            product.barcode = str(p.get("barcode")).strip() or None

        # Resolve category
        cat_name = (p.get("category") or "Без категории").strip()
        cat = db.query(models.Category).filter(models.Category.name == cat_name).first()
        if not cat:
            cat_slug = cat_name.lower().replace(" ", "-").replace("/", "-")
            cat = models.Category(name=cat_name, slug=cat_slug)
            db.add(cat)
            db.flush()
        product.category_id = cat.id

        # Characteristics (category-specific)
        chars = p.get("characteristics")
        if chars is None:
            chars = {}

        product.avito_params_json = json.dumps(chars, ensure_ascii=False)
        product.source_attributes_json = json.dumps(chars, ensure_ascii=False)
        product.avito_title = product.title
        product.avito_description = product.description
        product.avito_condition = product.condition
        product.source_type = "canonical_json"
        product.last_imported_at = now

        # Dynamic Avito category & attributes upsert
        try:
            avito_cat = upsert_avito_category_schema(
                db=db,
                category_name=cat_name,
                category_path=cat_name,
                characteristics=chars
            )
            if avito_cat:
                product.avito_category_id = avito_cat.id
                upsert_product_avito_attributes(
                    db=db,
                    product_id=product.id,
                    category_id=avito_cat.id,
                    characteristics=chars
                )
        except Exception:
            pass  # Attributes schema is auxiliary and shouldn't block product creation

        # Event log
        event_comment = f"Успешно {'обновлен' if operation == 'updated' else 'создан'} через канонический JSON импорт"
        db_event = models.ProductEvent(
            product_id=product.id,
            event_type=f"json_import_{operation}",
            comment=event_comment
        )
        db.add(db_event)
        db.flush()

        if operation == "created":
            created_count += 1
        else:
            updated_count += 1
        imported_ids.append(product.id)

    db.commit()

    return {
        "success": True,
        "created_count": created_count,
        "updated_count": updated_count,
        "skipped_count": skipped_count,
        "errors": errors,
        "imported_product_ids": imported_ids
    }

def export_canonical_products(db: Session, product_ids: Optional[List[int]] = None) -> Dict[str, Any]:
    """
    Exports products into canonical Technoreboot JSON payload.
    Preserves common fields + category + category-specific characteristics with full round-trip fidelity.
    """
    query = db.query(models.Product)
    if product_ids:
        query = query.filter(models.Product.id.in_(product_ids))
    products_db = query.order_by(models.Product.id.asc()).all()

    exported_products: List[Dict[str, Any]] = []

    for prod in products_db:
        # Reconstruct characteristics
        chars: Dict[str, Any] = {}

        # 1. From ProductAvitoAttributeValue table
        attr_vals = db.query(models.ProductAvitoAttributeValue).filter(
            models.ProductAvitoAttributeValue.product_id == prod.id
        ).all()
        for val_row in attr_vals:
            key = val_row.definition.name if val_row.definition else val_row.attribute_definition_id
            raw = val_row.raw_value if val_row.raw_value is not None else val_row.value
            if raw is not None:
                # If JSON encoded array/dict, unpack it
                if str(raw).startswith(("[", "{")):
                    try:
                        parsed = json.loads(raw)
                        chars[str(key)] = parsed
                        continue
                    except Exception:
                        pass
                chars[str(key)] = raw

        # 2. Fallback or merge with avito_params_json
        if prod.avito_params_json:
            try:
                stored_params = json.loads(prod.avito_params_json)
                if isinstance(stored_params, dict):
                    for k, v in stored_params.items():
                        if k not in chars and v is not None:
                            chars[k] = v
            except Exception:
                pass

        # Collect photos
        photos = []
        if prod.photos:
            for ph in prod.photos:
                url_or_path = ph.url or ph.file_path
                if url_or_path:
                    photos.append(url_or_path)

        # Resolve category
        category_name = "Без категории"
        if prod.category and prod.category.name:
            category_name = prod.category.name
        elif prod.avito_category and prod.avito_category.name:
            category_name = prod.avito_category.name

        prod_record = {
            "id": prod.id,
            "sku": prod.sku or "",
            "title": prod.title or "",
            "category": category_name,
            "brand": prod.brand or "",
            "model": prod.model or "",
            "price": float(prod.sale_price or 0.0),
            "purchase_price": float(prod.purchase_price) if prod.purchase_price is not None else None,
            "condition": prod.condition or "Б/у",
            "status": prod.status or "in_stock",
            "quantity": prod.quantity if prod.quantity is not None else 1,
            "description": prod.description or "",
            "storage_location": prod.storage_location or "",
            "barcode": prod.barcode or "",
            "characteristics": chars,
            "photos": photos
        }
        exported_products.append(prod_record)

    return {
        "format": CANONICAL_FORMAT,
        "version": CANONICAL_VERSION,
        "products": exported_products
    }
