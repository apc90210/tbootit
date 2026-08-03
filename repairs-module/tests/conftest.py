import pytest
import respx
from httpx import Response
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

CORE_URL = settings.core_api_base_url.rstrip("/")

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_core():
    with respx.mock(base_url=CORE_URL) as respx_mock:
        yield respx_mock
