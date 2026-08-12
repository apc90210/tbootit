# TECHNOREBOOT — Stage06A-R8 Chrome Extension + Local Avito Bridge One-Item Probe

## Роль

Ты senior solution architect, Chrome Extension Manifest V3 developer, FastAPI developer, frontend developer, integration engineer и release QA проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Стартовая точка:

```text
Stage06A-R7
Commit: c41c836
```

Это новый экспериментальный путь после того, как embedded Linux Chromium/noVNC оказался блокируемым Avito.

Stage06B reverse sync НЕ начинать.

---

# 1. Решение владельца

Используем:

```text
обычный Google Chrome / Chromium на Windows
        ↓
обычная ручная авторизация пользователя в Avito
        ↓
Chrome Extension «Техноребут Avito»
        ↓
Local Avito Bridge
        ↓
avito-module
        ↓
Core API
```

Критически:

```text
НЕ используем noVNC для owner Avito login;
НЕ используем Linux Chromium для owner Avito login;
НЕ используем Playwright/WebDriver для owner login;
НЕ копируем cookies;
НЕ читаем пароль;
НЕ пытаемся обходить блокировки Avito.
```

---

# 2. Цель R8

Не строить сразу полный синхронизатор.

Нужно доказать следующий минимальный сценарий:

```text
1. Owner открывает обычный Chrome Windows.
2. Owner обычным способом входит в свой Avito.
3. Owner устанавливает локальное расширение Техноребут.
4. Расширение подключается к localhost:8011.
5. Owner открывает «Мои объявления».
6. Расширение видит список собственных объявлений.
7. Owner открывает одну карточку.
8. Нажимает в расширении «Передать в Техноребут».
9. Техноребут получает:
   - Avito ID
   - URL
   - title
   - price
   - description
   - category
   - brand/model where available
   - characteristics
   - photos
   - status where available
10. Core создаёт/обновляет один Product.
11. Повторная отправка той же карточки не создаёт дубль.
```

После этого STOP для owner acceptance.

---

# 3. Архитектурный принцип

Расширение работает в обычной пользовательской сессии Chrome.

Оно НЕ должно:

```text
запрашивать пароль;
читать password fields;
экспортировать cookies;
читать Chrome cookie database;
отправлять cookies в Technoreboot;
подключаться к DevTools;
использовать WebDriver;
использовать Playwright;
менять fingerprint;
скрывать automation.
```

Расширение получает данные только из страницы, которую пользователь открыл в обычном Chrome.

---

# 4. Новый модуль расширения

Создать:

```text
chrome-extension/technoreboot-avito/
```

Минимальная структура:

```text
manifest.json
service_worker.js
content.js
popup.html
popup.js
popup.css
README.md
```

При необходимости:

```text
options.html
options.js
```

Manifest:

```text
Manifest V3
```

---

# 5. Permissions — минимальные

Не просить лишнее.

Предпочтительно:

```json
{
  "permissions": [
    "storage",
    "activeTab",
    "scripting"
  ],
  "host_permissions": [
    "https://www.avito.ru/*",
    "http://localhost:8011/*",
    "http://127.0.0.1:8011/*"
  ]
}
```

Если какая-то permission не нужна — убрать.

НЕ использовать:

```text
cookies permission
webRequestBlocking
proxy
debugger
nativeMessaging
history
downloads
```

без отдельного обоснования.

---

# 6. Расширение не работает скрытно постоянно

На R8 предпочтительно explicit user action.

То есть:

```text
owner открыл Avito page;
owner нажал extension icon;
extension анализирует active tab.
```

Не создавать постоянный массовый crawler в фоне.

---

# 7. Popup UX

Popup на русском:

```text
Техноребут Avito

Статус подключения:
✓ Техноребут доступен
или
✕ Нет подключения

Страница Avito:
✓ Объявление найдено
или
«Откройте объявление Avito»

[Передать объявление в Техноребут]
```

На странице «Мои объявления»:

```text
✓ Страница «Мои объявления»
Найдено: N

[Передать список в Техноребут]
```

---

# 8. Local Bridge

Не принимать write requests от любого сайта без авторизации.

Создать безопасный local bridge contract в `avito-module`, доступный через Admin Shell:

```text
http://localhost:8011/admin-api/avito-extension/...
```

или согласованный same-origin path.

Минимум:

```text
GET  /status
POST /pair
POST /heartbeat
POST /my-listings
POST /listing
```

---

