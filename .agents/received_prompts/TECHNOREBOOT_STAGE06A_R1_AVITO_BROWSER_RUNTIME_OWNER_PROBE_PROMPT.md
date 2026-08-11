# PROMPT — Техноребут / Stage06A-R1 Avito Browser Runtime, Source Origin Fix and One-Item Probe

## Роль

Ты senior FastAPI engineer, Playwright/Docker runtime engineer, integration auditor и release QA проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Это НЕ новый функциональный этап.

Нужно исправить и довести Stage06A до состояния, когда владелец реально может:

```text
открыть авторизованный браузер;
войти в один свой Avito-аккаунт;
проверить авторизацию;
импортировать ровно одно своё объявление;
сверить результат в Core.
```

Stage06B reverse sync НЕ начинать.

---

# 1. Причина R1

Автоматическая реализация Stage06A прошла тесты, но отчёт оставил runtime/architecture blockers.

## Blocker A — Product.source_origin default

В отчёте указано:

```text
Product.source_origin default = "avito"
```

Это неверный глобальный default.

Если обычный товар создаётся вручную, через JSON, Inventory или другой будущий импорт и поле не передано, он не должен автоматически становиться Avito-товаром.

Нужно:

```text
default = "manual"
```

или:

```text
default = null
```

в зависимости от существующего product contract.

Avito import endpoint должен ЯВНО устанавливать:

```text
source_origin = "avito"
```

Не использовать глобальный default `avito`.

---

# 2. Blocker B — browser runtime не доказан

В build report видно установку Python package:

```text
playwright==1.41.2
```

но не доказано наличие:

```text
Chromium binary;
Playwright browser dependencies;
Xvfb;
x11vnc;
noVNC;
websockify;
реально работающего localhost:8061.
```

Сам Python package Playwright недостаточен для интерактивного Chromium runtime.

Нужно проверить фактический Dockerfile и runtime.

---

# 3. Blocker C — docker-compose/noVNC не подтверждён

Stage06A требует локальный browser UI.

В отчёте UI содержит ссылку:

```text
http://localhost:8061
```

но необходимо доказать, что этот адрес реально обслуживается контейнером и открывает браузер.

Если docker-compose не содержит browser worker/noVNC service:

```text
добавить его.
```

Либо реализовать Chromium/Xvfb/noVNC внутри avito-module, если это проще и устойчиво.

Обязательное правило:

```text
bind only 127.0.0.1
```

Пример:

```yaml
ports:
  - "127.0.0.1:8061:6080"
```

Не публиковать browser UI на 0.0.0.0.

---

# 4. Blocker D — hardcoded profile names

В исходном prompt было:

```text
не хардкодить имена аккаунтов.
```

В отчёте реализованы:

```text
Main
Laptops
Office
```

как автоматически создаваемые профили.

Исправить.

Нужно поддержать:

```text
до 3 профилей;
профиль создаёт владелец;
display_name вводится вручную;
UUID/key создаётся системой.
```

Допустимо иметь:

```text
Профиль 1
Профиль 2
Профиль 3
```

как UI placeholders, но не реальные сохранённые account names.

Не создавать автоматически бизнес-смысловые имена.

---

# 5. Blocker E — Official API audit должен быть явным

В коде существует:

```text
avito-module/app/official_api.py
```

Но перед owner probe нужно вывести в отчёт точный результат:

```text
OFFICIAL_API_AUDIT
AVAILABLE_METHODS
MISSING_METHODS
AUTH_REQUIREMENTS
CHOSEN_IMPORT_PATH
```

Не писать общими словами.

Нужно перечислить:

```text
что именно официальный API покрывает;
что именно не покрывает;
почему для конкретных недостающих данных используется browser path.
```

Не требуется внедрять API ради API.

---

# 6. Blocker F — Stage06A не принят без реального one-item probe

Automated fixtures/mock tests НЕ заменяют:

```text
OWNER_ONE_ITEM_PROBE
```

После R1 финальный статус может быть только:

```text
READY_FOR_OWNER_PROBE
```

а не:

```text
COMPLETED
OWNER_ACCEPTED
FULL_IMPORT_READY
```

---

# 7. Browser runtime architecture

Выбрать один рабочий вариант.

