# Stage 10A LOCAL — User Manual PDF + Admin Download

## Analysis
USER_FACING_FUNCTIONS_INVENTORIED: true
PRODUCTS_DOCUMENTED: true
AVITO_DOCUMENTED: true
SALES_DOCUMENTED: true
REPAIRS_DOCUMENTED: true
REPORTS_DOCUMENTED: true
OWNER_FUNCTIONS_DOCUMENTED: true

## Manual
SOURCE_FILE: docs/user_manual/TECHNOREBOOT_USER_MANUAL_RU.md
PDF_FILE: admin-shell/app/static/docs/TECHNOREBOOT_USER_MANUAL_RU.pdf
PDF_PAGE_COUNT: 25
PDF_SIZE_BYTES: 2470296
SCREENSHOT_COUNT: 15
LANGUAGE: ru
CLICKABLE_TOC: true
CLICKABLE_TOC_VERIFIED: true
PDF_BOOKMARKS: true
CYRILLIC_OK: true
NO_CLIPPED_LAYOUT: true
SEARCHABLE_TEXT: true
MANUAL_VERSION: 1.0 (2026-09-14)
SYSTEM_GIT_SHA: 57d8bd283454fed176b77f2a2d3d4b57ea8b55de
AVITO_EXTENSION_VERSION: 0.2.62

## Chapters
CHAPTER_LIST:
1. Введение и назначение системы
2. Быстрый старт: вход в систему и навигация
3. Управление товарами (Инвентарь)
4. Расширение Avito: установка и подключение (v0.2.62)
5. Импорт товаров из Avito в один клик
6. Оформление продаж и работа с кассой
7. Чеки: термопечать и формат A4
8. Снятие товаров с Avito после продажи (ручной режим)
9. Модуль «Ремонты»: приём устройств и диагностика
10. Модуль «Ремонты»: согласование, запчасти и выдача
11. Аналитика и отчёты
12. Функции владельца: резервные копии и безопасность
13. Сертификаты доступа и сотрудники
14. Частые вопросы и решение проблем (FAQ)
15. Правила безопасности при работе с системой
16. Справочник терминов и статусов
17. Контакты и техническая поддержка

## Download Integration
MANUAL_ROUTE: /help/user-manual.pdf
CONTENT_TYPE: application/pdf
CONTENT_DISPOSITION: attachment; filename="TECHNOREBOOT_USER_MANUAL_RU.pdf"
TOP_NAV_LINK_PRESENT: true
USER_CAN_DOWNLOAD: true
OWNER_CAN_DOWNLOAD: true

## Security
SECRETS_FOUND_IN_MANUAL: false
INTERNAL_ADMIN_COMMANDS_EXPOSED: false

## Tests
FAILED: 0

## VDS Safety
VDS_DEPLOYED: false
VDS_CODE_MODIFIED: false
VDS_DATA_MODIFIED: false
UPDATE_VDS_RUN: false

## Git
COMMIT: 7410252bf986276ae3b631ba0e76a17c6b62414c
PUSH: false
HEAD_AFTER: 7410252bf986276ae3b631ba0e76a17c6b62414c
FINAL_GIT_STATUS: clean

FINAL_STATUS:
TECHNOREBOOT_STAGE10A_LOCAL_USER_MANUAL_READY_FOR_OWNER_ACCEPTANCE

DO_NOT_DEPLOY_TO_VDS_WITHOUT_OWNER_ACCEPTANCE: true

---

## Technical Implementation Details

### 1. Document Architecture & Content Coverage
The user manual was authored in pure Russian without developer jargon, specifically targeted at retail sales staff, service engineers, and workshop administrators.
- **Chapter 1-2: Introduction & Navigation**: Explains the client certificate security model (mTLS), browser certificate installation, unified top navigation, and role distinction (Продавец vs Владелец).
- **Chapter 3: Products / Inventory**: Comprehensive field explanation table for adding and editing products (Наименование, Категория, Цена продажи, Себестоимость, Остаток, Статус, Состояние, Описание), photo uploads, draft vs active modes, search and filtering.
- **Chapter 4-5: Avito Extension v0.2.62**: Clear installation instructions for Chrome/Яндекс.Браузер, unpacking ZIP, 6-digit pairing code generation in `/avito/extension`, one-click clipboard copying via `[ 📋 Скопировать ]`, instant pairing, and one-click import from live Avito listings directly into TechnoReboot inventory with automatic photo transfer.
- **Chapter 6-8: Sales, Receipts & Avito Post-Sale Deactivation**: Cart workflow, single and multi-item sales, discounts, payment methods (Наличные, Карта, Перевод), thermal 80mm receipts and A4 PDF printing. Full documentation of the Stage 09A-R5 manual Avito deactivation workflow: post-sale prompt, permanent `[ ↗ Снять с Avito вручную ]` button, honest non-mutating `[ Не снимать ]` option, and `[ ✓ Я снял объявление ]` confirmation.
- **Chapter 9-10: Repairs**: Full customer intake lifecycle: client information, device serial number, reported malfunction, preliminary cost estimation, diagnostic progress, status pipeline (*Принят*, *На диагностике*, *Согласование*, *В работе*, *Готов к выдаче*, *Выдан*, *Отказ*), replacement parts and labor accounting, warranty receipt printing.
- **Chapter 11: Analytics & Reports**: Revenue, profit, sales volume, repair profitability, date range filtering, export capabilities.
- **Chapter 12-13: Owner Operations & Certificates**: Safe backup creation and download, restore procedures with Direction Guard protection, employee certificate issuance and revocation.
- **Chapter 14-17: FAQ, Security & Terms**: Common operator issues (cert expired, extension offline, duplicate items), security fundamentals (never share certs, generic illustrative pairing code `123456`), terms glossary, and support contacts.

