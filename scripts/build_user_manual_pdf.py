import os
import re
import base64
import json
import subprocess
from pathlib import Path
from markdown_it import MarkdownIt
from playwright.sync_api import sync_playwright
import pymupdf

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_MD = REPO_ROOT / "docs" / "user_manual" / "TECHNOREBOOT_USER_MANUAL_RU.md"
ASSETS_DIR = REPO_ROOT / "docs" / "user_manual" / "assets"
TARGET_PDF = REPO_ROOT / "admin-shell" / "app" / "static" / "docs" / "TECHNOREBOOT_USER_MANUAL_RU.pdf"
LOCAL_COPY_PDF = REPO_ROOT / "docs" / "user_manual" / "TECHNOREBOOT_USER_MANUAL_RU.pdf"
RENDERED_PAGES_DIR = REPO_ROOT / "docs" / "user_manual" / "rendered_pages"

CHAPTER_TITLES = [
    (1, "Что такое ТехноРебут"),
    (2, "Быстрый старт"),
    (3, "Навигация по системе и роли пользователей"),
    (4, "Товары и складской учёт"),
    (5, "Добавление и редактирование товара вручную"),
    (6, "Штрихкоды и печать ценников 58×40"),
    (7, "Расширение для браузера «Техноребут Avito»"),
    (8, "Импорт товаров с Avito в ТехноРебут"),
    (9, "Оформление продаж и корзина"),
    (10, "Товарный чек"),
    (11, "Отмена продажи и возврат товаров в остатки"),
    (12, "Снятие объявления с Avito после продажи (ручной режим)"),
    (13, "Модуль ремонтов: приём, диагностика и выдача"),
    (14, "Отчёты по продажам и выручке"),
    (15, "Функции владельца (резервные копии, сертификаты, операции)"),
    (16, "Частые вопросы, ошибки и их решение"),
    (17, "Краткая памятка оператора на каждый день"),
]

def get_git_sha():
    try:
        res = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=str(REPO_ROOT), capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return "57d8bd2"

def get_extension_version():
    manifest_path = REPO_ROOT / "chrome-extension" / "technoreboot-avito" / "manifest.json"
    if manifest_path.exists():
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                return json.load(f).get("version", "0.2.62")
        except Exception:
            pass
    return "0.2.62"

def embed_images_as_base64(html: str) -> str:
    def repl(match):
        rel_path = match.group(1)
        clean_name = os.path.basename(rel_path)
        img_file = ASSETS_DIR / clean_name
        if img_file.exists():
            mime = "image/png" if clean_name.lower().endswith(".png") else "image/jpeg"
            b64 = base64.b64encode(img_file.read_bytes()).decode("utf-8")
            return f'src="data:{mime};base64,{b64}"'
        return match.group(0)
    
    return re.sub(r'src=["\']([^"\']+)["\']', repl, html)

def process_callouts(html: str) -> str:
    lines = html.splitlines()
    out = []
    in_bq = False
    bq_lines = []

    def format_bq(lines_list):
        text = "\n".join(lines_list)
        if "⚠️" in text or "Внимание" in text:
            return f'<div class="callout callout-warning">{text}</div>'
        elif "💡" in text or "Совет" in text:
            return f'<div class="callout callout-tip">{text}</div>'
        elif "🔒" in text or "Безопасность" in text:
            return f'<div class="callout callout-info">{text}</div>'
        else:
            return f'<div class="callout callout-default">{text}</div>'

    for line in lines:
        if line.startswith("<blockquote>"):
            in_bq = True
            bq_lines = [line.replace("<blockquote>", "")]
            if "</blockquote>" in line:
                in_bq = False
                out.append(format_bq([line.replace("<blockquote>", "").replace("</blockquote>", "")]))
        elif in_bq:
            if "</blockquote>" in line:
                in_bq = False
                bq_lines.append(line.replace("</blockquote>", ""))
                out.append(format_bq(bq_lines))
            else:
                bq_lines.append(line)
        else:
            out.append(line)
    return "\n".join(out)

