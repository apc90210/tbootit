# TECHNOREBOOT — Stage 10A LOCAL
## Full Russian User Manual PDF + permanent download link in Admin Panel

**Project:** ТехноРебут  
**LOCAL workspace:** `C:\tbootit`  
**LOCAL URL:** `https://localhost:8443`  
**Production VDS:** `https://144.31.50.134`  
**Stage:** `Stage 10A LOCAL — User Manual PDF + Admin Download`

# 0. OWNER GOAL

Create a complete but very simple Russian-language User Manual for the current TechnoReboot system.

The manual must be understandable by a non-technical employee who has never used the system.

Core principle:

```text
Человек открывает инструкцию
→ находит нужную функцию в содержании
→ кликает по ней
→ видит простые пошаговые действия
→ понимает, что и в какое поле вводить
→ понимает, что должно произойти после сохранения
```

The manual must cover all current user-facing functions of the system, from the Avito Chrome Extension through products, stock, sales and repairs.

The final PDF must be downloadable directly from the TechnoReboot control panel at any time.

This stage is LOCAL ONLY.
Do NOT deploy to VDS in this stage.

---

# 1. PROMPT PRESERVATION

Copy unchanged from:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE10A_LOCAL_USER_MANUAL_PDF_AND_ADMIN_DOWNLOAD_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE10A_LOCAL_USER_MANUAL_PDF_AND_ADMIN_DOWNLOAD_PROMPT.md`

---

# 2. PREFLIGHT

Before writing the manual, inspect the actual current application.

Required:

```text
git status
git rev-parse HEAD
docker compose ps
```

Inspect at minimum:

```text
AGENTS.md
docs/production_status.md
README / project docs
admin-shell routes/templates
inventory-sales-module routes/templates
repairs-module routes/templates
avito-module routes/templates
core API models/routes relevant to UI
Chrome extension manifest/popup/service worker/content script
current tests that describe accepted UI behavior
```

Do not write the manual from old assumptions.

The source of truth is the CURRENT working code/UI.

---

# 3. FUNCTION INVENTORY — MANDATORY

Before authoring, create an internal inventory of all user-facing functions and routes.

At minimum inspect and document current behavior for:

## A. General UI
- how to open TechnoReboot;
- main navigation;
- USER vs OWNER visible differences;
- common buttons;
- search;
- status messages;
- where to return/back.

## B. Products / Inventory
- product list;
- search and filters;
- open product card;
- add product manually;
- required and optional fields;
- category;
- title;
- description;
- price;
- purchase/cost price if exposed;
- quantity / stock;
- status;
- location/store if exposed;
- SKU/article;
- barcode;
- photos;
- edit product;
- stock changes;
- draft / in-stock / sold semantics if current UI exposes them;
- barcode scanning;
- barcode generation;
- price label 58x40 if present;
- printing labels if present.

## C. Avito Chrome Extension
- how to download the extension from TechnoReboot;
- how to install/reload unpacked extension;
- pairing with 6-digit code;
- copy-code button;
- server URL field;
- how to verify "connected";
- import single Avito listing;
- import from profile/list if current extension supports it;
- what fields/photos are imported now;
- current accepted limitations;
- what to do if import does not start;
- how to re-pair;
- current extension version handling.

IMPORTANT:
Current accepted post-sale Avito removal flow is MANUAL:
- TechnoReboot opens the exact linked Avito listing;
- operator manually removes it on Avito;
- optional "Я снял объявление" confirms locally.
Do NOT describe automatic DOM deactivation as working.

## D. Sales
- create a sale;
- find/add product;
- barcode/scanner workflow;
- cart;
- quantity behavior;
- price adjustment/discount if supported;
- payment method;
- completion;
- what happens to stock;
- receipt / товарный чек;
- expanded receipt if present;
- print/download;
- sale detail;
- cancel sale;
- reason for cancellation if required;
- stock return after cancellation;
- returns/exchanges if present;
- sale statuses;
- reports / Today / Week / Year if current UI exposes them;
- Avito post-sale prompt:
  - "Снять с Avito вручную";
  - "Не снимать";
  - "Я снял объявление";
  - permanent button in an old sale.

## E. Repairs
Inspect the actual repairs module and document every visible normal workflow:
- create repair/intake;
- customer fields;
- phone/contact if present;
- device/equipment;
- brand/model/serial if present;
- appearance/completeness/accessories if present;
- reported fault/problem;
- diagnostics;
- work/service;
- parts/materials;
- prices/cost;
- repair status transitions;
- comments;
- technician if exposed;
- issue/close repair;
- print/receipt/act if present;
- search/filter/history.

Do not invent fields that are not in the current UI.

## F. Reports
Document every report/filter actually available:
- Today;
- Week;
- Year;
- date filters;
- revenue;
- payment methods;
- canceled sales behavior;
- any other current report view.

## G. Owner/Admin functions
Inspect current owner-visible UI and include a separate chapter only for visible supported operations:
- backups;
- Owner Operations;
- VDS -> LOCAL sync;
- UPDATE;
- rollback;
- certificates if user-facing;
- any other current owner-only panel.

These sections must contain clear WARNING callouts.

Do NOT expose:
- passwords;
- tokens;
- SSH commands;
- secret file paths;
- private keys;
- internal production IP details unless the UI literally requires them for an end user.

This is a USER MANUAL, not a developer runbook.

---

# 4. MANUAL STRUCTURE

Create the manual in Russian.

Recommended structure:

```text
ТехноРебут
Руководство пользователя

