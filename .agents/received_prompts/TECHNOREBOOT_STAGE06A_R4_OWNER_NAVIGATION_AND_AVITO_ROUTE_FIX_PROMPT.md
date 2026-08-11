# TECHNOREBOOT — Stage06A-R4 Owner Navigation and Avito Route Fix

Рабочий репозиторий:

```powershell
C:\tbootit
```

Стартовая точка:

```text
Stage06A-R3
Commit: 82a397d
```

Это corrective stage. Stage06B НЕ начинать.

## 1. Реальный blocker владельца

Владелец получил:

```text
http://localhost:8040/avito
{"detail":"Not Found"}
```

Также:
- верхние ссылки сбиваются;
- переходы уводят на raw module ports;
- «Настройки Avito» не открываются там, где ожидается.

Stage06A-R3 НЕ принят.

## 2. Главный контракт

Единственный owner-facing origin:

```text
http://localhost:8011
```

Все пользовательские разделы должны жить только под ним:

```text
/                          Панель
/inventory/products        Товары
/inventory/sales           Продажи
/inventory/reports/sales   Отчёты
/repairs/repairs           Ремонты
/avito                     Авито
```

Запрещено owner-facing переходить на:

```text
8000
8020
8030
8040
8061
```

Raw ports могут существовать только как internal/developer endpoints.

## 3. Сначала воспроизвести

До кода зафиксировать:

```text
A. http://localhost:8011
B. Ремонты
C. открыть страницу ремонта
D. нажать Авито
E. записать фактический URL

F. Товары -> Авито
G. Продажи -> Авито
H. Панель -> Авито
```

Report:

```text
FROM_PAGE
LINK
ACTUAL_URL
EXPECTED_URL
```

## 4. Найти системную причину

Не чинить одну ссылку вручную.

Аудировать:

```text
url_for()
request.base_url
ROOT_PATH
X-Forwarded-Prefix
X-Forwarded-Host
Host
RedirectResponse
Location
window.location
hardcoded localhost
form action
```

Искать:

```powershell
git grep -n -I "localhost:8000\|localhost:8020\|localhost:8030\|localhost:8040\|localhost:8061" -- admin-shell inventory-sales-module repairs-module avito-module
```

```powershell
git grep -n -I "url_for(" -- admin-shell/app inventory-sales-module/app repairs-module/app avito-module/app
```

```powershell
git grep -n -I "RedirectResponse\|window.location\|location.href\|form action=" -- admin-shell/app inventory-sales-module/app repairs-module/app avito-module/app
```

Классифицировать каждый match как:
- internal;
- developer-only;
- owner-facing.

Owner-facing raw port matches = 0.

## 5. Canonical navigation

Cross-module owner links НЕ генерировать через backend module host.

Использовать canonical same-origin paths:

```html
<a href="/">Панель управления</a>
<a href="/inventory/products">Товары</a>
<a href="/inventory/sales">Продажи</a>
<a href="/inventory/reports/sales">Отчёты</a>
<a href="/repairs/repairs">Ремонты</a>
<a href="/avito">Авито</a>
```

Создать единый navigation helper/macro/contract, чтобы ссылки не расходились между модулями.

## 6. Admin Shell proxy

Admin Shell должен проксировать отдельные модули, сохраняя owner origin.

Передавать корректно:

```text
Host: localhost:8011
X-Forwarded-Host: localhost:8011
X-Forwarded-Port: 8011
X-Forwarded-Proto: http
X-Forwarded-Prefix: соответствующий prefix
```

Не позволять backend-у формировать public URLs вида:

```text
localhost:8030
localhost:8040
avito-module:8020
repairs-module:8040
```

## 7. Location rewrite

Если backend отвечает:

```http
Location: http://localhost:8040/...
```

или internal container URL, Admin Shell обязан переписать redirect в owner same-origin path.

Проверить:
- GET redirects;
- POST forms;
- create/edit flows;
- status changes;
- cancel/reissue;
- repair actions.

## 8. ROOT_PATH audit

Проверить `inventory-sales-module`, `repairs-module`, `avito-module`.

Не допустить двойных prefix:

```text
/repairs/repairs/repairs
/inventory/inventory/products
```

Canonical owner routes должны быть стабильны.

## 9. Avito route

Обязательно:

```text
GET http://localhost:8011/avito
```

Должно быть:

```text
HTTP 200
HTML
«Настройки Avito»
```

Не 404 и не JSON error.

## 10. Avito entry UX

На `/avito` явно показать:

```text
Настройки Avito
```

Основные действия:

```text
+ Добавить аккаунт
Авторизоваться в Avito
```

Если аккаунт уже существует — CTA «Авторизоваться в Avito» должен быть заметен сразу.

## 11. Верхнее меню

Проверить страницы:

```text
/
/inventory/products
/inventory/sales
/inventory/reports/sales
/repairs/repairs
/repairs/repairs/{id}
/avito
/avito/accounts
```

На каждой:
- меню видно;
- Avito ведёт на `/avito`;
- Repairs ведёт на `/repairs/repairs`;
- Sales ведёт на `/inventory/sales`;
- Products ведёт на `/inventory/products`;
- owner origin остаётся 8011.

## 12. Cross-module links

Отдельно проверить:

