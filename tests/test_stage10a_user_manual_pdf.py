import re
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
import pymupdf
from pypdf import PdfReader

REPO_ROOT = Path(__file__).resolve().parent.parent

# Clean up module imports to load admin-shell app
for k in list(sys.modules.keys()):
    if k == 'app' or k.startswith('app.'):
        mod = sys.modules[k]
        if hasattr(mod, '__file__') and mod.__file__:
            if 'admin-shell' not in mod.__file__:
                sys.modules.pop(k, None)

admin_shell_path = str(REPO_ROOT / 'admin-shell')
if admin_shell_path in sys.path:
    sys.path.remove(admin_shell_path)
sys.path.insert(0, admin_shell_path)

import app.main as admin_main
app = admin_main.app
client = TestClient(app)

PDF_PATH = REPO_ROOT / "admin-shell" / "app" / "static" / "docs" / "TECHNOREBOOT_USER_MANUAL_RU.pdf"

@pytest.fixture
def owner_headers():
    return {
        'x-client-cert-verify': 'SUCCESS',
        'x-client-cert-serial': '1001',
        'x-auth-subject': 'Technoreboot Owner',
        'x-auth-is-owner': 'true'
    }

@pytest.fixture
def user_headers():
    return {
        'x-client-cert-verify': 'SUCCESS',
        'x-client-cert-serial': '1002',
        'x-auth-subject': 'Technoreboot Seller',
        'x-auth-is-owner': 'false'
    }

def test_user_manual_pdf_exists_and_valid():
    assert PDF_PATH.exists(), f"PDF not found at {PDF_PATH}"
    raw = PDF_PATH.read_bytes()
    assert raw.startswith(b"%PDF"), "PDF does not start with %PDF header"
    assert len(raw) > 1_000_000, f"PDF file size suspiciously small: {len(raw)} bytes"

    doc = pymupdf.open(str(PDF_PATH))
    page_count = len(doc)
    assert page_count >= 15, f"Expected >= 15 pages, got {page_count}"

    all_text = ""
    for idx, page in enumerate(doc):
        txt = page.get_text()
        assert len(txt.strip()) > 0, f"Page {idx+1} has no extracted text"
        all_text += f"\n--- Page {idx+1} ---\n" + txt

    assert "Руководство пользователя" in all_text
    assert "Товары" in all_text
    assert "Avito" in all_text
    assert "Продажи" in all_text
    assert "Ремонты" in all_text
    assert "Отчёты" in all_text
    doc.close()

def test_user_manual_toc_and_bookmarks():
    doc = pymupdf.open(str(PDF_PATH))
    page_count = len(doc)

    # Check TOC on page 2 (index 1)
    toc_page = doc[1]
    links = toc_page.get_links()
    assert len(links) >= 15, f"Expected >= 15 clickable links on TOC page, got {len(links)}"

    # Check PDF Outlines / Bookmarks
    bookmarks = doc.get_toc()
    assert len(bookmarks) >= 17, f"Expected >= 17 bookmarks, got {len(bookmarks)}"
    for lvl, title, pno in bookmarks:
        assert 1 <= pno <= page_count, f"Bookmark '{title}' points to invalid page {pno}"
    doc.close()

def test_user_manual_security_clean():
    doc = pymupdf.open(str(PDF_PATH))
    all_text = "".join(p.get_text() for p in doc)
    doc.close()

    forbidden_patterns = [
        r"BEGIN (?:RSA|OPENSSH|EC|DSA) PRIVATE KEY",
        r"ssh-rsa AAAA",
        r"password\s*[:=]\s*['\"][^'\"]+['\"]",
        r"api_token\s*[:=]\s*['\"][^'\"]+['\"]",
        r"/srv/technoreboot",
        r"C:\\tbootit\\",
        r"update_vds",
    ]
    for pattern in forbidden_patterns:
        matches = re.findall(pattern, all_text, re.IGNORECASE)
        assert len(matches) == 0, f"Security violation: found forbidden pattern '{pattern}' in user manual"

def test_admin_shell_download_endpoint(owner_headers, user_headers):
    # Test OWNER access
    res_owner = client.get("/help/user-manual.pdf", headers=owner_headers)
    assert res_owner.status_code == 200
    assert res_owner.headers.get("content-type") == "application/pdf"
    assert "attachment" in res_owner.headers.get("content-disposition", "")
    assert "TECHNOREBOOT_USER_MANUAL_RU.pdf" in res_owner.headers.get("content-disposition", "")
    assert res_owner.content.startswith(b"%PDF")
    assert len(res_owner.content) > 1_000_000

    # Test SELLER/USER access
    res_user = client.get("/help/user-manual.pdf", headers=user_headers)
    assert res_user.status_code == 200
    assert res_user.headers.get("content-type") == "application/pdf"
    assert "attachment" in res_user.headers.get("content-disposition", "")
    assert res_user.content.startswith(b"%PDF")

def test_admin_shell_help_page(owner_headers):
    res = client.get("/help", headers=owner_headers)
    assert res.status_code == 200
    assert "Руководство пользователя" in res.text
    assert "/help/user-manual.pdf" in res.text

def test_unified_navbar_contains_manual_link():
    # Inventory-sales base
    inv_base = (REPO_ROOT / "inventory-sales-module" / "app" / "templates" / "base.html").read_text(encoding="utf-8")
    assert "/help/user-manual.pdf" in inv_base
    assert "Инструкция" in inv_base

    # Repairs base
    rep_base = (REPO_ROOT / "repairs-module" / "app" / "templates" / "base.html").read_text(encoding="utf-8")
    assert "/help/user-manual.pdf" in rep_base
    assert "Инструкция" in rep_base

    # Admin shell templates
    admin_index = (REPO_ROOT / "admin-shell" / "app" / "templates" / "index.html").read_text(encoding="utf-8")
    assert "/help/user-manual.pdf" in admin_index
    assert "Инструкция" in admin_index