1. Что такое ТехноРебут
2. Быстрый старт
3. Навигация по системе
4. Товары и склад
5. Добавление товара вручную
6. Работа со штрихкодами и ценниками
7. Расширение Avito
8. Импорт товаров с Avito
9. Продажи
10. Товарный чек
11. Отмена продажи / возврат в остатки
12. Снятие объявления Avito после продажи вручную
13. Ремонты
14. Отчёты
15. Функции владельца
16. Частые проблемы и что делать
17. Краткая памятка оператору
```

Adjust chapter names based on the real current UI.

---

# 5. CLICKABLE TABLE OF CONTENTS — MANDATORY

The PDF must have a real clickable table of contents.

Example:

```text
СОДЕРЖАНИЕ

1. Быстрый старт .................................... 3
2. Товары и склад ................................... 5
3. Добавление товара ................................ 8
4. Расширение Avito ................................ 14
5. Продажа ......................................... 23
6. Ремонты ......................................... 31
...
```

Requirements:

```text
CLICKABLE_TOC: true
PDF_BOOKMARKS: true
```

Clicking a TOC entry must jump to that chapter inside the PDF.

Also add PDF bookmarks/outlines if the chosen PDF library supports them.

Prefer a small:

```text
↑ К содержанию
```

link at the end or beginning of major chapters if practical.

---

# 6. WRITING STYLE

This manual is for a user with low technical confidence.

Rules:

- very simple Russian;
- short sentences;
- one action per step;
- do not use developer terminology unless unavoidable;
- explain every field in plain words;
- show examples;
- explain what is mandatory;
- explain what can be left blank;
- explain what happens after clicking Save/Complete;
- clearly distinguish normal result vs error;
- use numbered steps for procedures.

Bad:

```text
Создайте сущность Product с canonical identity.
```

Good:

```text
1. Нажмите «Добавить товар».
2. В поле «Название» напишите, что это за товар.
   Пример: HP LaserJet Pro M404dn.
