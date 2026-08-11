import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.routers import health, products, categories, customers, repairs, sales, photos, admin, product_cards, reports

# Ensure directories exist
os.makedirs(settings.storage_root, exist_ok=True)
os.makedirs(os.path.join(settings.storage_root, "product_photos"), exist_ok=True)
os.makedirs(os.path.dirname(settings.database_url.replace('sqlite:///', '')), exist_ok=True)

# Create tables
Base.metadata.create_all(bind=engine)

# Ad-hoc migrations for Stage 02
def migrate_db():
    from sqlalchemy import text
    with engine.begin() as conn:
        res = conn.execute(text("PRAGMA table_info(products);")).fetchall()
        columns = [row[1] for row in res]
        
        updates = [
            ("quantity", "INTEGER DEFAULT 0"),
            ("reserved_quantity", "INTEGER DEFAULT 0"),
            ("min_price", "FLOAT"),
            ("market_price", "FLOAT"),
            ("notes", "TEXT"),
            ("is_published_site", "INTEGER DEFAULT 0"),
            ("is_published_avito", "INTEGER DEFAULT 0"),
            ("site_title", "VARCHAR"),
            ("site_description", "TEXT"),
            ("avito_title", "VARCHAR"),
            ("avito_description", "TEXT"),
            ("avito_category_path", "TEXT"),
            ("avito_goods_type", "VARCHAR"),
            ("avito_condition", "VARCHAR"),
            ("avito_params_json", "TEXT"),
            ("avito_contact_name", "VARCHAR"),
            ("avito_phone", "VARCHAR"),
            ("avito_address", "VARCHAR"),
            ("avito_seller_type", "VARCHAR"),
            ("source_json", "TEXT"),
            ("source_type", "VARCHAR"),
            ("last_imported_at", "DATETIME"),
            ("barcode", "VARCHAR")
        ]
        
        for col_name, col_type in updates:
            if col_name not in columns:
                try:
                    conn.execute(text(f"ALTER TABLE products ADD COLUMN {col_name} {col_type};"))
                except Exception as e:
                    print(f"Migration error on {col_name}: {e}")

        # Ensure index for barcode
        try:
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_products_barcode ON products(barcode) WHERE barcode IS NOT NULL AND barcode != '';"))
        except Exception as e:
            print(f"Index creation warning: {e}")

        # Migrate sales table for Stage 04C & Stage 05C
        res_sales = conn.execute(text("PRAGMA table_info(sales);")).fetchall()
        sales_columns = [row[1] for row in res_sales]
        sales_updates = [
            ("status", "VARCHAR DEFAULT 'completed'"),
            ("cancelled_at", "DATETIME"),
            ("cancel_reason", "TEXT"),
            ("canceled_by", "VARCHAR"),
            ("original_sale_id", "INTEGER"),
            ("replaced_by_sale_id", "INTEGER"),
            ("source_sale_id", "INTEGER"),
            ("superseded_by_sale_id", "INTEGER"),
            ("reissued_at", "DATETIME"),
            ("warranty_days", "INTEGER"),
            ("warranty_enabled", "INTEGER DEFAULT 1"),
            ("source_type", "VARCHAR"),
            ("source_id", "INTEGER")
        ]
        for col_name, col_type in sales_updates:
            if col_name not in sales_columns:
                try:
                    conn.execute(text(f"ALTER TABLE sales ADD COLUMN {col_name} {col_type};"))
                except Exception as e:
                    print(f"Migration error on {col_name}: {e}")

        try:
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_sales_source_type_source_id ON sales(source_type, source_id) WHERE source_type IS NOT NULL AND source_id IS NOT NULL;"))
        except Exception as e:
            print(f"Index creation error on ix_sales_source_type_source_id: {e}")

        # Migrate organization_settings table
        res_org = conn.execute(text("PRAGMA table_info(organization_settings);")).fetchall()
        org_columns = [row[1] for row in res_org]
        org_updates = [
            ("warranty_text", "TEXT"),
            ("no_warranty_text", "TEXT")
        ]
        for col_name, col_type in org_updates:
            if col_name not in org_columns:
                try:
                    conn.execute(text(f"ALTER TABLE organization_settings ADD COLUMN {col_name} {col_type};"))
                except Exception as e:
                    print(f"Migration error on {col_name}: {e}")

        # Seed organization settings if not present
        settings_count = conn.execute(text("SELECT COUNT(*) FROM organization_settings")).scalar()
        if settings_count == 0:
            conn.execute(text("""
                INSERT INTO organization_settings (
                    organization_name, inn, address, phone, default_customer_label, warranty_text, no_warranty_text
                ) VALUES (
                    'ИП Атанов Павел Сергеевич',
                    '667009336901',
                    'Свердловская обл. г. Екатеринбург, ул. Кузнецова, дом 10',
                    '+7 343 344 88 95',
                    'Частное лицо',
                    'На все Б/У товары предоставляется гарантия 30 дней.\nГарантийный ремонт и обмен Б/У товара возможен только в случае обнаружения дефекта товара в течении 30 дней с даты продажи.\nТовар Б/У без дефектов возврату - не подлежит, возможен обмен, но только по согласованию с менеджером магазина. В случае обнаружения дефекта товара по вине покупателя обмен и возврат товара – невозможен.\nНа программное обеспечение и расходные материалы гарантия не предоставляется.\nВ случае обнаружения неисправности – товар сдается на диагностику. По согласованию с продавцом – возможна мгновенная замена товара, без проведения диагностики.',
                    'Товар продаётся без гарантии, в том состоянии, в котором есть.\nПокупатель внимательно осмотрел товар при покупке.'
                )
            """))

        # Idempotent normalization of misclassified reissued sales
        try:
            conn.execute(text("""
                UPDATE sales
                SET status = 'reissued'
                WHERE source_sale_id IS NOT NULL AND status = 'completed';
            """))
        except Exception as e:
            print(f"Migration error on sales status normalization: {e}")

        # Migrate repair_orders table for Stage 05A
        res_repairs = conn.execute(text("PRAGMA table_info(repair_orders);")).fetchall()
        repairs_columns = [row[1] for row in res_repairs]
        repairs_updates = [
            ("number", "TEXT"),
            ("status", "TEXT DEFAULT 'received'"),
            ("customer_id", "INTEGER"),
            ("customer_name", "TEXT"),
            ("customer_phone", "TEXT"),
            ("customer_email", "TEXT"),
            ("device_type", "TEXT"),
            ("brand", "TEXT"),
            ("model", "TEXT"),
            ("serial_number", "TEXT"),
            ("reported_issue", "TEXT"),
            ("completeness", "TEXT"),
            ("appearance", "TEXT"),
            ("customer_comment", "TEXT"),
            ("internal_note", "TEXT"),
            ("access_code_provided", "INTEGER DEFAULT 0"),
            ("assigned_to", "TEXT"),
            ("priority", "TEXT DEFAULT 'normal'"),
            ("accepted_at", "DATETIME"),
            ("created_at", "DATETIME"),
            ("updated_at", "DATETIME"),
            ("closed_at", "DATETIME"),
            ("issued_at", "DATETIME"),
            ("canceled_at", "DATETIME")
        ]
        for col_name, col_type in repairs_updates:
            if col_name not in repairs_columns:
                try:
                    conn.execute(text(f"ALTER TABLE repair_orders ADD COLUMN {col_name} {col_type};"))
                except Exception as e:
                    print(f"Migration error on repair_orders.{col_name}: {e}")

        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS repair_status_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repair_id INTEGER NOT NULL,
                    old_status TEXT,
                    new_status TEXT NOT NULL,
                    comment TEXT,
                    changed_by TEXT,
                    changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (repair_id) REFERENCES repair_orders (id)
                );
            """))
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_repair_orders_number ON repair_orders (number);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_repair_orders_status ON repair_orders (status);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_repair_orders_phone ON repair_orders (customer_phone);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_repair_orders_serial ON repair_orders (serial_number);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_repair_history_repair_id ON repair_status_history (repair_id);"))
        except Exception as e:
            print(f"Migration error on repair tables/indexes: {e}")

        # Migrate products table for Stage 06A
        res_prod = conn.execute(text("PRAGMA table_info(products);")).fetchall()
        prod_columns = [row[1] for row in res_prod]
        prod_updates = [
            ("source_origin", "VARCHAR DEFAULT 'manual'"),
            ("source_attributes_json", "TEXT")
        ]
        for col_name, col_type in prod_updates:
            if col_name not in prod_columns:
                try:
                    conn.execute(text(f"ALTER TABLE products ADD COLUMN {col_name} {col_type};"))
                except Exception as e:
                    print(f"Migration error on products.{col_name}: {e}")

        # Migrate product_photos table for Stage 06A photo deduplication
        res_photos = conn.execute(text("PRAGMA table_info(product_photos);")).fetchall()
        photos_columns = [row[1] for row in res_photos]
        photos_updates = [
            ("source_url", "VARCHAR"),
            ("content_hash", "VARCHAR")
        ]
        for col_name, col_type in photos_updates:
            if col_name not in photos_columns:
                try:
                    conn.execute(text(f"ALTER TABLE product_photos ADD COLUMN {col_name} {col_type};"))
                except Exception as e:
                    print(f"Migration error on product_photos.{col_name}: {e}")

        # Create product_external_listings table if not exists
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS product_external_listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                marketplace VARCHAR NOT NULL DEFAULT 'avito',
                external_account_key VARCHAR NOT NULL,
                external_item_id VARCHAR NOT NULL,
                external_url VARCHAR,
                remote_status VARCHAR NOT NULL DEFAULT 'active',
                remote_status_raw VARCHAR,
                source_title VARCHAR,
                source_price FLOAT,
                source_attributes_json TEXT,
                last_seen_at DATETIME,
                last_imported_at DATETIME,
                last_pushed_at DATETIME,
                sync_state VARCHAR NOT NULL DEFAULT 'synced',
                sync_error TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME,
                FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
            );
        """))

        try:
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_product_ext_listings_market_item ON product_external_listings(marketplace, external_item_id);"))
        except Exception as e:
            print(f"Index creation error on ix_product_ext_listings_market_item: {e}")

    try:
        from app.services.repair_migration import run_repair_additive_migration
        db_file = settings.database_url.replace("sqlite:///", "")
        run_repair_additive_migration(db_file)
    except Exception as e:
        print(f"Migration error on run_repair_additive_migration: {e}")

migrate_db()

app = FastAPI(title="Technoreboot Core API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/media", StaticFiles(directory=settings.storage_root), name="media")

from app.routers import settings as settings_router
from app.routers import integrations as integrations_router

app.include_router(health.router)
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(categories.router, prefix="/api/categories", tags=["categories"])
app.include_router(customers.router, prefix="/api/customers", tags=["customers"])
app.include_router(repairs.router, prefix="/api/repairs", tags=["repairs"])
app.include_router(sales.router, prefix="/api/sales", tags=["sales"])
app.include_router(photos.router, prefix="/api/products", tags=["photos"])
app.include_router(product_cards.router, prefix="/api/product-cards", tags=["product-cards"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(settings_router.router, prefix="/api", tags=["settings"])
app.include_router(integrations_router.router, prefix="/api/integrations", tags=["integrations"])
