# PROMPT — Техноребут / Stage06A Avito Authenticated Catalog Bootstrap

## Роль

Ты senior solution architect, FastAPI engineer, Playwright engineer, Docker engineer, data-integration engineer и release QA проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Нужно НЕ делать публичный сайт.

Предыдущий prompt:

```text
TECHNOREBOOT_STAGE06A_PUBLIC_SITE_CATALOG_FOUNDATION_PROMPT.md
```

считать отменённым владельцем и НЕ выполнять.

Новый Stage06A:

```text
Stage06A — авторизованный импорт собственных объявлений Avito в основной каталог Техноребут
```

На этом этапе реализовать только направление:

```text
Avito -> Техноребут
```

Обратную публикацию и закрытие объявлений пока только архитектурно подготовить, но НЕ реализовывать.

---

# 1. Бизнес-цель

У компании есть 2–3 собственных аккаунта Avito с уже созданными объявлениями.

Нужно:

```text
1. Авторизоваться в каждом аккаунте через обычный браузер.
2. Сохранить браузерную сессию локально.
3. Открывать только собственные объявления аккаунта.
4. Получить полный список собственных объявлений.
5. Для каждого объявления получить уникальный Avito ID и URL.
6. Открыть карточку объявления.
7. Забрать название.
8. Забрать цену.
9. Забрать описание.
10. Забрать категорию.
11. Забрать все доступные характеристики.
12. Забрать фотографии.
13. Забрать текущий удалённый статус объявления.
14. Создать/обновить соответствующий Product в Core.
15. Сохранить устойчивую связь Product <-> Avito listing.
16. Повторный импорт не должен создавать дубликаты.
```

Главная задача Stage06A:

```text
наполнить основной каталог Техноребут существующими собственными объявлениями Avito.
```

---

# 2. Ключевая архитектурная идея

Не строить анонимный массовый scraper Avito.

Использовать:

```text
авторизованные браузерные профили;
только собственные аккаунты;
только собственные объявления;
обычный Chromium;
Playwright;
ручную авторизацию владельцем.
```

Общая схема:

```text
Owner browser
    |
    | управление импортом
    v
avito-module UI
    |
    +-----------------------------+
    |                             |
    v                             v
Avito browser profile A      Avito browser profile B
persistent session           persistent session
    |                             |
    +-------------+---------------+
                  |
                  v
          Playwright importer
                  |
                  v
             Core API
                  |
          +-------+-------+
          |               |
          v               v
      Product data     Core Storage
                        photos
```

---

# 3. Важно: существующий avito-module

В проекте уже существует:

```text
avito-module
```

и ранее реализовывался Avito parser/normalizer.

Сначала провести полный аудит:

```text
avito-module/app
avito-module/tests
существующий parser
normalizer
storage/import code
Core Avito-card contract
Stage03A/Stage03B docs/reports
```

Максимально переиспользовать существующий код.

Запрещено:

```text
создать второй независимый Avito module;
сломать старые Avito tests;
создать параллельную несовместимую модель данных;
копировать parser без необходимости.
```

---

# 4. Official API audit first

Перед браузерной реализацией выполнить технический аудит доступного официального Avito API для наших аккаунтов.

Проверить, доступно ли официальным API получить:

```text
список собственных объявлений;
ID объявления;
URL;
статус;
описание;
характеристики;
фотографии.
```

Правило выбора:

```text
если официальный API реально предоставляет нужные данные
для наших аккаунтов — использовать API там, где он полностью покрывает задачу;

Playwright использовать для отсутствующих возможностей
и для авторизованного просмотра собственных карточек.
```

Не строить искусственно браузерный scraper там, где официальный поддерживаемый API уже решает задачу надёжнее.

В отчёте обязательно:

```text
OFFICIAL_API_AUDIT
AVAILABLE_METHODS
MISSING_METHODS
CHOSEN_IMPORT_PATH
```

Не останавливать Stage06A только потому, что API ограничен, если собственные объявления доступны через авторизованный браузер.

---

# 5. Никакого обхода защит

Запрещено реализовывать:

```text
CAPTCHA bypass;
stealth plugins;
fingerprint spoofing;
proxy rotation;
массовую смену IP;
обход rate limits;
anti-bot evasion;
автоматический обход SMS/2FA;
извлечение пароля из браузера;
хранение паролей Avito в БД;
кражу cookies;
парсинг чужих аккаунтов.
```