3. Укажите цену продажи.
4. Добавьте фотографию.
5. Нажмите «Сохранить».
```

---

# 7. EVERY FUNCTION CHAPTER MUST CONTAIN

For each major function include:

```text
Что делает эта функция
Где её найти
Что нужно заполнить
Пошагово
Что произойдёт после сохранения
Как понять, что всё получилось
Частые ошибки
Что делать, если ошибся
```

For forms, use tables like:

| Поле | Что писать | Обязательно | Пример |
| --- | --- | --- | --- |
| Название | Понятное название товара | Да | HP LaserJet Pro M404dn |
| Цена | Цена продажи | Да | 12 500 ₽ |

Only document fields actually present.

---

# 8. SCREENSHOTS

Add current LOCAL UI screenshots for the most important workflows where practical.

Target approximately 8-15 useful screenshots, for example:

- main menu/dashboard;
- products list;
- add product form;
- product card;
- Avito extension download/pairing page;
- extension popup;
- sale/cart page;
- sale completed / manual Avito prompt;
- sale detail;
- repairs list;
- repair form;
- reports;
- Owner Operations page.

Requirements:
- use CURRENT UI;
- crop screenshots to useful areas;
- do not expose passwords/tokens/private keys;
- avoid personal customer information;
- blur/crop sensitive data if present;
- use captions.

Do not add screenshots merely for decoration.

If a useful screenshot cannot be captured safely, use text instructions instead.

---

# 9. PDF DESIGN

The manual should look clean and practical, not like a developer document.

Required:

- A4;
- readable Cyrillic font;
- title page;
- version/date;
- clickable TOC;
- page numbers;
- consistent H1/H2/H3 hierarchy;
- screenshots with captions;
- warning/info callouts;
- searchable/selectable text;
- no broken Cyrillic;
- no clipped text;
- no black squares;
- no overflow outside page.

Suggested footer:

```text
ТехноРебут — Руководство пользователя | версия <date/commit> | стр. N
```

Do NOT commit font files.

---

# 10. SOURCE + GENERATED FILES

Keep the manual maintainable.

Create source files, preferably:

```text
docs/user_manual/TECHNOREBOOT_USER_MANUAL_RU.md
docs/user_manual/assets/
```

Create generated PDF:

```text
admin-shell/app/static/docs/TECHNOREBOOT_USER_MANUAL_RU.pdf
```

If the current admin-shell static path differs, use the correct existing static architecture.

Also create a build script, for example:

```text
scripts/build_user_manual_pdf.py
```

or another reproducible build command.

The PDF must be rebuildable later when UI changes.

Preferred authoring pipeline:
- Markdown/HTML or DOCX source;
- render to PDF with a tool available in the environment;
- preserve internal links/bookmarks.

Choose the tool that actually works in the current environment.

Do not claim TOC links work without verifying them.

---

# 11. PDF VERIFICATION — MANDATORY

After creating PDF:

1. verify PDF opens;
2. verify page count;
3. verify text extraction works;
4. verify Cyrillic text;
5. verify clickable links/annotations exist;
6. verify TOC internal jumps;
7. verify bookmarks/outlines if generated;
8. render all pages to PNG;
9. inspect representative pages including:
   - title;
   - TOC;
   - product form chapter;
   - Avito chapter;
   - sales chapter;
   - repairs chapter;
   - final page.

Required:

```text
PDF_VALID: true
CLICKABLE_TOC_VERIFIED: true
CYRILLIC_OK: true
NO_CLIPPED_LAYOUT: true
```

If PDF utilities are available, use them.

---

# 12. DOWNLOAD FROM ADMIN PANEL

Add a permanent visible download action in the unified TechnoReboot UI.

Preferred label:

```text
📘 Инструкция
```

or:

```text
📘 Руководство пользователя
```

Requirements:
- visible to normal authenticated USER and OWNER;
- present in the unified top navigation or another permanent common navigation area;
- works from all main modules;
- one click downloads the PDF;
- do not require OWNER role;
- do not expose it publicly outside normal TechnoReboot access.

Create a stable route, for example:

```text
GET /help/user-manual.pdf
```

Response:

```text
Content-Type: application/pdf
Content-Disposition: attachment; filename="TECHNOREBOOT_USER_MANUAL_RU.pdf"
```

Use the actual application architecture.

Optionally create:

```text
/help
```

with:
- current manual version;
- button "Скачать PDF".

But the permanent nav download link is still required.

---

# 13. MANUAL VERSIONING

Show in the manual:

```text
Версия руководства:
Дата:
Версия системы / Git short SHA:
Версия расширения Avito:
```

Do not expose sensitive infrastructure.

Current Avito extension version must be discovered from `manifest.json`, not hardcoded from this prompt.

---

# 14. SECURITY REVIEW

Before finalizing, grep/extract PDF text and ensure the manual does NOT contain:

```text
SSH private key
password
API token
extension token
pairing token
private certificate key
C:\tbootit internal development instructions
/srv/technoreboot internal server administration instructions
developer-only commands
```

A 6-digit pairing code may appear only in a generic illustrative form such as:

```text
123456
```

never a real active code.

---

# 15. TESTS

Add tests for the downloadable manual.

At minimum:

## PDF artifact

```text
PDF exists
PDF begins with %PDF
PDF size is non-trivial
PDF page count > 1
PDF text includes "Руководство пользователя"
PDF text includes major chapters:
- Товары
- Avito
- Продажи
- Ремонты
```

## Download route

```text
GET manual route -> 200 for USER
GET manual route -> 200 for OWNER
Content-Type == application/pdf
Content-Disposition contains attachment
response bytes match generated PDF
```

## UI

```text
unified navigation contains "Инструкция" / "Руководство пользователя"
link points to manual route
available in USER role
available in OWNER role
```

## PDF navigation

Where feasible automatically verify:
- internal PDF link annotations exist;
- bookmarks/outlines exist.

Run the relevant targeted regression suites.

Required:

```text
FAILED = 0
```

---

# 16. OWNER LOCAL ACCEPTANCE

After implementation, Owner should be able to do only this:

1. Open:
   ```text
   https://localhost:8443
   ```
2. Click:
   ```text
   📘 Инструкция
   ```
3. PDF downloads.
4. Open PDF.
5. Click several TOC entries:
   - Добавление товара;
   - Avito;
   - Продажа;
   - Ремонты.
6. Confirm navigation jumps to correct chapters.
7. Compare instructions against real UI.

Do not require command line for Owner acceptance.

---

# 17. VDS SAFETY

Strictly LOCAL:

```text
VDS_DEPLOYED = false
VDS_CODE_MODIFIED = false
VDS_DATA_MODIFIED = false
UPDATE_VDS_RUN = false
```

Do not deploy this manual/UI link to production in this stage.

A separate production deployment will happen only after Owner accepts the LOCAL manual.

---

# 18. DOCUMENTATION

Create:

```text
reports/stage10a_local_user_manual_pdf_report.md
```

Update:

```text
docs/production_status.md
logs/<current-date>.md
```

Document:
- manual chapters;
- PDF page count;
- build pipeline;
- clickable TOC verification;
- screenshots count;
- route;
- tests.

---

# 19. GIT

Commit LOCAL changes.

Do not deploy VDS.

Report:

```text
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:
```

---

# 20. FINAL REPORT CONTRACT

Return:

```text
# Stage 10A LOCAL — User Manual PDF + Admin Download

