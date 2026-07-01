import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.routers import health, products, categories, customers, repairs, sales, photos, admin, product_cards

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
            ("last_imported_at", "DATETIME")
        ]
        
        for col_name, col_type in updates:
            if col_name not in columns:
                try:
                    conn.execute(text(f"ALTER TABLE products ADD COLUMN {col_name} {col_type};"))
                except Exception as e:
                    print(f"Migration error on {col_name}: {e}")

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

app.include_router(health.router)
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(categories.router, prefix="/api/categories", tags=["categories"])
app.include_router(customers.router, prefix="/api/customers", tags=["customers"])
app.include_router(repairs.router, prefix="/api/repairs", tags=["repairs"])
app.include_router(sales.router, prefix="/api/sales", tags=["sales"])
app.include_router(photos.router, prefix="/api/products", tags=["photos"])
app.include_router(product_cards.router, prefix="/api/product-cards", tags=["product-cards"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
