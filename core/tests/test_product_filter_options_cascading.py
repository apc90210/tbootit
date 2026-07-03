from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, get_db
from sqlalchemy.orm import sessionmaker
import pytest
from app import models

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Categories
    c1 = models.Category(id=1, name="Laptops")
    c2 = models.Category(id=2, name="Phones")
    db.add(c1)
    db.add(c2)
    db.commit()
    
    # Products
    # Laptop 1: Lenovo, ThinkPad
    p1 = models.Product(
        sku="TEST-SKU-1", title="Lenovo ThinkPad",
        category_id=1, brand="Lenovo", model="ThinkPad", status="in_stock", 
        storage_location="A1", avito_title="t", avito_description="d", site_title="t", site_description="d"
    )
    # Laptop 2: Apple, MacBook
    p2 = models.Product(
        sku="TEST-SKU-2", title="Apple MacBook",
        category_id=1, brand="Apple", model="MacBook", status="draft", 
        storage_location="A2", avito_title=None, avito_description=None, site_title=None, site_description=None
    )
    # Phone 1: Apple, iPhone
    p3 = models.Product(
        sku="TEST-SKU-3", title="Apple iPhone",
        category_id=2, brand="Apple", model="iPhone", status="sold", 
        storage_location="B1", avito_title="t", avito_description="d", site_title=None, site_description=None
    )
    # Phone 2: Samsung, Galaxy
    p4 = models.Product(
        sku="TEST-SKU-4", title="Samsung Galaxy",
        category_id=2, brand="Samsung", model="Galaxy", status="in_stock", 
        storage_location="B2", avito_title=None, avito_description=None, site_title="t", site_description="d"
    )
    
    db.add_all([p1, p2, p3, p4])
    db.commit()
    yield
    db.close()

def test_cascading_filters_no_params():
    response = client.get("/api/products/filter-options")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["categories"]) == 2
    assert len(data["brands"]) == 3 # Lenovo, Apple, Samsung
    assert len(data["models"]) == 4
    assert len(data["statuses"]) == 3 # in_stock, draft, sold
    assert len(data["storage_locations"]) == 4

def test_cascading_filters_with_category():
    response = client.get("/api/products/filter-options?category_id=1")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["categories"]) == 2 # category should still have all
    assert len(data["brands"]) == 2 # Lenovo, Apple
    assert {"value": "Samsung", "count": 1} not in data["brands"]
    
def test_cascading_filters_with_category_and_brand():
    response = client.get("/api/products/filter-options?category_id=1&brand=Apple")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["brands"]) == 2 # brands shouldn't be filtered by brand
    assert len(data["models"]) == 1 # only MacBook
    assert data["models"][0]["value"] == "MacBook"
    
def test_cascading_filters_with_category_brand_and_model():
    response = client.get("/api/products/filter-options?category_id=1&brand=Lenovo&model=ThinkPad")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["statuses"]) == 1 # only in_stock
    assert data["statuses"][0]["value"] == "in_stock"
    
def test_selected_persisted_in_response():
    response = client.get("/api/products/filter-options?category_id=1&brand=Lenovo")
    data = response.json()
    assert data["selected"]["category_id"] == 1
    assert data["selected"]["brand"] == "Lenovo"
    assert data["selected"]["model"] is None