## Вариант A — отдельный avito-browser service

Предпочтительно:

```text
avito-module
    |
    v
avito-browser
Chromium + Xvfb + noVNC
persistent user-data-dir
```

Плюсы:

```text
чёткая изоляция;
browser dependencies не раздувают API container;
удобное сохранение профилей.
```

## Вариант B — всё в avito-module

Допустимо только если:

```text
Chromium;
Xvfb;
noVNC;
Playwright;
persistent profile storage
```

реально запускаются и доказаны runtime.

Не создавать лишнюю микросервисную сложность.

---

# 8. Persistent profiles

Профили должны храниться вне container writable layer.

Например:

```text
C:\tbootit\data\avito-module\profiles\<profile_uuid>\
```

смонтировано в контейнер.

Или named volume.

Требования:

```text
container recreate не теряет login;
профиль A не видит cookies B;
профиль B не видит cookies A;
профиль не попадает в Git.
```

---

# 9. Profile CRUD — минимально

Страница:

```text
http://localhost:8020/accounts
```

Добавить:

```text
Создать профиль
Имя профиля
```

Для каждого:

```text
Переименовать — optional;
Удалить — только если нет активного import job;
Открыть браузер;
Проверить авторизацию;
Импортировать 1 объявление;
Импортировать выбранную область — пока owner gate.
```

На Stage06A-R1 достаточно:

```text
create;
list;
open;
auth check.
```

Не делать сложную account management систему.

---

# 10. Browser launch

При нажатии:

```text
Открыть браузер
```

система должна:

```text
выбрать конкретный profile UUID;
запустить/подключить Chromium с его user-data-dir;
открыть Avito;
дать owner обычный визуальный browser UI.
```

Не использовать headless mode для manual login.

---

# 11. Login policy

Owner вручную вводит:

```text
логин;
пароль;
SMS;
2FA;
CAPTCHA.
```

Система НЕ получает эти значения через собственную форму.

Не логировать:

```text
password;
SMS code;
cookie values;
Authorization headers.
```

---

# 12. Auth check runtime

После ручного логина:

```text
Проверить авторизацию
```

должно реально открыть аккаунт через тот же profile и определить:

```text
authorized
unauthorized
challenge_required
unknown
```

Не считать профиль `authorized` только потому, что каталог cookies непустой.

---

# 13. Playwright installation proof

В Docker build/runtime доказать:

```text
playwright Python package installed;
Chromium executable exists;
Playwright can launch it;
dependencies installed.
```

Допустимые способы:

```dockerfile
RUN playwright install --with-deps chromium
```

или официальный Playwright image совместимой версии.

В отчёте:

```text
PLAYWRIGHT_VERSION
CHROMIUM_EXECUTABLE
CHROMIUM_LAUNCH_TEST
```

---

# 14. noVNC proof

Доказать:

```text
GET/open http://127.0.0.1:8061
```

и наличие UI.

Не ограничиваться тем, что ссылка вставлена в HTML.

В отчёте:

```text
NOVNC_SERVICE_RUNNING
NOVNC_BIND_ADDRESS
NOVNC_HTTP_STATUS
BROWSER_VISIBLE
```

---

# 15. Core source_origin correction

Провести аудит всех способов создания Product:

```text
manual CRUD;
JSON import;
Avito import;
sales-related flows;
tests.
```

Исправить default так, чтобы:

```text
manual Product -> manual/null;
JSON Product -> json/manual согласно текущему контракту;
Avito Product -> avito;
```

Existing imported Avito products должны сохранить:

```text
source_origin=avito.
```

Не менять существующие реальные товары массово без доказательства происхождения.

Если в live DB уже появились Stage06A test products:

```text
перечислить IDs;
не считать их реальными owner imports;
не удалять без owner approval.
```

---

# 16. External listing unique contract audit

Текущий индекс:

```text
(marketplace, external_item_id)
```

Перед owner probe подтвердить, что Avito item ID глобально уникален между аккаунтами.

Если нет доказательства:

```text
использовать
(marketplace, external_account_key, external_item_id)
```

Если official/public contract подтверждает глобальную уникальность item ID:

```text
оставить текущий индекс;
зафиксировать основание в report.
```

Не менять индекс без необходимости.

