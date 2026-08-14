# TECHNOREBOOT — Avito UI Cleanup R1: Fix Product Button / Core API Regression

Репозиторий:

```powershell
C:\tbootit
```

Контекст:

```text
Avito UI Cleanup Plugin-Only выполнен.
Commit cleanup: 6bb4f2c
```

Но OWNER CHECK выявил регресс.

---

# 1. OWNER ERROR

Реальный сценарий Owner:

```text
1. Открыть интерфейс Техноребута.
2. Нажать на кнопку / ссылку конкретного товара.
3. Вместо карточки товара открывается ошибка.
```

Текст ошибки:

```text
## Ошибка

Ошибка Core API

На главную
К списку товаров
```

То есть ошибка возникает ИМЕННО:

```text
при переходе в карточку товара через owner UI
```

а не при работе Avito extension.

Ожидаемый target route для Product 58:

```text
http://localhost:8011/inventory/products/58
```

До cleanup карточка товара работала.

Следовательно:

```text
CLEANUP_OWNER_CHECK = FAILED
PRODUCT_DETAIL_NAVIGATION_REGRESSION = true
```

---

# 2. ЦЕЛЬ

Найти и исправить только регресс:

```text
Owner product button/link
→ product detail route
→ Core API
→ product page
```

После исправления:

```text
клик по товару
→ корректная карточка товара
→ без "Ошибка Core API"
```

---

# 3. НЕ ТРОГАТЬ

НЕЛЬЗЯ:

- возвращать старый Avito sync/import/parser UI;
- откатывать весь cleanup;
- удалять R9 Core model;
- менять photo import;
- менять Avito extension без необходимости;
- начинать Stage06A-R9-R1;
- начинать Stage06A-R10;
- начинать Stage06B.

---

# 4. СНАЧАЛА GIT/RUNTIME AUDIT

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

---

# 5. СРАВНИТЬ CLEANUP DIFF

Определить parent cleanup commit:

```powershell
git rev-parse 6bb4f2c^
```

Посмотреть:

```powershell
git diff --name-status 6bb4f2c^ 6bb4f2c
git diff --stat 6bb4f2c^ 6bb4f2c
```

Особенно:

```text
admin-shell/app/main.py
admin-shell/app/templates/index.html
inventory-sales-module/app/templates/base.html
repairs-module/app/templates/base.html
```

и все изменения ссылок/маршрутов товаров.

---

# 6. ВОСПРОИЗВЕСТИ OWNER PATH

Проверить именно тот путь, который создаётся owner UI.

Найти в шаблоне/JS:

```text
product link href
button onclick
row click handler
modal open handler
```

Для Product 58 зафиксировать фактический URL:

```text
OWNER_PRODUCT_CLICK_TARGET = ...
```

Проверить:

```text
GET target URL
HTTP status
response body
```

---

# 7. ОПРЕДЕЛИТЬ FAILING LAYER

Нужно установить, где ломается цепочка:

```text
A. неправильный href / URL после cleanup
B. Admin Shell route
C. Inventory module route
D. Admin Shell proxy to Inventory
E. Inventory route → Core API
F. Core endpoint
G. wrong API path
H. response schema mismatch
I. template/render error
```

Не гадать.

---

# 8. ЛОГИ

Получить:

```powershell
docker compose logs --tail=300 admin-shell
docker compose logs --tail=300 inventory-sales-module
docker compose logs --tail=300 core
```

Найти traceback / HTTP error рядом с Owner переходом на Product 58.

Зафиксировать:

```text
FAILED_URL
FAILED_SERVICE
FAILED_ENDPOINT
HTTP_STATUS
ERROR_MESSAGE
TRACEBACK_FILE
TRACEBACK_FUNCTION
TRACEBACK_LINE
```

---

# 9. ПРОВЕРИТЬ DIRECT ROUTES

Сравнить:

```text
http://localhost:8011/inventory/products
http://localhost:8011/inventory/products/58
```

Если список товаров работает, а detail нет:

это важный сигнал.

Проверить также внутренний inventory route напрямую только технически,
если это допустимо в dev:

```text
inventory-sales-module internal product detail route
```

Но Owner UI должен оставаться same-origin через 8011.

---

# 10. ПРОВЕРИТЬ CORE API

Определить какой Core endpoint вызывает product detail.

Например фактически может быть:

```text
GET /api/products/58/details
GET /api/v1/products/58
...
```

Не предполагать.

Проверить его напрямую из контейнера/через proxy.

Зафиксировать:

```text
CORE_ENDPOINT
CORE_HTTP_STATUS
CORE_JSON_VALID
CORE_RESPONSE_SHAPE
```

---

# 11. ОСОБО ПРОВЕРИТЬ CLEANUP-ИЗМЕНЕНИЯ В ROUTING

Cleanup менял owner navigation.

Проверить, не произошло ли:

```text
старый working route → новый broken route
relative URL вместо absolute owner route
/admin-api/products/... вместо /inventory/products/...
/products/{id} без proxy prefix
```

И не был ли случайно удалён route/import, который нужен product detail.

---

# 12. ОСОБО ПРОВЕРИТЬ ADMIN SHELL MAIN.PY

Cleanup менял:

```text
admin-shell/app/main.py
```

Проверить:

- proxy routes;
- redirects;
- catch-all;
- route ordering;
- removed Avito routes;
- side effects от route imports;
- product detail proxy logic.

Нельзя исправлять unrelated code.

---

# 13. ИСПРАВЛЕНИЕ

