import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_avito_main_navigation():
    response = client.get("/avito")
    assert response.status_code == 200
    assert "Интеграция с Avito" in response.text
    assert "Обзор" in response.text

def test_avito_accounts_navigation():
    response = client.get("/avito/accounts")
    assert response.status_code == 200
    assert "Аккаунты Avito" in response.text

def test_avito_browser_navigation():
    response = client.get("/avito/accounts/test_acc/browser")
    assert response.status_code == 200
    assert "Авторизация Avito" in response.text
    assert "novnc/vnc.html" in response.text

def test_avito_probe_navigation():
    response = client.get("/avito/probe")
    assert response.status_code == 200
    assert "Пробный импорт 1 объявления" in response.text
