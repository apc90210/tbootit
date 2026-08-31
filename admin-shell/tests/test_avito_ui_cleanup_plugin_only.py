import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app, follow_redirects=False)
redirect_client = TestClient(app, follow_redirects=True)

class TestAvitoUiCleanupPluginOnly:

    def test_navigation_shows_extension_avito_entry(self):
        """Verify top navigation across dashboard shows 'Расширение Avito' pointing to /avito/extension."""
        res = client.get("/")
        assert res.status_code == 200
        assert 'href="/avito/extension"' in res.text
        assert "Расширение Avito" in res.text

    def test_navigation_has_no_legacy_avito_sync_entries(self):
        """Verify navigation bar does not contain legacy links /avito/accounts or /avito/probe."""
        res = client.get("/")
        assert res.status_code == 200
        assert 'href="/avito/accounts"' not in res.text
        assert 'href="/avito/probe"' not in res.text

    def test_legacy_avito_routes_hidden_from_navigation(self):
        """Verify legacy routes exist technically for backend tests but are hidden from UI navigation."""
        for route in ["/avito", "/avito/accounts", "/avito/probe"]:
            res = client.get(route)
            assert res.status_code == 200

    def test_extension_page_returns_200_and_clean_ui(self):
        """Verify /avito/extension returns 200 OK with clean plugin-only UI and no legacy sub-nav."""
        res = client.get("/avito/extension")
        assert res.status_code == 200
        assert "Интеграция через Chrome Extension" in res.text
        assert "Скачать расширение (ZIP, v0.2.33)" in res.text
        assert 'href="/avito/accounts"' not in res.text
        assert 'href="/avito/probe"' not in res.text

    def test_extension_download_returns_200_zip(self):
        """Verify /avito/extension/download returns 200 OK with ZIP attachment."""
        res = client.get("/avito/extension/download")
        assert res.status_code == 200
        assert res.headers["content-type"] in ["application/zip", "application/x-zip-compressed"]
        assert "technoreboot-avito-extension" in res.headers.get("content-disposition", "")

    def test_product_detail_modal_has_no_stale_avito_controls(self):
        """Verify index.html has no tab-avito or stale owner-visible sync controls in productModal."""
        res = client.get("/")
        assert res.status_code == 200
        assert 'onclick="switchTab(\'tab-avito\')"' not in res.text
        assert 'id="tab-avito"' not in res.text
        assert 'id="iAvitoReady"' not in res.text

    def test_backend_core_apis_and_models_preserved(self):
        """Verify backend endpoints for category/attribute models and proxy routes remain registered."""
        routes = [r.path for r in app.routes]
        assert "/admin-api/products/{product_id}/avito-attributes" in routes
        assert "/admin-api/avito/categories/{category_id}/schema" in routes
        assert "/avito/extension" in routes
        assert "/avito/extension/download" in routes