## Analysis
USER_FACING_FUNCTIONS_INVENTORIED:
PRODUCTS_DOCUMENTED:
AVITO_DOCUMENTED:
SALES_DOCUMENTED:
REPAIRS_DOCUMENTED:
REPORTS_DOCUMENTED:
OWNER_FUNCTIONS_DOCUMENTED:

## Manual
SOURCE_FILE:
PDF_FILE:
PDF_PAGE_COUNT:
PDF_SIZE_BYTES:
SCREENSHOT_COUNT:
LANGUAGE: ru
CLICKABLE_TOC:
CLICKABLE_TOC_VERIFIED:
PDF_BOOKMARKS:
CYRILLIC_OK:
NO_CLIPPED_LAYOUT:
SEARCHABLE_TEXT:
MANUAL_VERSION:
SYSTEM_GIT_SHA:
AVITO_EXTENSION_VERSION:

## Chapters
CHAPTER_LIST:

## Download Integration
MANUAL_ROUTE:
CONTENT_TYPE:
CONTENT_DISPOSITION:
TOP_NAV_LINK_PRESENT:
USER_CAN_DOWNLOAD:
OWNER_CAN_DOWNLOAD:

## Security
SECRETS_FOUND_IN_MANUAL: false
INTERNAL_ADMIN_COMMANDS_EXPOSED: false

## Tests
FAILED:

## VDS Safety
VDS_DEPLOYED: false
VDS_CODE_MODIFIED: false
VDS_DATA_MODIFIED: false
UPDATE_VDS_RUN: false

## Git
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:

FINAL_STATUS:
TECHNOREBOOT_STAGE10A_LOCAL_USER_MANUAL_READY_FOR_OWNER_ACCEPTANCE

DO_NOT_DEPLOY_TO_VDS_WITHOUT_OWNER_ACCEPTANCE: true
```

Return BLOCKED if:
- manual is incomplete for major current modules;
- TOC is not clickable;
- PDF has broken Cyrillic/layout;
- manual contains secrets;
- download link is not available to USER;
- tests fail.

---

# 21. STOP

After LOCAL PDF generation + download integration:

STOP.

Wait for Owner browser acceptance.

Do not deploy to VDS.