Если Avito показывает:

```text
CAPTCHA;
SMS;
2FA;
подтверждение входа;
security challenge;
```

импорт должен:

```text
остановиться;
показать статус «Требуется ручное подтверждение»;
дать владельцу открыть браузер;
после ручного прохождения продолжить импорт.
```

---

# 6. Browser profiles

Нужно поддержать минимум:

```text
3 независимых профиля Avito.
```

Каждый профиль:

```text
имеет внутренний UUID;
имеет понятное имя;
имеет отдельное persistent browser storage;
имеет отдельную сессию;
не смешивает cookies с другим аккаунтом.
```

Пример:

```text
Avito — Основной
Avito — Ноутбуки
Avito — Оргтехника
```

Не хардкодить эти имена.

---

# 7. Auth storage

Пароль Avito НЕ хранить.

Хранить только browser session data:

```text
cookies;
localStorage;
session browser profile;
прочие данные Chromium, необходимые для сохранения авторизации.
```

Хранилище:

```text
Docker named volume / отдельный persistent volume на профиль.
```

Не коммитить:

```text
cookies;
storage_state;
Chromium profiles;
tokens;
session files.
```

Добавить соответствующие `.gitignore` правила.

---

# 8. Встроенный простой браузер

Нужен простой способ владельцу открыть браузер соответствующего профиля и войти вручную.

Предпочтительная Docker-реализация:

```text
Chromium + Xvfb + x11vnc/noVNC
```

Browser UI доступен только локально.

Пример:

```text
http://localhost:8061
```

или отдельный локальный порт на выбранный browser worker.

Не публиковать browser UI наружу.

В docker-compose bind:

```text
127.0.0.1:<port>:<port>
```

---

# 9. Avito module UI

Расширить существующий avito-module.

Добавить страницу:

```text
Аккаунты Avito
```

Для каждого профиля показывать:

```text
Имя
Статус авторизации
Последняя проверка
Последний импорт
Количество найденных объявлений
Количество импортированных
Количество обновлённых
Количество ошибок
```

Кнопки:

```text
Открыть браузер
Проверить авторизацию
Импортировать объявления
Посмотреть последний импорт
```

---

# 10. Account authorization check

Добавить безопасную проверку:

```text
авторизован;
не авторизован;
требуется подтверждение;
не удалось определить.
```

Не определять авторизацию только по наличию cookie.

Проверить фактическое состояние страницы аккаунта.

---

# 11. Import workflow

Импорт должен идти этапами.

## Step 1

Открыть:

```text
собственную страницу «Мои объявления»
```

или эквивалентный текущий интерфейс Avito.

## Step 2

Получить все объявления текущего аккаунта.

Учитывать пагинацию / lazy loading.

## Step 3

Для каждой записи получить минимум:

```text
external_item_id
external_url
remote_status
title
```

## Step 4

Открыть каждую собственную карточку.

## Step 5

Получить полные данные.

## Step 6

Скачать/передать фотографии в Core Storage.

## Step 7

Сделать idempotent upsert в Core.

## Step 8

Сохранить результаты import run.

---

# 12. Уникальный внешний ID

Это фундамент будущей синхронизации.

Для каждого объявления обязательно сохранить:

```text
marketplace = avito
external_item_id
external_url
account_id
product_id
```

Нельзя связывать товары только:

```text
по названию;
по цене;
по URL без ID;
по фотографии.
```

Основной ключ:

```text
Avito external item ID.
```

Если Avito ID глобально уникален — использовать:

```text
(marketplace, external_item_id)
```

Если аудит покажет, что ID нужно квалифицировать аккаунтом:

```text
(marketplace, account_id, external_item_id)
```

Решение задокументировать.

---

# 13. Core external listing model

В Core создать additive модель связи.

Предпочтительно:

```text
ProductExternalListing
```

Поля минимум:

```text
id
product_id
marketplace
external_account_key
external_item_id
external_url
remote_status
source_title
last_seen_at
last_imported_at
created_at
updated_at
```

Полезно сразу заложить:

```text
last_pushed_at nullable
sync_state
sync_error nullable
```

