import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Setup test DB
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def db_session():
    # Because main.py migrate_db() might have seeded it, let's clean it up
    Base.metadata.create_all(bind=engine)
    db = TestSessionLocal()
    db.execute(text("DELETE FROM organization_settings"))
    db.commit()
    yield db
    db.execute(text("DELETE FROM organization_settings"))
    db.commit()
    db.close()

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_get_organization_settings_returns_defaults(client, db_session):
    # Ensure DB is empty
    db_session.execute(text("DELETE FROM organization_settings"))
    db_session.commit()
    
    response = client.get("/api/settings/organization")
    assert response.status_code == 200
    data = response.json()
    
    assert data["organization_name"] == "ИП Атанов Павел Сергеевич"
    assert data["inn"] == "667009336901"
    assert "Кузнецова" in data["address"]
    assert "343" in data["phone"]
    assert "Гарантийный ремонт и обмен" in data["warranty_text"]
    assert "продаётся без гарантии" in data["no_warranty_text"]

def test_put_organization_settings_changes_values(client, db_session):
    payload = {
        "organization_name": "ООО Новая Компания",
        "inn": "1234567890",
        "address": "г. Москва",
        "phone": "+7 999 000 11 22",
        "warranty_text": "New Warranty",
        "no_warranty_text": "New No Warranty"
    }
    response = client.put("/api/settings/organization", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["organization_name"] == "ООО Новая Компания"
    assert data["warranty_text"] == "New Warranty"

    # Verify GET after PUT returns changed values
    get_response = client.get("/api/settings/organization")
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["organization_name"] == "ООО Новая Компания"
    assert get_data["warranty_text"] == "New Warranty"

def test_get_organization_settings_backfills_blank_values(client, db_session):
    # Insert a blank row
    db_session.execute(text("DELETE FROM organization_settings"))
    db_session.execute(text(
        "INSERT INTO organization_settings (organization_name, inn, address, phone, warranty_text, no_warranty_text) "
        "VALUES ('', ' ', NULL, '', '   ', '')"
    ))
    db_session.commit()
    
    response = client.get("/api/settings/organization")
    assert response.status_code == 200
    data = response.json()
    
    # Assert it was backfilled
    assert data["organization_name"] == "ИП Атанов Павел Сергеевич"
    assert data["inn"] == "667009336901"
    assert "Кузнецова" in data["address"]
    assert "343" in data["phone"]
    assert "Гарантийный ремонт и обмен" in data["warranty_text"]
    assert "продаётся без гарантии" in data["no_warranty_text"]

def test_get_organization_settings_partial_backfill(client, db_session):
    db_session.execute(text("DELETE FROM organization_settings"))
    db_session.execute(text(
        "INSERT INTO organization_settings (organization_name, inn, address, phone, warranty_text, no_warranty_text) "
        "VALUES ('Custom Org', '123', 'Custom Address', '999', '', '')"
    ))
    db_session.commit()
    
    response = client.get("/api/settings/organization")
    assert response.status_code == 200
    data = response.json()
    
    assert data["organization_name"] == "Custom Org"
    assert data["inn"] == "123"
    assert data["address"] == "Custom Address"
    assert data["phone"] == "999"
    assert "Гарантийный ремонт и обмен" in data["warranty_text"]
    assert "продаётся без гарантии" in data["no_warranty_text"]