def build_html(toc_page_map=None):
    md_text = SOURCE_MD.read_text(encoding="utf-8")
    
    # Remove the markdown TOC block from the body since we render a custom styled TOC container
    # From ## СОДЕРЖАНИЕ to the first ---
    toc_pattern = r'## СОДЕРЖАНИЕ\s*\n.*?\n---'
    body_md = re.sub(toc_pattern, '', md_text, flags=re.DOTALL)
    # Remove title block from body since we have cover page
    body_md = re.sub(r'^# ТЕХНОРЕБУТ.*?---', '', body_md, flags=re.DOTALL)

    md = MarkdownIt("commonmark").enable("table")
    raw_html = md.render(body_md)
    
    html_with_imgs = embed_images_as_base64(raw_html)
    html_processed = process_callouts(html_with_imgs)

    # Format chapter headers with anchors and IDs
    for num, title in CHAPTER_TITLES:
        pattern = rf'<h2>{num}\.\s+([^<]+)</h2>'
        repl = rf'<h2 id="ch{num}" class="chapter-heading"><span class="chapter-number">{num}.</span> \1</h2>'
        html_processed = re.sub(pattern, repl, html_processed)

    # Build TOC HTML
    toc_items_html = []
    for num, title in CHAPTER_TITLES:
        pno = toc_page_map.get(num, num + 2) if toc_page_map else ""
        pno_str = f'<span class="toc-page">{pno}</span>' if pno else ''
        item = f'''
        <div class="toc-item">
            <a href="#ch{num}" class="toc-link">
                <span class="toc-num">{num}.</span>
                <span class="toc-title">{title}</span>
            </a>
            <span class="toc-dots"></span>
            {pno_str}
        </div>
        '''
        toc_items_html.append(item)
    
    toc_block = f'''
    <div class="toc-page-container" id="toc">
        <div class="toc-header">
            <h2>СОДЕРЖАНИЕ</h2>
            <div class="toc-subtitle">Кликните по любому разделу для быстрого перехода внутри документа</div>
        </div>
        <div class="toc-grid">
            {"".join(toc_items_html)}
        </div>
    </div>
    '''

    css = """
    @page {
        size: A4;
        margin: 20mm 16mm 22mm 16mm;
    }
    
    * {
        box-sizing: border-box;
    }
    
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        color: #1e293b;
        line-height: 1.5;
        font-size: 10.5pt;
        background: #ffffff;
        margin: 0;
        padding: 0;
    }

    .cover-page {
        page-break-after: always;
        height: 100vh;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        padding: 30mm 16mm 20mm 16mm;
        border: 2px solid #2563eb;
        border-radius: 8px;
        background: linear-gradient(135deg, #f8fafc 0%, #eff6ff 100%);
    }

    .cover-header {
        border-bottom: 3px solid #2563eb;
        padding-bottom: 20px;
    }

    .cover-brand {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        font-size: 24pt;
        font-weight: 900;
        color: #0f172a;
        letter-spacing: -0.5px;
    }

    .cover-badge {
        background: #2563eb;
        color: #ffffff;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 16pt;
        font-weight: 800;
    }

    .cover-title {
        font-size: 27pt;
        font-weight: 800;
        color: #0f172a;
        margin: 35px 0 15px 0;
        line-height: 1.2;
    }

    .cover-subtitle {
        font-size: 13pt;
        color: #475569;
        margin: 0 0 35px 0;
        line-height: 1.4;
    }

    .cover-meta {
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 18px 22px;
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 14px;
        font-size: 10pt;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }

    .cover-meta-item strong {
        color: #0f172a;
        display: block;
        font-size: 8.5pt;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 3px;
    }

    .cover-footer {
        font-size: 9pt;
        color: #64748b;
        text-align: center;
        border-top: 1px solid #e2e8f0;
        padding-top: 15px;
    }

    .toc-page-container {
        page-break-after: always;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 24px 26px;
        margin: 10px 0 25px 0;
    }

    .toc-header {
        border-bottom: 2px solid #2563eb;
        padding-bottom: 10px;
        margin-bottom: 16px;
    }

    .toc-header h2 {
        margin: 0;
        color: #0f172a;
        font-size: 17pt;
        font-weight: 800;
    }

    .toc-subtitle {
        color: #64748b;
        font-size: 9pt;
        margin-top: 4px;
    }

    .toc-grid {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }

    .toc-item {
        display: flex;
        align-items: baseline;
        font-size: 10pt;
        padding: 2px 0;
    }

    .toc-link {
        color: #1e3a8a;
        text-decoration: none;
        font-weight: 600;
        display: inline-flex;
        gap: 6px;
        white-space: nowrap;
    }

    .toc-link:hover {
        text-decoration: underline;
        color: #2563eb;
    }

    .toc-num {
        color: #2563eb;
        min-width: 22px;
    }

    .toc-dots {
        flex: 1;
        border-bottom: 1.5px dotted #cbd5e1;
        margin: 0 8px;
        min-width: 20px;
        position: relative;
        top: -4px;
    }

    .toc-page {
        font-weight: 700;
        color: #0f172a;
        font-size: 9.5pt;
        min-width: 20px;
        text-align: right;
    }

    h1, h2, h3, h4 {
        color: #0f172a;
        font-weight: 700;
        page-break-after: avoid;
        break-after: avoid;
    }

    h2.chapter-heading {
        font-size: 14pt;
        border-bottom: 1.5px solid #cbd5e1;
        padding-bottom: 6px;
        margin-top: 28px;
        margin-bottom: 12px;
        color: #1e3a8a;
        page-break-before: auto;
    }

    h3 {
        font-size: 11.5pt;
        margin-top: 18px;
        margin-bottom: 8px;
        color: #1e293b;
    }

    p {
        margin: 7px 0;
        text-align: justify;
    }

    ul, ol {
        margin: 6px 0 10px 0;
        padding-left: 22px;
        text-align: left;
    }

    li {
        margin: 3px 0;
        text-align: left;
    }

    table {
        width: 100%;
        border-collapse: collapse;
        margin: 12px 0;
        font-size: 9pt;
        page-break-inside: avoid;
        break-inside: avoid;
    }

    th, td {
        border: 1px solid #cbd5e1;
        padding: 6px 9px;
        text-align: left;
        vertical-align: top;
    }

    th {
        background-color: #f1f5f9;
        color: #0f172a;
        font-weight: 700;
        font-size: 8.5pt;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }

    tr:nth-child(even) td {
        background-color: #f8fafc;
    }

    img {
        max-width: 100%;
        height: auto;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        display: block;
        margin: 10px auto 4px auto;
        box-shadow: 0 2px 4px rgba(0,0,0,0.06);
        page-break-inside: avoid;
        break-inside: avoid;
    }

    em {
        display: block;
        text-align: center;
        font-size: 8.5pt;
        color: #64748b;
        margin-bottom: 14px;
        page-break-before: avoid;
        break-before: avoid;
    }

    .callout {
        border-radius: 6px;
        padding: 10px 14px;
        margin: 12px 0;
        font-size: 9pt;
        page-break-inside: avoid;
        break-inside: avoid;
    }

    .callout-warning {
        background: #fffbeb;
        border: 1px solid #fde68a;
        border-left: 4px solid #d97706;
        color: #92400e;
    }

    .callout-tip {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-left: 4px solid #16a34a;
        color: #166534;
    }

    .callout-info {
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        border-left: 4px solid #2563eb;
        color: #1e40af;
    }

    .callout-default {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #64748b;
        color: #334155;
    }

    pre {
        background: #0f172a;
        color: #f8fafc;
        padding: 10px 14px;
        border-radius: 6px;
        font-size: 8pt;
        line-height: 1.35;
        overflow-x: auto;
        white-space: pre-wrap;
        word-break: break-all;
        page-break-inside: avoid;
        break-inside: avoid;
        font-family: Consolas, "Courier New", monospace;
    }

    code {
        background: #f1f5f9;
        color: #0f172a;
        padding: 2px 4px;
        border-radius: 3px;
        font-size: 8.5pt;
        font-family: Consolas, "Courier New", monospace;
    }

    a {
        color: #2563eb;
        text-decoration: none;
    }

    a:hover {
        text-decoration: underline;
    }

    .chapter-number {
        color: #2563eb;
        margin-right: 4px;
    }
    """

    full_html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>ТехноРебут — Руководство пользователя</title>
    <style>{css}</style>