но Stage06A не реализует push.

Unique constraint обязателен.

---

# 14. Avito account metadata

Core может хранить только НЕсекретную метаинформацию:

```text
external_account_key
display_name
marketplace_user_id, если удалось надёжно определить
```

Auth cookies/session остаются только в avito-module browser volume.

Core не должен хранить:

```text
пароль;
cookies;
OAuth secret;
browser storage state.
```

---

# 15. Product import mapping

Нужно взять существующий Product model и существующий Avito normalization contract.

Импортировать максимально возможные данные:

```text
название;
категория;
бренд;
модель;
цена;
описание;
состояние;
характеристики;
комплектация;
все поддерживаемые product attributes;
фотографии.
```

Не выбрасывать характеристику только потому, что для неё пока нет отдельной колонки.

Для неизвестных Avito параметров использовать существующее структурированное поле характеристик/JSON, если оно есть.

Если его нет:

```text
добавить минимальное additive JSON поле source_attributes
```

только после аудита текущей Product schema.

---

# 16. Raw source snapshot

Для диагностики импорта желательно сохранять нормализованный source snapshot объявления.

Не хранить полный HTML страницы.

Допустимо:

```text
raw_source_data JSON
```

с:

```text
external ID;
title;
price;
description;
attributes;
photo URLs;
remote status;
source timestamps;
```

Не сохранять:

```text
cookies;
session tokens;
личные сообщения;
платёжные данные;
секретные данные аккаунта.
```

---

# 17. Photos

Для каждого объявления получить все фотографии товара.

Процесс:

```text
Avito browser/API
   ↓
photo bytes
   ↓
Core Storage API
   ↓
Product photo records
```

Запрещено:

```text
site hotlink как единственное постоянное хранение;
прямое сохранение фото в avito-module как источник истины;
копирование в случайную папку;
прямая запись в Core storage filesystem.
```

Core Storage остаётся владельцем фотографий.

---

# 18. Photo idempotency

Повторный импорт не должен создавать бесконечные дубликаты фотографий.

Использовать один или комбинацию:

```text
source_photo_id;
source URL normalization;
content SHA256;
position/order.
```

Предпочтительно:

```text
content SHA256 + source metadata.
```

Если фотография не изменилась:

```text
не сохранять второй раз.
```

Если набор фото изменился:

```text
синхронизировать актуальный набор безопасно.
```

На Stage06A не удалять физически старые файлы без необходимости.

---

# 19. Remote statuses

Нужно сохранять фактический удалённый статус Avito.

Минимально различать то, что реально обнаруживается:

```text
active
inactive
sold/closed
archived
unknown
```

Не выдумывать mapping.

Сначала посмотреть реальные состояния аккаунтов.

Хранить:

```text
remote_status_raw
```

и нормализованный:

```text
remote_status
```

если полезно.

---

# 20. Что делать с закрытыми объявлениями при первичном импорте

На первом массовом импорте пользователь хочет «вылить всю информацию с Avito».

Поэтому предусмотреть режимы:

```text
Активные
Архив/закрытые
Все собственные объявления
```

По умолчанию первый bootstrap желательно сделать:

```text
Все доступные собственные объявления
```

Но НЕ превращать автоматически закрытое объявление в доступный товар на складе.

Remote status и локальный Product availability — разные понятия.

---

# 21. Product creation rule

Если external listing ещё не связан:

```text
создать новый Product;
создать ProductExternalListing.
```

Если связь уже существует:

```text
обновить существующий Product;
обновить external link metadata.
```

Нельзя:

```text
создавать новый Product при каждом импорте.
```

---

# 22. Existing local products

Если в Core уже существует товар, визуально похожий на Avito listing, но external link отсутствует:

```text
не объединять автоматически по эвристике.
```

На Stage06A:

```text
создать новый импортированный Product
ИЛИ
пометить как возможный дубль для ручного связывания,
если проект уже имеет безопасный механизм.
```

Не делать fuzzy auto-merge.

---

# 23. Source ownership

На Stage06A Avito является источником первичного наполнения импортированных товаров.

Сохранить происхождение:

```text
source_origin = avito
```

или эквивалент в external link.

Это нужно для будущей двусторонней синхронизации.

---

# 24. Future reverse synchronization foundation