# 9. Pairing

Сделать простое локальное pairing.

В Technoreboot:

```text
Авито
→ Расширение Chrome
→ Подключить расширение
```

Система генерирует одноразовый короткий код.

Например:

```text
483921
```

В popup расширения:

```text
Код подключения
[______]
[Подключить]
```

После успешного pairing bridge выдаёт extension token.

---

# 10. Extension token

Хранить token:

```text
в chrome.storage.local
```

На стороне avito-module хранить:

```text
только hash/identifier token
```

или другой безопасный persistent representation.

Не хранить token в Core DB без необходимости.

Не выводить token в logs.

---

# 11. Pairing security

Pair code:

```text
одноразовый;
TTL 5–10 минут;
после использования недействителен.
```

Bridge:

```text
localhost only;
extension token required for ingestion.
```

Не делать публичный unauthenticated write endpoint.

---

# 12. CORS / extension origin

Настроить bridge строго для local integration.

Не использовать:

```text
Access-Control-Allow-Origin: *
```

для write API без необходимости.

Учитывать, что extension request идёт из extension service worker.

---

# 13. Content extraction — current listing

Из открытой карточки Avito извлечь максимально устойчиво:

Приоритет источников:

```text
1. JSON-LD / structured data
2. embedded page JSON/state
3. semantic DOM
4. visible labels/text
```

Не завязываться только на один fragile CSS selector.

---

# 14. Поля карточки

Минимум:

```text
external_item_id
external_url
title
price
description
category
brand
model
status
characteristics
photos
source_timestamp
```

Если поле отсутствует:

```text
null / empty
```

Не выдумывать.

---

# 15. Avito ID

ID объявления обязателен.

Источники:

```text
URL;
structured data;
page state;
visible item metadata.
```

Если ID надёжно определить нельзя:

```text
НЕ импортировать.
```

Показать:

```text
«Не удалось определить ID объявления.»
```

---

# 16. Ownership

На R8 разрешать ingest только если owner явно работает в собственном аккаунте.

Для «Мои объявления»:

```text
listing URLs получены с own listings page.
```

Для single current listing:

```text
owner explicitly presses «Передать объявление»
```

Не делать произвольный массовый scraping внешних продавцов.

---

# 17. «Мои объявления»

На странице own listings расширение может извлечь:

```text
Avito ID
URL
title
price
status
thumbnail
```

и передать список в Technoreboot.

Это discovery only.

Не импортировать весь список автоматически.

---

# 18. Technoreboot UI

Добавить:

```text
/avito/extension
```

или эквивалентную страницу в Admin Shell.

Показывать:

```text
Расширение Chrome
Статус: подключено / не подключено
Последний heartbeat
Версия расширения
Последний полученный список
Последнее полученное объявление
```

Кнопки:

```text
Подключить расширение
Создать новый код подключения
Скачать расширение
Инструкция установки
```

---

# 19. Распространение расширения

Для локальной разработки НЕ использовать Chrome Web Store.

Собрать:

```text
dist/technoreboot-avito-extension.zip
```

И добавить в UI:

```text
Скачать расширение
```

Owner workflow без CLI:

```text
1. Скачать ZIP из Technoreboot.
2. Распаковать папку.
3. chrome://extensions
4. Режим разработчика.
5. Загрузить распакованное расширение.
```

Не пытаться silently install extension.

---

# 20. Инструкция внутри Technoreboot

На странице `/avito/extension` прямо показать пошагово:

```text
1. Скачайте расширение.
2. Распакуйте ZIP.
3. Откройте chrome://extensions.
4. Включите «Режим разработчика».
5. Нажмите «Загрузить распакованное расширение».
6. Выберите распакованную папку.
7. Вернитесь сюда.
8. Нажмите «Подключить расширение».
```

---

# 21. Existing embedded browser

Не удалять сразу код R5/R6/R7.

Но owner-facing workflow переключить на:

```text
Chrome Extension — экспериментальный основной путь.
```

Embedded browser пометить:

```text
«Экспериментальный старый способ»
```

или скрыть из обычного UI.

Не делать destructive removal в R8.

---

# 22. Avito-module boundary

Расширение НЕ обращается напрямую к Core.

Только:

```text
Chrome Extension
→ Avito Bridge / avito-module
→ Core integration API
```

Сохранить архитектурный boundary.

---

# 23. Ingest schema

Создать versioned payload:

```json
{
  "schema_version": 1,
  "extension_version": "0.1.0",
  "captured_at": "...",
  "page_type": "listing",
  "listing": {
    "external_item_id": "...",
    "external_url": "...",
    "title": "...",
    "price": 0,
    "description": "...",
    "category": "...",
    "brand": "...",
    "model": "...",
    "status": "...",
    "characteristics": {},
    "photos": []
  }
}
```

---

# 24. Validation

Bridge должен валидировать:

```text
schema_version supported;
external_item_id non-empty;
external_url avito.ru;
title non-empty where possible;
price integer/null;
photos URL list;
payload size limit.
```

Не доверять extension payload слепо.

---

# 25. Import into existing Core model

Использовать существующий:

```text
ProductExternalListing
```

и Stage06A import semantics.

Сохранить:

```text
marketplace = avito
external_item_id unique
source_origin = avito
```

Не создавать новую параллельную product model.

---

# 26. Idempotency

Повторная отправка того же:

```text
external_item_id
```

должна:

```text
обновить существующий Product/ExternalListing
или оставить unchanged;
НЕ создать второй Product.
```

---

# 27. Photos

Передать:

```text
source photo URLs
order
```

Core/avito-module использует существующий photo import/storage mechanism.

Сохранить dedup:

```text
source_url
content_hash
```

Повторная отправка:

```text
7 фото → остаётся 7
```

не 14.

---

# 28. Не передавать cookies

Отдельный blocker test:

Extension payload никогда не содержит:

```text
Cookie
Set-Cookie
document.cookie
session token
Authorization Avito
localStorage dump
```

Technoreboot не должен получать Avito session secrets.

---

# 29. Content script privacy

Не собирать:

```text
личные сообщения;
телефонные контакты;
историю браузера;
другие сайты;
пароли;
payment data.
```

R8 работает только на:

```text
www.avito.ru
```

и только для listing-related pages.

---

# 30. Logging

Log safe metadata:

```text
extension connected
listing ID received
import created/updated
photo count
```

Не log:

```text
tokens
cookies
full page HTML
credentials.
```

---

# 31. Current page parser fixtures

Создать saved sanitized HTML fixtures:

```text
chrome-extension/technoreboot-avito/tests/fixtures/
```

Минимум:

```text
listing_with_jsonld.html
listing_with_characteristics.html
my_listings.html
```

Без реальных owner credentials/private data.

---

# 32. Parser design

Parser должен быть отдельным pure function/module, насколько возможно:

```text
extractListing(document)
extractMyListings(document)
```

Чтобы можно было тестировать без реального Avito login.

---

# 33. Tests extension

Если Node runtime в проекте уже есть — использовать native test runner.

Если Node нет — не тащить тяжёлый frontend stack ради R8.

Минимум contract/source tests:

```text
manifest valid
permissions minimal
Avito host permission exists
localhost permission exists
no cookies permission
no debugger permission
no proxy permission
no cookie extraction code
payload schema
parser fixtures
```

---

# 34. Bridge tests

Добавить:

```text
avito-module/tests/test_extension_pairing.py
avito-module/tests/test_extension_pair_expiry.py
avito-module/tests/test_extension_auth_required.py
avito-module/tests/test_extension_heartbeat.py
avito-module/tests/test_extension_listing_validation.py
avito-module/tests/test_extension_listing_idempotency.py
avito-module/tests/test_extension_no_cookie_payload.py
avito-module/tests/test_extension_my_listings_discovery.py
```

---

# 35. Admin Shell tests

Добавить:

```text
admin-shell/tests/test_avito_extension_page.py
admin-shell/tests/test_avito_extension_download.py
admin-shell/tests/test_avito_extension_pairing_ui.py
admin-shell/tests/test_avito_extension_status_ui.py
```

---

# 36. One-item owner probe

После implementation owner делает:

```text
1. Открыть обычный Chrome Windows.
2. Проверить, что Avito работает.
3. В Technoreboot открыть Авито → Расширение Chrome.
4. Скачать ZIP.
5. Установить unpacked extension.
6. Получить pairing code.
7. Ввести code в extension.
8. Увидеть «Техноребут подключен».
9. В Chrome открыть Avito → Мои объявления.
10. Расширение показывает N объявлений.
11. Открыть одно своё объявление.
12. Нажать «Передать объявление в Техноребут».
13. Открыть импортированный Product.
14. Сверить данные.
15. Нажать передачу повторно.
16. Проверить отсутствие дубля.
```

---