```text
Avito -> Product
Sale -> Product
Repair -> Sale
Sale -> Repair
```

Все должны оставаться на `localhost:8011`.

## 13. Forms

Проверить form actions внутри proxied modules.

POST не должен уходить на raw backend port.

После submit пользователь остаётся внутри owner shell на 8011.

## 14. Runtime smoke — обязательно против Docker

Не ограничиваться TestClient.

После `docker compose up -d` реально проверить:

```text
http://localhost:8011/
http://localhost:8011/inventory/products
http://localhost:8011/inventory/sales
http://localhost:8011/repairs/repairs
http://localhost:8011/avito
```

Все должны возвращать expected HTML/redirect, без raw module URL.

## 15. Navigation crawl

Создать runtime/test crawl:

1. получить HTML owner page;
2. найти navbar links;
3. убедиться, что нет raw port;
4. пройти по ссылкам через 8011;
5. проверить 200/expected redirect.

## 16. Обязательная регрессия реального бага

Создать:

```text
admin-shell/tests/test_repairs_nav_avito_stays_on_admin_origin.py
```

Контракт:

```text
FROM:
http://localhost:8011/repairs/repairs

NAV:
Авито

EXPECTED:
http://localhost:8011/avito

FORBIDDEN:
http://localhost:8040/avito
```

## 17. Дополнительные tests

Создать/обновить:

```text
admin-shell/tests/test_owner_origin_contract.py
admin-shell/tests/test_avito_settings_route_is_reachable.py
admin-shell/tests/test_proxy_location_rewrite.py
admin-shell/tests/test_nav_crawl.py
admin-shell/tests/test_no_raw_owner_ports_runtime.py
```

Сохранить существующие:
- unified navigation;
- no owner raw module ports;
- cross-module same-origin links.

## 18. Manual Avito auth сохранить

Не ломать R3:

```text
manual login required;
embedded Chromium;
same persistent profile;
discovery blocked before authorized;
no stealth;
no CAPTCHA bypass;
one-item probe;
full import gated.
```

R4 не переписывает parser — только owner routing + Avito reachability.

## 19. Regression tests

Обязательно:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
docker compose exec -T inventory-sales-module pytest
docker compose exec -T avito-module pytest
docker compose exec -T repairs-module pytest
pytest admin-shell/tests
```

## 20. Safety

Проверить:
- owner-facing raw module URLs = 0;
- direct DB access from avito-module = 0;
- browser sessions tracked in git = 0;
- credentials stored = 0;
- noVNC public exposure = 0.

## 21. Документация

Создать:

```text
docs/stage06a_r4_owner_origin_navigation_fix.md
reports/stage06a_r4_owner_origin_navigation_fix_report.md
```

Обновить:

```text
README.md
logs/2026-08-11.md
```

## 22. Report sections

```text
STATUS
OWNER_REPORTED_BUG
BEFORE_REPRODUCTION
ROOT_CAUSE
OWNER_ORIGIN_CONTRACT
PROXY_HEADERS
LOCATION_REWRITE
ROOT_PATH_AUDIT
NAVIGATION_COMPONENT
CROSS_MODULE_LINKS
AVITO_ROUTE
AVITO_SETTINGS_UI
FORMS_AND_REDIRECTS
NAV_CRAWL
RUNTIME_DOCKER_SMOKE
TESTS
RAW_PORT_SCAN
FILES_CHANGED
COMMIT
PUSH
FINAL_GIT_STATUS
OWNER_BROWSER_ONLY_CHECK
FINAL_STATUS
```

## 23. Git

Expected HEAD:

```text
82a397d
```

или фактический потомок.

Только targeted add.

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
```

Commit:

```powershell
git commit -m "Fix owner navigation and Avito settings route"
git push origin main
```

## 24. Definition of Done

Готово только если:

```text
owner uses only localhost:8011;
repairs -> Avito stays 8011;
inventory -> Avito stays 8011;
sales -> Avito stays 8011;
dashboard -> Avito stays 8011;
GET /avito = 200;
«Настройки Avito» visible;
«Авторизоваться в Avito» visible;
no raw owner ports in navbar;
no raw owner ports in redirects;
forms stay under proxy paths;
cross-module links stay 8011;
runtime Docker smoke PASS;
navigation crawl PASS;
Core PASS;
Inventory PASS;
Avito PASS;
Repairs PASS;
Admin Shell PASS;
targeted commit;
push;
clean Git.
```

## 25. Owner check after R4

Owner должен сделать только:

```text
1. Открыть http://localhost:8011
2. Нажать Товары
3. Нажать Продажи
4. Нажать Ремонты
5. Нажать Авито
6. Проверить: порт всегда 8011
7. Проверить: верхнее меню всегда остаётся
8. Проверить: открывается «Настройки Avito»
9. Проверить: есть «Авторизоваться в Avito»
```

Только после этого возвращаться к ручному Avito login probe.

## 26. Final status

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE06A_R4_OWNER_NAVIGATION_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
OWNER_AVITO_LOGIN_PROBE_NOT_YET_ACCEPTED: true
FULL_ACCOUNT_IMPORT_NOT_YET_AUTHORIZED: true
DO_NOT_START_STAGE06B_REVERSE_SYNC_WITHOUT_OWNER_ACCEPTANCE: true
```