Stage06A НЕ публикует объявления обратно.

Но структура должна позволить Stage06B позже:

```text
Core Product -> Avito create/update
Sale -> Avito close
Core price -> Avito price update
Core description -> Avito description update
```

Поэтому обязательны:

```text
stable external ID;
account binding;
external URL;
last imported timestamp;
last pushed timestamp placeholder;
sync state.
```

Не реализовывать outbound actions сейчас.

---

# 25. Sale future sync

На Stage06A только подготовить связь.

Не делать:

```text
автозакрытие Avito при продаже;
webhooks;
outbound status update.
```

Но ProductExternalListing должен позволить однозначно найти объявление товара после продажи.

---

# 26. Import runs

Создать журнал импортов:

```text
AvitoImportRun
```

или runtime storage в avito-module, если Core не должен владеть operational log.

Поля:

```text
id
account_key
started_at
finished_at
status
listings_found
created_count
updated_count
skipped_count
error_count
last_error
```

Не смешивать import run log с Product data.

---

# 27. Per-item import result

Для диагностики показывать:

```text
external_item_id
title
result
product_id
photos_imported
warning/error
```

Статусы:

```text
created
updated
unchanged
skipped
failed
```

---

# 28. Retry

Если один товар не импортировался:

```text
не падать всем batch;
зафиксировать error;
продолжить остальные объявления.
```

После batch дать:

```text
Повторить ошибки
```

Не создавать дубль при retry.

---

# 29. Rate and navigation policy

Работать последовательно или с очень небольшой concurrency.

Предпочтительно:

```text
1–2 страницы одновременно максимум.
```

Не устраивать агрессивный параллельный обход.

Не пытаться имитировать антибот-стратегии.

---

# 30. DOM parsing strategy

Avito UI может меняться.

Не строить parser только на:

```text
случайных CSS class names.
```

Предпочитать:

```text
семантические data attributes;
aria labels;
структурированные данные страницы;
JSON-LD;
стабильные ссылки;
видимый текст с локализованным fallback.
```

Сделать extraction layer отдельно от orchestration.

Пример:

```text
AvitoPageExtractor
AvitoListingNormalizer
AvitoImportService
```

---

# 31. Existing static parser compatibility

Существующий Stage03A static HTML parser/normalizer не удалять.

Новая система может:

```text
получить HTML/structured data через Playwright
        ↓
передать существующему parser/normalizer
```

если это возможно.

Цель:

```text
не дублировать нормализацию.
```

---

# 32. Core API contracts

Предпочтительно добавить явный import endpoint для доверенного локального avito-module:

```text
POST /api/integrations/avito/import-item
```

или переиспользовать существующий Stage03B Avito import endpoint.

Сначала провести аудит.

Запрещено:

```text
avito-module -> direct DB.
```

Core должен выполнять:

```text
Product create/update;
external link upsert;
photo ownership;
validation;
audit.
```

---

# 33. Auditing

Core audit events минимум:

```text
avito.product_imported
avito.product_updated
avito.external_link_created
avito.external_link_updated
```

Payload:

```text
product_id;
external_item_id;
account_key;
changed_fields;
```

Не записывать cookies, tokens или полный HTML.

---

# 34. Browser worker health

Добавить health/status:

```text
browser process running
profile available
authorization state
current import state
```

При падении Chromium:

```text
перезапуск worker;
session volume сохраняется.
```

---

# 35. Docker

Переиспользовать существующий `avito-module`.

При необходимости добавить companion service:

```text
avito-browser
```

или:

```text
avito-browser-worker
```

Отдельный browser container допустим.

Пример локальных портов:

```text
8020 — avito-module
127.0.0.1:8061 — noVNC browser
```

Не занимать существующие порты проекта.

---

# 36. Multi-account

UI должен позволять выбрать конкретный профиль:

```text
Аккаунт A
Аккаунт B
Аккаунт C
```

Импорт запускается:

```text
для одного выбранного аккаунта;
или последовательно для всех авторизованных.
```

Не запускать три интерактивных браузера одновременно без необходимости.

---

# 37. Import scope UI

Перед запуском:

```text
Аккаунт
Область:
  Активные
  Закрытые/архив
  Все
```

Кнопка:

```text
Начать импорт
```

