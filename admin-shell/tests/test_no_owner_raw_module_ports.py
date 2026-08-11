import re
import os
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_no_raw_module_ports_in_rendered_html():
    """
    Scans all rendered owner-facing pages to ensure zero raw module ports
    (8000, 8020, 8030, 8040, 8061) are present in href attributes or navigation.
    """
    raw_port_pattern = re.compile(r'href=["\']http://(localhost|127\.0\.0\.1):(8000|8020|8030|8040|8061)')
    
    pages = ["/", "/avito", "/avito/accounts", "/avito/probe"]
    for page in pages:
        response = client.get(page)
        assert response.status_code == 200
        matches = raw_port_pattern.findall(response.text)
        assert len(matches) == 0, f"Found raw module port links on {page}: {matches}"

def test_no_raw_module_ports_in_templates_source():
    """
    Scans source files of all admin-shell templates for raw ports in hrefs.
    """
    templates_dir = os.path.join(os.path.dirname(__file__), "..", "app", "templates")
    raw_port_pattern = re.compile(r'href=["\']http://(localhost|127\.0\.0\.1):(8000|8020|8030|8040|8061)')
    
    for root, _, files in os.walk(templates_dir):
        for f in files:
            if f.endswith(".html"):
                path = os.path.join(root, f)
                with open(path, "r", encoding="utf-8") as file:
                    content = file.read()
                    matches = raw_port_pattern.findall(content)
                    assert len(matches) == 0, f"Found raw module port link in template {f}: {matches}"