</head>
<body>
    <!-- Обложка -->
    <div class="cover-page">
        <div class="cover-header">
            <div class="cover-brand">
                <span class="cover-badge">TR</span>
                ТЕХНОРЕБУТ
            </div>
        </div>
        
        <div>
            <div class="cover-title">Руководство пользователя</div>
            <div class="cover-subtitle">
                Полная иллюстрированная инструкция по работе с системой учёта товаров, розничными продажами, кассовыми чеками, приёмом в ремонт и интеграцией с Avito
            </div>
            
            <div class="cover-meta">
                <div class="cover-meta-item">
                    <strong>Версия руководства</strong>
                    1.0 (LOCAL Edition)
                </div>
                <div class="cover-meta-item">
                    <strong>Дата публикации</strong>
                    14 сентября 2026 г.
                </div>
                <div class="cover-meta-item">
                    <strong>Версия системы (Git SHA)</strong>
                    {get_git_sha()}
                </div>
                <div class="cover-meta-item">
                    <strong>Версия расширения Avito</strong>
                    {get_extension_version()}
                </div>
                <div class="cover-meta-item" style="grid-column: 1 / -1;">
                    <strong>Локальный адрес системы</strong>
                    https://localhost:8443
                </div>
            </div>
        </div>
        
        <div class="cover-footer">
            ТехноРебут — система автоматизации компьютерного магазина и сервисного центра &copy; 2026
        </div>
    </div>

    <!-- Содержание -->
    {toc_block}

    <!-- Основной текст руководства -->
    <div class="content-container">
        {html_processed}
    </div>