На первом этапе достаточно синхронного job с progress state либо простого background worker.

Не строить сложную очередь задач.

---

# 38. Progress

Показывать:

```text
Найдено: N
Обработано: X / N
Создано: N
Обновлено: N
Без изменений: N
Ошибок: N
```

---

# 39. Manual stop

Добавить:

```text
Остановить импорт
```

Остановка должна быть graceful:

```text
текущий item завершить;
новые items не начинать;
run отметить stopped.
```

---

# 40. Database safety

До Core migration:

```text
backup live DB;
SHA256;
counts;
schema snapshot.
```

Каталог:

```text
C:\tbootit-data-backups\stage06a-avito-bootstrap\<timestamp>\
```

Migration:

```text
additive;
idempotent;
никаких DROP;
никаких DELETE;
никакого пересоздания products.
```

---

# 41. Live DB protection

Automated tests должны использовать isolated DB.

До и после тестов сравнить:

```text
LIVE_DB_SHA256;
products;
product_photos;
sales;
repairs;
external listings;
audit.
```

Все значения идентичны.

Runtime bootstrap import, наоборот, осознанно добавляет реальные Product records после owner запуска.

Не запускать массовый реальный импорт автоматически в unit tests.

---

# 42. Test account policy

Automated tests НЕ должны логиниться в реальный Avito.

Использовать:

```text
saved sanitized HTML fixtures;
mock pages;
mock Playwright adapter;
test Core;
temporary browser profile.
```

Live account проверка — только отдельный owner/runtime check.

---

# 43. Avito module tests

Создать минимум:

```text
avito-module/tests/test_browser_profiles.py
avito-module/tests/test_auth_state.py
avito-module/tests/test_my_listings_discovery.py
avito-module/tests/test_listing_page_extract.py
avito-module/tests/test_import_idempotency.py
avito-module/tests/test_multi_account_isolation.py
avito-module/tests/test_photo_import.py
avito-module/tests/test_import_retry.py
avito-module/tests/test_no_secrets_in_git.py
avito-module/tests/test_no_direct_db_access.py
```

Покрыть:

```text
profiles separated;
0 сохраняется где применимо;
account cookies do not mix;
own-listing discovery;
external ID;
URL;
title;
price;
description;
attributes;
photos;
status;
duplicate import;
retry;
partial failure;
challenge state;
manual auth required.
```

---

# 44. Core tests

Создать/обновить:

```text
core/tests/test_avito_external_listing.py
core/tests/test_avito_import_upsert.py
core/tests/test_avito_import_photos.py
core/tests/test_avito_import_idempotency.py
```

Проверить:

```text
new external listing -> Product created;
same external ID -> same Product updated;
unique link;
different accounts isolated;
unknown attributes preserved;
photo duplicate prevention;
audit;
no stock/sales mutation.
```

---

# 45. Runtime owner validation — one account first

Перед массовым импортом обязательно сделать probe.

## Step A

Владелец открывает browser profile.

## Step B

Ручной login.

## Step C

Проверка:

```text
AUTHORIZED
```

## Step D

Импортировать только:

```text
1 объявление
```

## Step E

В Core проверить:

```text
Product;
external ID;
URL;
price;
description;
attributes;
photos.
```

Только после owner подтверждения:

```text
разрешить полный batch аккаунта.
```

---

# 46. Runtime owner validation — full account

После probe:

```text
получить весь список;
зафиксировать listings_found;
импортировать;
проверить created/updated/errors.
```

Сделать повторный import.

Ожидаемо:

```text
новые дубли Product = 0;
новые дубли external link = 0;
неизменённые товары распознаны;
фото не дублируются.
```

---

# 47. Second and third accounts

После успешного первого аккаунта:

```text
авторизовать профиль B;
импортировать;
проверить account isolation.
```

Затем профиль C при необходимости.

Не смешивать объявления аккаунтов.

---

# 48. Existing product visibility

После bootstrap в основном каталоге/Inventory существующие импортированные товары должны быть видны через текущий интерфейс остатков.

Не создавать отдельный «Avito каталог» как второй источник истины.

Основной каталог:

```text
Core Product
```

Avito — только внешний источник и канал синхронизации.

---

# 49. Future architecture note

В документации Stage06A явно зафиксировать будущий Stage06B:

```text
двусторонняя синхронизация Core <-> Avito
```

Будущие действия:

```text
create listing
update title
update description
update price
update photos
close listing on local sale
import remote status changes
conflict policy
```

Но никакой outbound логики в Stage06A.

---

# 50. Prompt discovery

Найти только:

```text
TECHNOREBOOT_STAGE06A_AVITO_AUTHENTICATED_CATALOG_BOOTSTRAP_PROMPT.md
```

Искать:

```text
C:\Users\Apc\Downloads
C:\tbootit\.agents\received_prompts
C:\tbootit
```

Скопировать в:

```text
C:\tbootit\.agents\received_prompts\
```

В отчёте:

```text
PROMPT_SEARCH_DONE
PROMPT_USED
PROMPT_SOURCE
PROMPT_LOCAL_COPY
PROMPT_SHA256
```

---

# 51. Preflight

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

Ожидаемый стартовый HEAD:

```text
74376c6
```

Если отличается — указать фактический.

---

# 52. Existing Avito audit

Перед кодом вывести в report:

```text
EXISTING_AVITO_MODULE_STRUCTURE
EXISTING_STAGE03_PARSER
EXISTING_NORMALIZER
EXISTING_CORE_IMPORT_ENDPOINT
EXISTING_PRODUCT_AVITO_FIELDS
EXISTING_PHOTO_CONTRACT
REUSE_PLAN
```

Никакого rewrite-before-audit.

---

# 53. Full automated tests

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
docker compose exec -T inventory-sales-module pytest
docker compose exec -T avito-module pytest
docker compose exec -T repairs-module pytest
```

Если добавлен browser worker test container:

```powershell
docker compose run --rm avito-browser-worker pytest
```

или эквивалент.

---

# 54. Safety scans

```powershell
git grep -n -I "create_engine\|SessionLocal\|sqlite\|technoreboot.db\|data/db\|sqlalchemy\|SELECT .* FROM\|INSERT INTO\|UPDATE .* SET\|DELETE FROM" -- avito-module
```

Ожидаемо:

```text
нет прямого DB access.
```

Секреты:

```powershell
git grep -n -I "cookie\|authorization:\|bearer \|password\|storage_state" -- avito-module . ':!*.md' ':!tests/fixtures/*'
```

Классифицировать matches.

Никаких реальных secrets.

Tracked runtime:

```powershell
git ls-files | Select-String -Pattern "Cookies|Local Storage|storage_state|SingletonCookie|Default/Network|avito-profile|user-data-dir|\.sqlite|technoreboot\.db"
```

Ожидаемо:

```text
0 secret/runtime browser profile files.
```

---

# 55. Documentation

Создать:

```text
docs/stage06a_avito_authenticated_catalog_bootstrap.md
reports/stage06a_avito_authenticated_catalog_bootstrap_report.md
```

Обновить:

```text
README.md
logs/2026-08-11.md
```

Report sections:

```text
# Stage06A Avito Authenticated Catalog Bootstrap Report

## STATUS
## OWNER_SCOPE
## CANCELED_PUBLIC_SITE_STAGE
## PROMPT_DISCOVERY
## PREFLIGHT
## EXISTING_AVITO_AUDIT
## OFFICIAL_API_AUDIT
## CHOSEN_IMPORT_ARCHITECTURE
## BROWSER_WORKER
## ACCOUNT_PROFILES
## AUTH_SESSION_STORAGE
## SECURITY_CHALLENGE_POLICY
## MY_LISTINGS_DISCOVERY
## LISTING_EXTRACTION
## NORMALIZATION_REUSE
## EXTERNAL_ID_CONTRACT
## CORE_EXTERNAL_LINK_MODEL
## PRODUCT_UPSERT
## ATTRIBUTES
## PHOTOS
## PHOTO_IDEMPOTENCY
## REMOTE_STATUS
## IMPORT_RUNS
## RETRY
## MULTI_ACCOUNT_ISOLATION
## FUTURE_REVERSE_SYNC_FOUNDATION
## CORE_TESTS
## AVITO_TESTS
## OTHER_REGRESSION_TESTS
## LIVE_DB_TEST_ISOLATION
## SAFETY_SCANS
## OWNER_ONE_ITEM_PROBE
## OWNER_FULL_ACCOUNT_IMPORT
## FILES_CHANGED
## COMMIT
## PUSH
## FINAL_GIT_STATUS
## OWNER_CHECK_GUIDE
## FINAL_STATUS
```

---

# 56. Git

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

Добавлять только реально изменённые файлы.

Возможные зоны:

```text
core/app/models.py
core/app/schemas.py
core/app/routers/...
core/app/services/...
core/tests/...

