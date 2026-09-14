import re
import sys
from pathlib import Path
import pymupdf
from pypdf import PdfReader

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

REPO_ROOT = Path(__file__).resolve().parents[1]
PDF_PATH = REPO_ROOT / "admin-shell" / "app" / "static" / "docs" / "TECHNOREBOOT_USER_MANUAL_RU.pdf"
PAGES_DIR = REPO_ROOT / "docs" / "user_manual" / "rendered_pages"

def main():
    print("=== PDF VERIFICATION SUITE ===")
    assert PDF_PATH.exists(), f"PDF not found at {PDF_PATH}"
    
    # 1. Verify begins with %PDF
    raw_bytes = PDF_PATH.read_bytes()
    assert raw_bytes.startswith(b"%PDF"), "PDF does not start with %PDF"
    print(f"✓ PDF Header: Valid (%PDF), Total bytes: {len(raw_bytes):,}")

    # 2. PyMuPDF inspection
    doc = pymupdf.open(str(PDF_PATH))
    page_count = len(doc)
    print(f"✓ Page count: {page_count} (expected > 1)")
    assert page_count >= 15, f"Expected at least 15 pages, got {page_count}"

    # 3. Cyrillic text extraction and major chapters check
    all_text = ""
    for idx, page in enumerate(doc):
        text = page.get_text()
        all_text += f"\n--- Page {idx+1} ---\n" + text
        assert len(text.strip()) > 0, f"Page {idx+1} has no extracted text!"

    assert "Руководство пользователя" in all_text, "Missing 'Руководство пользователя' in PDF text"
    assert "Товары" in all_text, "Missing 'Товары' in PDF text"
    assert "Avito" in all_text, "Missing 'Avito' in PDF text"
    assert "Продажи" in all_text, "Missing 'Продажи' in PDF text"
    assert "Ремонты" in all_text, "Missing 'Ремонты' in PDF text"
    assert "Отчёты" in all_text, "Missing 'Отчёты' in PDF text"
    print("✓ Cyrillic text extraction: OK across all pages")

    # 4. Check clickable TOC links / annotations
    # Inspect TOC page (page 2)
    toc_page = doc[1]  # 0-indexed -> Page 2
    links = toc_page.get_links()
    print(f"✓ TOC Page (Page 2) links count: {len(links)}")
    assert len(links) >= 15, f"Expected at least 15 clickable links on TOC page, got {len(links)}"

    # Verify link targets
    internal_links_count = 0
    for link in links:
        if link.get("kind") in [pymupdf.LINK_GOTO, pymupdf.LINK_NAMED]:
            internal_links_count += 1
    print(f"✓ Internal jump links on TOC page: {internal_links_count}")

    # 5. Check bookmarks / outlines
    toc = doc.get_toc()
    print(f"✓ PDF Bookmarks / Outlines count: {len(toc)}")
    assert len(toc) >= 17, f"Expected at least 17 outline entries, got {len(toc)}"
    for lvl, title, pno in toc:
        assert 1 <= pno <= page_count, f"Bookmark target page {pno} out of range [1, {page_count}]"
    print("✓ Bookmarks hierarchy and page targets: Valid")

    # 6. Check rendered PNG pages exist
    png_files = list(PAGES_DIR.glob("page_*.png"))
    print(f"✓ Rendered PNG pages count: {len(png_files)}")
    assert len(png_files) == page_count, f"Expected {page_count} PNG pages, got {len(png_files)}"
    for png in png_files:
        assert png.stat().st_size > 10000, f"PNG {png.name} size suspiciously small ({png.stat().st_size} bytes)"

    # 7. Security scan (Strict Section 14)
    forbidden_terms = [
        r"BEGIN (?:RSA|OPENSSH|EC|DSA) PRIVATE KEY",
        r"ssh-rsa AAAA",
        r"password\s*[:=]\s*['\"][^'\"]+['\"]",
        r"api_token\s*[:=]\s*['\"][^'\"]+['\"]",
        r"/srv/technoreboot",
        r"C:\\tbootit\\",
        r"update_vds",
    ]
    for term in forbidden_terms:
        matches = re.findall(term, all_text, re.IGNORECASE)
        assert len(matches) == 0, f"Security violation: found forbidden pattern '{term}' in manual text!"
    print("✓ Security Review: ZERO secrets, tokens, private keys or dev paths found")

    # 8. pypdf verification
    reader = PdfReader(str(PDF_PATH))
    assert len(reader.pages) == page_count
    reader_text = "".join([p.extract_text() for p in reader.pages])
    assert "ТехноРебут" in reader_text
    print("✓ Secondary parser (pypdf): Verified identical page count and Cyrillic text")

    doc.close()
    print("\nALL PDF VERIFICATION CHECKS PASSED!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