</body>
</html>
"""
    return full_html

def render_with_playwright(html_path: Path, output_pdf: Path, git_sha: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"file:///{str(html_path).replace(chr(92), '/')}", wait_until="networkidle")
        
        footer_tpl = f"""
        <div style="font-size: 8pt; color: #64748b; width: 100%; display: flex; justify-content: space-between; padding: 0 16mm; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
            <span>ТехноРебут — Руководство пользователя | git {git_sha}</span>
            <span>Стр. <span class="pageNumber"></span> из <span class="totalPages"></span></span>
        </div>
        """
        
        page.pdf(
            path=str(output_pdf),
            format="A4",
            print_background=True,
            display_header_footer=True,
            header_template="<div></div>",
            footer_template=footer_tpl,
            margin={
                "top": "18mm",
                "bottom": "20mm",
                "left": "16mm",
                "right": "16mm"
            }
        )
        browser.close()

def discover_chapter_pages(pdf_path: Path):
    doc = pymupdf.open(str(pdf_path))
    page_map = {}
    for num, title in CHAPTER_TITLES:
        prefix = f"{num}. "
        found_pno = None
        for pno in range(len(doc)):
            text = doc[pno].get_text()
            if prefix in text and (title[:12] in text):
                found_pno = pno + 1
                break
        page_map[num] = found_pno if found_pno else (num + 2)
    doc.close()
    return page_map

def generate_pdf():
    git_sha = get_git_sha()
    temp_html_path = REPO_ROOT / "docs" / "user_manual" / "_temp_manual.html"
    TARGET_PDF.parent.mkdir(parents=True, exist_ok=True)
    LOCAL_COPY_PDF.parent.mkdir(parents=True, exist_ok=True)
    RENDERED_PAGES_DIR.mkdir(parents=True, exist_ok=True)

    # PASS 1: Generate initial PDF to discover exact page layout
    html_pass1 = build_html()
    temp_html_path.write_text(html_pass1, encoding="utf-8")
    render_with_playwright(temp_html_path, TARGET_PDF, git_sha)

    # Discover exact chapter page locations
    page_map = discover_chapter_pages(TARGET_PDF)
    print("Discovered chapter pages:", page_map)

    # PASS 2: Re-render with exact page numbers printed in the TOC
    html_pass2 = build_html(toc_page_map=page_map)
    temp_html_path.write_text(html_pass2, encoding="utf-8")
    render_with_playwright(temp_html_path, TARGET_PDF, git_sha)

    if temp_html_path.exists():
        temp_html_path.unlink()

    # Enhance with PyMuPDF bookmarks
    doc = pymupdf.open(str(TARGET_PDF))
    page_count = len(doc)

    toc_entries = [[1, "Обложка", 1], [1, "Содержание", 2]]
    for num, title in CHAPTER_TITLES:
        pno = page_map.get(num, 3)
        toc_entries.append([1, f"{num}. {title}", pno])

    doc.set_toc(toc_entries)
    doc.saveIncr()

    # Re-render PNG pages for inspection
    print(f"Rendering all {page_count} pages to PNG in {RENDERED_PAGES_DIR}...")
    for old_png in RENDERED_PAGES_DIR.glob("page_*.png"):
        try:
            old_png.unlink()
        except Exception:
            pass

    for pno in range(page_count):
        pix = doc[pno].get_pixmap(dpi=150)
        out_png = RENDERED_PAGES_DIR / f"page_{pno+1:02d}.png"
        pix.save(str(out_png))

    # Also save local copy
    doc.save(str(LOCAL_COPY_PDF))
    doc.close()

    pdf_size = TARGET_PDF.stat().st_size
    print(f"User manual PDF generated successfully!")
    print(f"  Target: {TARGET_PDF}")
    print(f"  Pages: {page_count}")
    print(f"  Size: {pdf_size:,} bytes")
    print(f"  TOC Bookmarks: {len(toc_entries)}")

    return {
        "target_pdf": str(TARGET_PDF),
        "pages": page_count,
        "size_bytes": pdf_size,
        "toc_count": len(toc_entries),
        "page_map": page_map
    }

if __name__ == "__main__":
    res = generate_pdf()
    print("Result:", res)