# 37. Owner probe UI result

Technoreboot должен показать:

```text
Объявление получено
Avito ID: ...
Product ID: ...
Результат: Created / Updated / Unchanged
Фото: N
```

При повторе:

```text
Product ID тот же
Дубликатов не создано
```

---

# 38. Full automatic sync — НЕ R8

В R8 НЕ делать:

```text
автоматический обход всех страниц аккаунта;
автоматическое открытие сотен объявлений;
планировщик;
background crawler;
reverse publish;
auto close sold listing;
price sync.
```

Это будет отдельный этап только после доказательства расширения.

---

# 39. Future architecture note

После owner acceptance R8 можно планировать:

```text
Stage06A-R9
Chrome Extension Sequential Own Listings Sync
```

Где расширение будет:

```text
работать только с собственным кабинетом;
последовательно открывать own listings;
передавать карточки;
останавливаться при challenge/access denied.
```

Но НЕ начинать автоматически.

---

# 40. Existing Avito browser code

Не удалять:

```text
noVNC
Xvfb
embedded browser
Playwright parser
```

в рамках R8 без отдельного решения.

Но не использовать их в owner extension probe.

---

# 41. Security scan

Проверить:

```text
cookies permission = absent
debugger permission = absent
proxy permission = absent
nativeMessaging = absent
document.cookie extraction = absent
Avito credential storage = absent
extension token in logs = absent
direct Core call from extension = absent
```

---

# 42. Regression

Обязательно:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
docker compose exec -T inventory-sales-module pytest
docker compose exec -T avito-module pytest
docker compose exec -T repairs-module pytest
pytest admin-shell/tests
```

Плюс extension tests согласно выбранному lightweight runner.

---

# 43. Documentation

Создать:

```text
docs/stage06a_r8_chrome_extension_avito_bridge.md
reports/stage06a_r8_chrome_extension_avito_bridge_report.md
chrome-extension/technoreboot-avito/README.md
```

Обновить:

```text
README.md
logs/2026-08-12.md
```

---

# 44. Git

Expected starting HEAD:

```text
c41c836
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
git commit -m "Add Chrome extension Avito bridge probe"
git push origin main
```

---

# 45. Report

```text
STATUS
ARCHITECTURE_DECISION
OLD_BROWSER_PATH_STATUS
EXTENSION_STRUCTURE
MANIFEST_PERMISSIONS
PAIRING
LOCAL_BRIDGE
TOKEN_STORAGE
EXTENSION_UI
MY_LISTINGS_DISCOVERY
CURRENT_LISTING_EXTRACTION
INGEST_SCHEMA
CORE_IMPORT
PHOTO_IMPORT
IDEMPOTENCY
PRIVACY
SECURITY
EXTENSION_PACKAGE
OWNER_INSTALL_UI
TESTS
REGRESSION
FILES_CHANGED
COMMIT
PUSH
FINAL_GIT_STATUS
OWNER_ONE_ITEM_EXTENSION_PROBE
FINAL_STATUS
```

---

# 46. Definition of Done

R8 готов только если:

```text
ordinary Windows Chrome remains owner browser;
owner manually logs into Avito normally;
extension Manifest V3 created;
extension installable unpacked;
extension downloadable from Technoreboot UI;
pairing works;
extension token stored locally;
no Avito cookies/passwords transferred;
my listings page recognized;
current own listing recognized;
one listing transferred to avito-module;
Core creates/updates Product;
ProductExternalListing linked by Avito ID;
photos imported;
repeat transfer idempotent;
no duplicate Product;
no duplicate photos;
no stealth/evasion;
no Playwright/noVNC used for owner R8 probe;
all regressions PASS;
commit pushed;
git clean.
```

---

# 47. Final status

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE06A_R8_CHROME_EXTENSION_BRIDGE_READY_FOR_OWNER_ONE_ITEM_PROBE

OWNER_EXTENSION_INSTALL_REQUIRED: true
OWNER_ONE_ITEM_EXTENSION_PROBE_REQUIRED: true
AUTOMATIC_ACCOUNT_SYNC_NOT_YET_AUTHORIZED: true
FULL_ACCOUNT_IMPORT_NOT_YET_AUTHORIZED: true
DO_NOT_START_STAGE06A_R9_WITHOUT_OWNER_ACCEPTANCE: true
DO_NOT_START_STAGE06B_REVERSE_SYNC_WITHOUT_OWNER_ACCEPTANCE: true
```