---

# 17. One-item import mode

Добавить явный owner-safe режим:

```text
Импортировать 1 объявление
```

Это НЕ должен быть скрытый debug endpoint.

UI:

```text
Аккаунт
Область: Активные
Лимит: 1
Кнопка: Пробный импорт
```

Можно реализовать фиксированный limit=1.

Не позволять случайно запустить full account до owner acceptance.

---

# 18. Full import gate

До owner approval one-item probe:

```text
кнопку полного импорта сделать disabled;
или требовать явный owner flag/config;
или UI показывает «Доступно после пробного импорта».
```

Не запускать full import автоматически.

---

# 19. One-item selection

Для пробного импорта предпочтительно:

```text
первое активное собственное объявление
```

или дать owner выбрать из discovered list.

Минимальный Stage06A-R1:

```text
discover own listings;
показать первые N;
owner выбирает одно;
нажимает «Импортировать».
```

Это безопаснее, чем случайно импортировать первое.

---

# 20. Preview before import

Добавить простой preview выбранного listing:

```text
Avito ID
title
price
URL
remote status
количество фото
```

Кнопка:

```text
Импортировать это объявление
```

Не требуется полноценный diff UI.

---

# 21. Import correctness

После выбранного listing Core должен получить:

```text
external_item_id
external_account_key
external_url
title
price
description
attributes
photo data
remote status
```

И создать:

```text
Product
ProductExternalListing
ProductPhoto[]
```

---

# 22. One-item idempotency

Owner должен иметь возможность повторно нажать импорт того же объявления.

Ожидаемо:

```text
Product ID тот же;
external listing row тот же;
Product count не увеличился;
photo count не растёт для неизменённых фото.
```

---

# 23. Photo correctness

Проверить не только count.

Для пробного listing:

```text
сравнить порядок фото;
content hash;
размер downloaded file > 0;
Core photo endpoint реально открывается.
```

---

# 24. NoVNC/security

Browser UI:

```text
только localhost;
не публиковать во внешний network;
не сохранять VNC password в Git;
если VNC password нужен — runtime secret/env вне Git.
```

Для локальной разработки допустим loopback-only no-auth noVNC только если сервис физически bind на 127.0.0.1.

В отчёте явно указать.

---

# 25. Automated tests

Добавить/обновить:

```text
avito-module/tests/test_browser_runtime_config.py
avito-module/tests/test_profile_crud.py
avito-module/tests/test_profile_persistence.py
avito-module/tests/test_one_item_probe_gate.py
avito-module/tests/test_no_full_import_before_probe.py

core/tests/test_product_source_origin.py
```

Проверить:

```text
Product default != avito;
Avito import explicitly sets avito;
profile names owner-defined;
profiles isolated;
browser storage persistent path;
localhost-only browser port config;
one-item probe exists;
full import gated;
same item import idempotent.
```

---

# 26. Regression tests

Обязательно:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
docker compose exec -T inventory-sales-module pytest
docker compose exec -T avito-module pytest
docker compose exec -T repairs-module pytest
```

---

# 27. Runtime technical smoke before owner login

Без реального логина доказать:

```text
avito-module /accounts opens;
browser service healthy;
noVNC opens;
Chromium starts;
new empty profile opens Avito;
container recreate;
same profile directory still exists.
```

Не вводить реальные credentials агентом.

---

# 28. Owner probe instructions

После автоматизированного R1 агент должен ОСТАНОВИТЬСЯ.

Owner выполняет вручную:

```text
1. http://localhost:8020/accounts
2. Создать профиль с произвольным именем.
3. Открыть браузер.
4. Вручную войти в Avito.
5. При необходимости пройти SMS/2FA/CAPTCHA.
6. Вернуться в /accounts.
7. Проверить авторизацию.
8. Получить authorized.
9. Открыть список собственных объявлений.
10. Выбрать одно.
11. Посмотреть preview.
12. Импортировать это одно объявление.
13. Открыть Product в Техноребут.
14. Сверить данные.
15. Повторить import того же объявления.
16. Убедиться, что дублей нет.
```

---

# 29. Что owner сверяет

Обязательно:

```text
Product ID
Avito external item ID
Avito URL
account/profile binding
title
price
description
category
brand
model
other attributes
remote status
photo count
photo order
photo content
```

---

# 30. Full import запрещён до acceptance

После технического R1 final status:

```text
OWNER_ONE_ITEM_PROBE_REQUIRED: true
FULL_ACCOUNT_IMPORT_NOT_YET_AUTHORIZED: true
```

Даже если кнопка full import реализована, owner не должен запускать её до успешной проверки одного item.

---

# 31. Safety scans

Direct DB:

```powershell
git grep -n -I "create_engine\|SessionLocal\|sqlite3\|technoreboot.db\|data/db\|sqlalchemy" -- avito-module/app
```

Tracked sessions:

```powershell
git ls-files | Select-String -Pattern "Cookies|Local Storage|storage_state|SingletonCookie|user-data-dir|profiles/|browser_data|\.sqlite"
```

Ports/config:

```powershell
docker compose config
```

Проверить, что browser/noVNC порт:

```text
127.0.0.1 only.
```

---

# 32. Documentation

Создать:

```text
docs/stage06a_r1_avito_browser_runtime_owner_probe.md
reports/stage06a_r1_avito_browser_runtime_owner_probe_report.md
```

Обновить:

```text
README.md
logs/2026-08-11.md
```

Report sections:

```text
# Stage06A-R1 Avito Browser Runtime and Owner Probe Report

