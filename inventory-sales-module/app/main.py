from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers import health, products
import os

app = FastAPI(title="Inventory and Sales Module")

# Static files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Include routers
app.include_router(health.router)
app.include_router(products.router)