### 2. Live Screenshots Capture
15 authentic UI screenshots were captured locally via Playwright using local Owner client certificates (`data/auth/certificates/owner.crt`):
1. `01_dashboard.png`: Main dashboard overview
2. `02_products_list.png`: Products catalog and filters
3. `03_product_add.png`: New product creation form
4. `04_product_detail.png`: Product detail and photo gallery
5. `05_avito_extension.png`: Admin shell extension pairing page with one-click copy button
6. `06_avito_popup.png`: Extension popup interface (v0.2.62)
7. `07_cart.png`: Sales cart and checkout
8. `08_sales_new.png`: New sale creation
9. `09_sales_list.png`: Sales history and receipt links
10. `10_sales_detail.png`: Sale detail with manual Avito deactivation controls
11. `11_repair_new.png`: Repair intake form
12. `12_repair_detail.png`: Repair order detail with diagnostic statuses
13. `13_repairs_list.png`: Repairs registry
14. `14_reports_sales.png`: Sales and financial analytics
15. `15_owner_operations.png`: Backups and owner operations center

### 3. PDF Compilation Pipeline (`scripts/build_user_manual_pdf.py`)
- Two-pass Playwright Chromium PDF generator.
- Pass 1 renders with anchor tags (`#ch1`...`#ch17`) to discover real dynamic page breaks and chapter starting pages.
- Pass 2 injects exact discovered page numbers into dotted leader TOC lines (`.toc-dots` and `.toc-page`).
- Embedded base64 images ensure complete offline reproducibility with zero external dependencies.
- Header and footer templates dynamically render title, version, and `Стр. <pageNumber> из <totalPages>`.
- PyMuPDF injects a 19-node PDF outline/bookmark hierarchy with exact page targets.
- Produces 25 pages (2,470,296 bytes) at `admin-shell/app/static/docs/TECHNOREBOOT_USER_MANUAL_RU.pdf`.
- Rendered 25 page PNGs in `docs/user_manual/rendered_pages/` for visual verification.

### 4. Admin Shell & Navigation Integration
- Added routes in `admin-shell/app/main.py`:
  - `GET /help/user-manual.pdf`: Serves `application/pdf` with `Content-Disposition: attachment; filename="TECHNOREBOOT_USER_MANUAL_RU.pdf"`.
  - `GET /help`: Renders `admin-shell/app/templates/help.html` with download button and chapter table of contents.
- Added `📘 Инструкция` (`/help/user-manual.pdf`) to unified top navigation in:
  - `inventory-sales-module/app/templates/base.html`
  - `repairs-module/app/templates/base.html`
  - All 12 admin-shell templates (`index.html`, `products_json.html`, `backups.html`, `certificates.html`, `avito_extension.html`, `avito_post_sale.html`, `avito.html`, `avito_accounts.html`, `avito_browser.html`, `avito_probe.html`, `avito_profile_not_found.html`, `operations.html`).
- Updated `admin-shell/tests/test_unified_top_navigation_bar.py` (`EXPECTED_LINKS` includes `("/help/user-manual.pdf", "Инструкция")`).

### 5. Automated Verification & Security Scan
- Automated test suite `tests/test_stage10a_user_manual_pdf.py` (6 passed).
- Dedicated verifier `scripts/verify_user_manual_pdf.py` (all checks passed):
  - Valid `%PDF` header (2,470,296 bytes).
  - 25 pages, 17 clickable internal TOC jumps on Page 2, 19 PDF bookmarks.
  - Cyrillic text extraction across all 25 pages passes with zero garbled characters.
  - Rigorous security scan for SSH keys, passwords, dev paths (`/srv/technoreboot`, `C:\tbootit\`), tokens, or update commands found 0 occurrences.
  - Secondary parser (`pypdf`) confirmed identical page count and text extraction.
