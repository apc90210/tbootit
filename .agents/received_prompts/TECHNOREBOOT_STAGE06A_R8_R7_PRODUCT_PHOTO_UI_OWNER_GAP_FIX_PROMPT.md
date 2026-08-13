# TECHNOREBOOT — Stage06A-R8-R7 Product Photo UI Owner Gap Audit & Fix

Репозиторий:

```powershell
C:\tbootit
```

Это corrective stage внутри Stage06A-R8.

НЕ начинать:
- Stage06A-R9
- Stage06B
- любой следующий функциональный этап

Предыдущий статус:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE06A_R8_R6_PHOTO_IMPORT_READY_FOR_OWNER_CHECK
```

R8-R6 заявил:

```text
Product ID 58
Avito ID 8313765236
extension version 0.1.4

product_photos rows exist
Core photo storage exists
photo files exist
photo URLs resolve in UI
Product 58 UI can show photos
```

Но реальная OWNER-проверка выявила несоответствие.

---

# 1. Реальный OWNER result

Owner сообщает:

```text
Расширение при передаче объявления сообщает о картинке / картинках.
Но в интерфейсе товаров Техноребута фотографии как нормальная часть товара фактически не видны.

Нет понятного блока фотографий.
Нет очевидного места, где посмотреть фотографии товара.
Owner не может открыть Product и проверить реально сохранённые изображения.

Допустимо, что товар существует без фотографии.
```

ВАЖНО:

Не считать, что расширение обязательно врёт про изображение.

Изображение действительно может проходить по цепочке и сохраняться.

Проблема текущего owner-check:

```text
PHOTO_PIPELINE_BACKEND_MAY_EXIST
OWNER_VISIBLE_PRODUCT_PHOTO_UI = NOT PROVEN / FAILED
```

R8-R6 НЕ принят.

---

# 2. Цель R8-R7

Установить фактическое состояние photo pipeline после R8-R6 и убрать несоответствие между отчётом агента и реальным интерфейсом владельца.

Доказать отдельно:

```text
A. Есть ли реальные фото в Core DB/storage.
B. Отдаёт ли их Core API.
C. Получает ли их inventory-sales-module.
D. Есть ли owner-visible UI для просмотра фотографий товара.
E. Что происходит при 0 фотографий.
```

Если backend уже корректен — НЕ переделывать его заново.

Исправлять минимально необходимый слой.

---

# 3. Сначала READ-ONLY аудит Product 58

До любых изменений НЕ выполнять повторный импорт объявления.

Не изменять Product 58.

Проверить фактическое состояние:

```text
Product ID: 58
Avito ID: 8313765236
```

Зафиксировать:

```text
PRODUCT_58_EXISTS
PRODUCT_58_TITLE
PRODUCT_58_PRICE
PRODUCT_58_SOURCE_ORIGIN

PRODUCT_58_DB_PHOTO_COUNT
PRODUCT_58_PHOTO_ROWS
PRODUCT_58_STORAGE_FILE_COUNT
PRODUCT_58_STORAGE_FILES
PRODUCT_58_STORAGE_FILE_SIZES
PRODUCT_58_STORAGE_MIME_TYPES