avito-module/app/...
avito-module/tests/...
avito-module/Dockerfile
avito-module/requirements.txt

docker-compose.yml
.gitignore

docs/stage06a_avito_authenticated_catalog_bootstrap.md
reports/stage06a_avito_authenticated_catalog_bootstrap_report.md
.agents/received_prompts/TECHNOREBOOT_STAGE06A_AVITO_AUTHENTICATED_CATALOG_BOOTSTRAP_PROMPT.md
README.md
logs/2026-08-11.md
```

Коммит:

```powershell
git commit -m "Add authenticated Avito catalog import"
git push origin main
```

---

# 57. Definition of Done — implementation

Implementation-ready только если:

```text
старый Stage06A site prompt не выполнялся;
существующий avito-module переиспользован;
official API audited;
browser profiles работают;
минимум 3 профиля поддерживаются;
пароли не хранятся;
browser sessions persistent;
profiles isolated;
manual login работает;
challenge/CAPTCHA требует ручного вмешательства;
список собственных объявлений определяется;
external ID извлекается;
URL извлекается;
title извлекается;
price извлекается;
description извлекается;
attributes извлекаются;
photos извлекаются;
remote status извлекается;
ProductExternalListing или эквивалент существует;
Product upsert идемпотентный;
photos идемпотентные;
повторный import не создаёт Product duplicates;
нет direct DB access из avito-module;
нет secret files в Git;
Core safe tests PASS;
Inventory PASS;
Avito PASS;
Repairs PASS;
live DB не меняется от automated tests;
migration additive/idempotent;
targeted commit;
push;
clean Git.
```

---

# 58. Definition of Done — owner gate

Stage06A НЕ считается окончательно принятым после automated tests.

Сначала обязательно:

```text
OWNER_ONE_ITEM_PROBE_REQUIRED: true
```

Порядок:

```text
1. Владелец авторизует один Avito профиль.
2. Импортируется ровно одно реальное собственное объявление.
3. Владелец проверяет Product.
4. Владелец проверяет все фото.
5. Владелец проверяет цену.
6. Владелец проверяет описание.
7. Владелец проверяет характеристики.
8. Владелец подтверждает.
9. Только после этого запускается полный импорт аккаунта.
```

---

# 59. Owner check guide

```text
1. Открыть «Аккаунты Avito».
2. Создать профиль «Основной».
3. Нажать «Открыть браузер».
4. Вручную войти в свой Avito.
5. Закрыть/оставить браузер.
6. Нажать «Проверить авторизацию».
7. Получить статус «Авторизован».
8. Запустить пробный импорт одного объявления.
9. Открыть созданный Product в Техноребут.
10. Сверить Avito ID.
11. Сверить ссылку.
12. Сверить название.
13. Сверить цену.
14. Сверить описание.
15. Сверить все характеристики.
16. Сверить фотографии и порядок.
17. Повторить импорт этого же объявления.
18. Убедиться, что дубль товара не появился.
19. После принятия запустить весь аккаунт.
20. Повторить полный импорт и убедиться, что дублей нет.
```

---

# 60. Final status

После автоматизированной реализации:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE06A_AVITO_AUTHENTICATED_CATALOG_BOOTSTRAP_READY_FOR_OWNER_PROBE

OWNER_ONE_ITEM_PROBE_REQUIRED: true
OWNER_FULL_IMPORT_ACCEPTANCE_REQUIRED: true
DO_NOT_START_STAGE06B_REVERSE_SYNC_WITHOUT_OWNER_ACCEPTANCE: true
```

Если browser/API архитектура не позволяет надёжно получить собственные объявления:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE06A_AVITO_AUTHENTICATED_CATALOG_BOOTSTRAP_BLOCKED

BLOCKERS:
...
OWNER_DECISION_REQUIRED: true
```