Сделать минимальный fix.

Требование:

```text
owner product click
→ /inventory/products/{id}
→ page renders
→ Core data loads
```

Сохранить:

```text
same-origin owner architecture
plugin-only Avito UI
R9 data model
photo gallery
sales/inventory behavior
```

---

# 14. TESTS — ОБЯЗАТЕЛЬНО

Добавить regression test:

```text
test_owner_product_link_opens_product_detail
```

или эквивалент.

Тест должен:

1. получить owner product list/page;
2. извлечь или проверить link Product 58;
3. GET этот URL;
4. ожидать HTTP 200;
5. убедиться, что нет:
   `Ошибка Core API`.

Также тест:

```text
product detail Product 58 returns 200
```

---

# 15. CLEANUP REGRESSION TESTS СОХРАНИТЬ

Проверить, что после fix:

```text
старые Avito sync/import/parser пункты не вернулись;
остался только «Расширение Avito»;
extension page работает;
product detail работает.
```

---

# 16. FULL REGRESSION

Запустить:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
docker compose exec -T inventory-sales-module pytest
docker compose exec -T avito-module pytest
docker compose exec -T repairs-module pytest
pytest admin-shell/tests
pytest chrome-extension/technoreboot-avito/tests
```

Указать фактические counts.

---

# 17. RUNTIME

Проверить:

```text
Core healthy
Inventory healthy
Avito module healthy
Repairs healthy
Admin Shell healthy
```

И:

```text
GET /inventory/products → 200
GET /inventory/products/58 → 200
```

---

# 18. НЕ МЕНЯТЬ EXTENSION VERSION

Если extension code не меняется:

```text
version НЕ bump.
ZIP НЕ пересобирать без причины.
```

---

# 19. DOCUMENTATION

Создать:

```text
reports/avito_ui_cleanup_r1_product_detail_core_api_regression_report.md
```

Обновить:

```text
logs/2026-08-14.md
```

Сохранить prompt:

```text
.agents/received_prompts/TECHNOREBOOT_AVITO_UI_CLEANUP_R1_PRODUCT_DETAIL_CORE_API_FIX_PROMPT.md
```

---

# 20. REPORT STRUCTURE

Обязательно:

```text
STATUS

OWNER_ERROR
OWNER_PRODUCT_CLICK_TARGET

FAILED_LAYER
FAILED_URL
FAILED_SERVICE
FAILED_ENDPOINT
HTTP_STATUS
TRACEBACK

ROOT_CAUSE
CLEANUP_CHANGE_THAT_TRIGGERED_REGRESSION

FIX
FILES_CHANGED

PLUGIN_ONLY_UI_PRESERVED
R9_MODEL_PRESERVED
EXTENSION_CHANGED
EXTENSION_VERSION

TESTS
RUNTIME

COMMIT
PUSH
FINAL_GIT_STATUS

OWNER_CHECK_GUIDE
FINAL_STATUS
```

---

# 21. DEFINITION OF DONE

PASS только если:

```text
OWNER_PRODUCT_CLICK_WORKS: true
PRODUCT_DETAIL_ROUTE_200: true
CORE_API_ERROR_ELIMINATED: true
PRODUCT_58_OPENS_CORRECTLY: true
PHOTO_GALLERY_STILL_WORKS: true
PLUGIN_ONLY_AVITO_UI_PRESERVED: true
LEGACY_AVITO_UI_STILL_HIDDEN: true
R9_CORE_MODEL_PRESERVED: true
EXTENSION_UNCHANGED_OR_JUSTIFIED: true
OWNER_MANUAL_CHECK_REQUIRED: true
```

---

# 22. GIT SAFETY

Запрещено:

```text
git add .
git add -A
git add -u
git reset
git clean
git rebase
git commit --amend
force push
DROP TABLE
mass DELETE
```

Targeted add only.

Commit message:

```text
Fix product detail route after Avito UI cleanup
```

Push:

```powershell
git push origin main
```

---

# 23. OWNER CHECK GUIDE

После успешного отчёта ОСТАНОВИТЬСЯ.

Owner проверяет:

```text
1. Открыть http://localhost:8011/
2. Нажать на товар.
3. Карточка товара должна открыться без «Ошибка Core API».
4. Проверить Product 58.
5. Фото должны отображаться.
6. В меню по-прежнему только «Расширение Avito».
7. Старые Avito sync/import/parser элементы не должны вернуться.
```

После OWNER acceptance:

```text
cleanup считается принятым
```

и следующий шаг:

```text
повторно отправить
TECHNOREBOOT_STAGE06A_R9_R1_ATTRIBUTE_PROVENANCE_EXTENSION_SCOPE_AUDIT_PROMPT.md
```

---

# 24. FINAL STATUS

При успехе:

```text
FINAL_STATUS:
TECHNOREBOOT_AVITO_UI_CLEANUP_R1_PRODUCT_DETAIL_FIXED_READY_FOR_OWNER_CHECK

OWNER_PRODUCT_CLICK_WORKS: true
PRODUCT_DETAIL_ROUTE_200: true
CORE_API_ERROR_ELIMINATED: true
PLUGIN_ONLY_AVITO_UI_PRESERVED: true
R9_CORE_MODEL_PRESERVED: true
OWNER_MANUAL_CHECK_REQUIRED: true

PROJECT_NEXT_STEP_AFTER_OWNER_ACCEPTANCE:
RESUME_STAGE06A_R9_R1
```

После отчёта ОСТАНОВИТЬСЯ.