## STATUS
## WHY_R1_REQUIRED
## PREFLIGHT
## SOURCE_ORIGIN_BEFORE
## SOURCE_ORIGIN_AFTER
## EXISTING_LIVE_STAGE06A_PRODUCTS
## PROFILE_NAME_FIX
## PROFILE_STORAGE
## DOCKER_BROWSER_ARCHITECTURE
## PLAYWRIGHT_RUNTIME
## CHROMIUM_PROOF
## NOVNC_PROOF
## LOCALHOST_BIND_PROOF
## AUTH_CHECK_IMPLEMENTATION
## OFFICIAL_API_AUDIT
## EXTERNAL_ID_UNIQUENESS_AUDIT
## ONE_ITEM_PROBE_UI
## FULL_IMPORT_GATE
## CORE_TESTS
## AVITO_TESTS
## REGRESSION_TESTS
## LIVE_DB_TEST_ISOLATION
## SAFETY_SCANS
## OWNER_PROBE_GUIDE
## FILES_CHANGED
## COMMIT
## PUSH
## FINAL_GIT_STATUS
## FINAL_STATUS
```

---

# 33. Git

Expected starting HEAD:

```text
5c534f3
```

или фактический потомок, если есть новые owner-approved commits.

Только targeted add.

Не использовать:

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

Коммит:

```powershell
git commit -m "Make Avito browser import ready for owner probe"
git push origin main
```

---

# 34. Definition of Done

R1 готов только если:

```text
Product default source_origin больше не avito;
Avito import явно ставит source_origin=avito;
hardcoded Main/Laptops/Office устранены;
owner может создать именованный профиль;
profile storage persistent;
Chromium реально установлен;
Chromium реально запускается;
noVNC реально открывается;
browser порт localhost-only;
manual login возможен;
auth check использует реальный profile;
official API audit документирован;
external ID uniqueness decision документирован;
one-item selection/preview работает;
one-item import работает;
full import gated;
repeat one-item import не создаёт дубль;
Core tests PASS;
Inventory tests PASS;
Avito tests PASS;
Repairs tests PASS;
live DB не меняется от automated tests;
sessions/cookies не попадают в Git;
targeted commit;
push;
clean Git.
```

---

# 35. Final status

После автоматизированной доработки:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE06A_R1_AVITO_BROWSER_RUNTIME_READY_FOR_OWNER_ONE_ITEM_PROBE

OWNER_ONE_ITEM_PROBE_REQUIRED: true
FULL_ACCOUNT_IMPORT_NOT_YET_AUTHORIZED: true
DO_NOT_START_STAGE06B_REVERSE_SYNC_WITHOUT_OWNER_ACCEPTANCE: true
```

Если browser/noVNC не удаётся реально поднять:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE06A_R1_AVITO_BROWSER_RUNTIME_BLOCKED

BLOCKERS:
...
OWNER_DECISION_REQUIRED: true
```