PRODUCT_58_CORE_API_PHOTO_COUNT
PRODUCT_58_CORE_API_PHOTO_URLS
PRODUCT_58_PHOTO_HTTP_STATUS
```

Если photo rows существуют, установить:

```text
table/model name
product_id relation
storage path/reference
position/order
source URL if stored
created_at
```

Не выводить секреты/cookies/tokens.

---

# 4. Проверить утверждения R8-R6

R8-R6 заявил, что до исправления у Product 58 были dummy placeholders, а затем был реализован Core remote photo downloader.

Нужно подтвердить текущими фактическими данными, а не ссылкой на старый отчёт:

```text
dummy 146-byte files still exist: yes/no
real image files exist: yes/no
real file size(s)
real MIME
real HTTP retrieval
```

Если старые dummy rows/files остались параллельно реальным фото:

```text
не удалять автоматически live owner data;
сначала классифицировать;
предложить safe cleanup only if necessary;
не выполнять destructive cleanup без необходимости.
```

---

# 5. Найти фактический owner-facing product route

Определить, какой URL реально использует владелец для товаров через Admin Shell.

Проверить минимум:

```text
http://localhost:8011/inventory/products
product detail route
product edit route
```

Зафиксировать:

```text
OWNER_PRODUCTS_URL
OWNER_PRODUCT_58_URL
HTTP_STATUS
TEMPLATE_USED
ROUTER_USED
CORE_CLIENT_METHOD_USED
```

Не проверять только raw module port.

Owner-facing проверка должна идти через:

```text
localhost:8011
```

---

# 6. Аудит inventory-sales-module

Проверить:

```text
inventory-sales-module/app/routers/products.py
inventory-sales-module/app/core_client.py
inventory-sales-module/app/templates/products*.html
inventory-sales-module/app/templates/product_detail*.html
inventory-sales-module/app/templates/product_edit*.html
```

и любые реально используемые эквиваленты.

Ответить:

```text
Есть ли поле photos/images в Core response?
Передаёт ли router photos в template?
Рендерит ли template photos?
Есть ли route detail вообще?
Есть ли ссылка из списка товаров на detail?
Не существует ли gallery code, который недостижим из UI?
Не используется ли другой template, чем тот, который агент изменял?
```

Особо проверить ситуацию:

```text
код photo UI существует,
но owner route рендерит другой template
```

или:

```text
photo UI добавлен только в raw inventory port,
но не работает через Admin Shell proxy
```

---

# 7. Проверка списка товаров

На:

```text
http://localhost:8011/inventory/products
```

не обязательно показывать полноценную галерею.

Но владелец должен иметь понятный путь к фотографиям товара.

Минимально допустимо:

```text
Название товара
→ ссылка/кнопка «Открыть»
→ карточка товара
→ блок «Фотографии»
```

Если существующая UX-модель уже имеет карточку товара — использовать её.

Не создавать второй параллельный интерфейс товара.

---

# 8. Product detail — обязательный owner contract

В карточке товара должен быть явный блок:

```text
Фотографии
```

Если фото есть:

```text
показать реальные thumbnails / preview
сохранить порядок position
главная фотография первой
каждая фотография кликабельна или открывается в нормальном размере
```

Минимально достаточно обычной HTML-галереи.

Не нужен сложный JS gallery framework.

Если фото нет:

```text
Фотографий нет
```

Это нормальное состояние.

НЕ показывать fake placeholder как реальную фотографию.

---

# 9. Product без фотографий — обязательный сценарий

Найти существующий товар с:

```text
0 product_photos
```

или использовать безопасный isolated test fixture.

Проверить:

```text
карточка открывается
HTTP 200
нет ошибки шаблона
нет broken <img>
нет fake placeholder, считающегося фотографией
показывается «Фотографий нет»
```

Не создавать live owner product только ради проверки, если можно использовать существующий товар или isolated test.

---

# 10. Core API contract

Если Core уже отдаёт фотографии — использовать существующий API.

Не создавать новый duplicate endpoint.

Проверить фактический contract:

```text
GET product
GET product photos / media
photo file serving route
```

Если product response не содержит photos, но есть отдельный photo endpoint:

```text
inventory-sales-module должен получить их через Core HTTP API
```

Прямой доступ Inventory к Core DB/storage запрещён.

Архитектура:

```text
Inventory → Core HTTP API → photo metadata/content
```

Запрещено:

```text
Inventory читает C:\tbootit\data\... напрямую
Inventory читает SQLite напрямую
Inventory строит filesystem URL самостоятельно
```

---

# 11. Core owns photo storage

Подтвердить:

```text
photo DB relation owned by Core
photo files owned by Core
persistent storage/volume
photo serving owned by Core
```

Если это уже реализовано в R8-R6 — не переписывать.

Только исправить недостающую интеграцию в UI/API client.

---

# 12. Admin Shell proxy

Проверить, что изображения доступны владельцу через normal owner flow.

Если HTML находится на:

```text
localhost:8011
```

а img src указывает на raw Core/module port, проверить существующую proxy architecture.

Предпочтительно owner-visible URL должен работать стабильно через принятый proxy contract.

Не создавать CORS workaround вместо корректного same-origin/proxy пути, если проект уже использует Admin Shell reverse proxy.

Проверить:

```text
page HTTP 200
img HTTP 200
Content-Type image/*
browser-accessible URL
```

---

# 13. Не выполнять повторный реальный Avito import автоматически

До завершения аудита:

```text
DO_NOT_REIMPORT_OWNER_LISTING_AUTOMATICALLY
```

Product 58 уже является owner live data.

Автоматические тесты должны использовать isolated fixtures.

После исправления подготовить owner check.

Только Owner сам решает, нажимать ли повторно:

```text
«Передать объявление в Техноребут»
```

---

# 14. Если Product 58 уже содержит реальные фото

Если аудит подтверждает:

```text
DB photos > 0
real files > 0
Core returns photos
```

но UI их не показывает:

ROOT CAUSE должен быть точно классифицирован, например:

```text
Inventory CoreClient drops photos
router does not request photos
template does not render photos
wrong template used
wrong route used
Admin Shell proxy path missing
photo URLs inaccessible from owner page
```

Исправить только нужные слои.

---

# 15. Если Product 58 НЕ содержит реальных фото

Если выяснится:

```text
DB photo count = 0
или
files are still dummy/broken
или
Core API returns 0
```

то R8-R6 backend fix фактически не доказан.

В таком случае:

```text
не маскировать проблему UI;
зафиксировать backend root cause;
исправить photo pipeline;
после этого реализовать owner-visible UI;
```

Но не создавать новый Product.

Сохранять:

```text
Product ID 58
Avito ID 8313765236
```

Не выполнять реальный owner reimport автоматически.

---

# 16. UI text

Полностью по-русски.

Обязательные тексты:

```text
Фотографии
Фотографий нет
```

Для фото можно показать:

```text
Фото 1
Фото 2
...
```

если требуется alt/title.

Не выводить:

```text
null
None
[]
raw JSON
filesystem path
internal storage filename
```

в owner UI.

---

# 17. Tests — Inventory/UI

Добавить/обновить тесты, соответствующие реальным путям проекта.

Минимум:

```text
test_product_detail_zero_photos
test_product_detail_one_photo
test_product_detail_multiple_photos
test_product_photos_preserve_order
test_product_photo_url_rendered
test_product_without_photo_has_no_fake_image
test_product_detail_owner_route
test_product_photo_owner_proxy_access
```

Если имена файлов в проекте приняты иначе — использовать существующий naming pattern.

Не создавать бессмысленные duplicate test modules.

---

# 18. Tests — CoreClient contract

Проверить:

```text
CoreClient получает photo metadata через HTTP
0 photos → []
1 photo → 1
N photos → N
```

Добавить regression test на конкретный обнаруженный root cause.

Например, если router забывал photos:

```text
test_product_detail_router_passes_photos_to_template
```

Если использовался неправильный template:

```text
test_owner_product_detail_uses_photo_capable_template
```

---

# 19. Tests — Core, только если требуется изменение Core

Core менять только если аудит докажет backend defect.

Если Core не меняется — не добавлять лишний backend-код.

Если Core меняется, safe tests обязательны:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
```

Не запускать unsafe Core pytest против live DB.

---

# 20. Full regression

После исправления запустить:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
docker compose exec -T inventory-sales-module pytest
docker compose exec -T avito-module pytest
docker compose exec -T repairs-module pytest
pytest admin-shell/tests
pytest chrome-extension/technoreboot-avito/tests
```

Указать фактические финальные числа.

Не копировать числа из R8-R6.

---

# 21. Runtime owner-facing proof

Поднять/проверить реальный stack.

Зафиксировать:

```powershell
docker compose ps
```

Проверить:

```text
http://localhost:8011/inventory/products
OWNER_PRODUCT_58_URL
```

Для Product 58:

```text
HTTP 200
block «Фотографии» exists
real photo count shown/rendered
each img src resolves HTTP 200
Content-Type = image/*
```

Если Product 58 фактически имеет 0 фото после read-only audit:

```text
не утверждать, что фото UI PASS на Product 58;
проверить UI через isolated fixture;
owner reimport remains required.
```

---

# 22. Browser-level proof where practical

Если возможно без ненадёжной GUI automation:

```text
получить rendered HTML owner route
проверить наличие блока «Фотографии»
проверить <img src>
выполнить HTTP GET image URL
```

Не считать unit test достаточным доказательством owner UI.

---

# 23. Safety

Проверить:

```text
Product 58 not deleted
Product 58 not duplicated
owner listing not automatically reimported
live DB destructive cleanup = 0
direct DB access from Inventory = 0
direct photo storage access from Inventory = 0
cookies transferred = 0
credentials transferred = 0
extension token logged = 0
```

Forbidden:

```text
DROP TABLE
drop_all
mass DELETE
git add .
git add -A
git add -u
git reset
git clean
git rebase
git commit --amend
force push
```

---

# 24. Documentation

Обновить:

```text
docs/stage06a_r8_extension_photo_import.md
README.md
chrome-extension/technoreboot-avito/README.md
```

Создать:

```text
reports/stage06a_r8_r7_product_photo_ui_owner_gap_report.md
```

Обновить актуальный daily log:

```text
logs/2026-08-13.md
```

Сохранить этот prompt:

```text
.agents/received_prompts/TECHNOREBOOT_STAGE06A_R8_R7_PRODUCT_PHOTO_UI_OWNER_GAP_FIX_PROMPT.md
```

---

# 25. Report structure

Отчёт должен содержать:

```text
STATUS

OWNER_REPORTED_GAP

R8_R6_CLAIMS_AUDIT

PRODUCT_58_READ_ONLY_STATE
PRODUCT_58_DB_PHOTOS
PRODUCT_58_STORAGE_PHOTOS
PRODUCT_58_CORE_API_PHOTOS

OWNER_PRODUCTS_ROUTE
OWNER_PRODUCT_DETAIL_ROUTE
TEMPLATE_USED
INVENTORY_CORE_CLIENT_PHOTO_CONTRACT

ROOT_CAUSE

BACKEND_CHANGES
INVENTORY_CHANGES
ADMIN_SHELL_PROXY_CHANGES
TEMPLATE_CHANGES

ZERO_PHOTO_BEHAVIOR
ONE_PHOTO_BEHAVIOR
MULTI_PHOTO_BEHAVIOR

PRODUCT_58_RUNTIME_PROOF
OWNER_ROUTE_RUNTIME_PROOF
IMAGE_HTTP_PROOF

TESTS
SAFETY
FILES_CHANGED
COMMIT
PUSH
FINAL_GIT_STATUS

OWNER_CHECK_GUIDE
FINAL_STATUS
```

---

# 26. Git

Перед работой:

```powershell
Set-Location C:\tbootit

git status --short --untracked-files=all
git branch --show-current
git rev-parse HEAD
git log --oneline -10
git diff --name-status
git diff --stat
docker compose ps
```

Не затереть существующие незакоммиченные изменения.

Использовать только targeted add.

Commit message:

```text
Fix owner product photo visibility
```

или более точный, если root cause требует другого названия.

После:

```powershell
git push origin main
git status --short --untracked-files=all
git rev-parse HEAD
git log --oneline -5
```

Git status должен быть clean, кроме заранее существовавших и явно задокументированных unrelated changes.

---

# 27. Definition of Done

R8-R7 готов только если установлены факты:

```text
R8-R6 photo claims independently audited
Product 58 current photo state known
Core photo DB/storage state known
Core photo API state known
owner product detail route identified
owner can see explicit «Фотографии» block
0-photo product shows «Фотографий нет»
real photos render when they exist
no fake placeholder counted as photo
image URLs return HTTP 200 image/*
Inventory uses Core HTTP only
no automatic owner Avito reimport
all regression suites PASS
runtime owner-facing proof completed
targeted commit pushed
final git status clean
```

---

# 28. OWNER CHECK

После завершения остановиться.

Не запускать Stage06A-R9.
Не запускать Stage06B.

Дать Owner точные URL и короткий сценарий проверки.

Owner check должен начинаться БЕЗ нового Avito импорта:

```text
1. Открыть Техноребут → Товары.
2. Открыть Product 58.
3. Найти блок «Фотографии».
4. Если фотографии уже существуют в Core — убедиться, что они реально отображаются.
5. Если фото в Core пока нет — убедиться, что отображается «Фотографий нет».
```

Только если отчёт докажет, что backend готов, но Product 58 нуждается в одном реальном повторном импорте:

```text
6. Owner открывает Avito 8313765236.
7. Нажимает «Передать объявление в Техноребут» ОДИН РАЗ.
8. Product ID должен остаться 58.
9. Снова открыть Product 58.
10. Проверить фото, количество и порядок.
```

Не разрешать full account import.

---

# 29. Final status

При успехе:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE06A_R8_R7_PRODUCT_PHOTO_UI_READY_FOR_OWNER_CHECK

R8_R6_PHOTO_CLAIMS_AUDITED: true
PRODUCT_58_PHOTO_STATE_CONFIRMED: true
CORE_PHOTO_STORAGE_CONFIRMED: true
CORE_PHOTO_API_CONFIRMED: true
OWNER_PRODUCT_PHOTO_UI_AVAILABLE: true
ZERO_PHOTO_PRODUCT_SUPPORTED: true
REAL_PHOTO_RENDERING_VERIFIED: true
OWNER_AVITO_REIMPORT_PERFORMED_BY_AGENT: false
OWNER_MANUAL_CHECK_REQUIRED: true
OWNER_ONE_ITEM_EXTENSION_IMPORT_NOT_YET_FULLY_ACCEPTED: true
FULL_ACCOUNT_IMPORT_NOT_YET_AUTHORIZED: true
DO_NOT_START_STAGE06A_R9_WITHOUT_OWNER_ACCEPTANCE: true
DO_NOT_START_STAGE06B_REVERSE_SYNC_WITHOUT_OWNER_ACCEPTANCE: true
```

Если backend photo state не подтверждён:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE06A_R8_R7_PRODUCT_PHOTO_UI_BLOCKED

BLOCKERS:
...
```

После финального отчёта ОСТАНОВИТЬСЯ.
