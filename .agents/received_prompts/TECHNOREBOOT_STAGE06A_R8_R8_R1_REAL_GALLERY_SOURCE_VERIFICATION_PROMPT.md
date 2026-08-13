# TECHNOREBOOT — Stage06A-R8-R8-R1 Real Avito Gallery Source Verification & Safe Multi-Photo Fix

Репозиторий:

```powershell
C:\tbootit
```

Это corrective stage внутри Stage06A-R8-R8.

НЕ начинать:
- Stage06A-R9
- Stage06B
- любой следующий функциональный этап

Предыдущий отчёт заявил:

```text
TECHNOREBOOT_STAGE06A_R8_R8_AVITO_MULTI_PHOTO_READY_FOR_OWNER_CHECK
extension 0.1.5
multi-photo extraction implemented
1280x960 URL upgrade implemented
474 tests PASS
```

Но R8-R8 пока НЕ принят Owner.

---

# 1. Почему нужен R8-R8-R1

В отчёте R8-R8 есть два критичных несоответствия требованиям prompt.

## Проблема A — high-res URL строится эвристически

Отчёт говорит:

```text
Dimension path tokens
140x105 / 208x156 / 480x360 / 640x480 / 800x600
автоматически заменяются на 1280x960.
```

Но исходный prompt прямо запрещал:

```text
слепо удалять параметры URL
слепо заменять width/height
угадывать CDN path
создавать URL, который случайно работает только на одном объявлении
```

High-res допустим только если URL реально предоставлен самой страницей Avito:
- DOM;
- srcset;
- JSON-LD;
- hydration/page state;
- gallery state;
- другой подтверждённый источник.

Если `1280x960` не найден как реальный source/variant в данных страницы, такую трансформацию нужно удалить.

Главный приоритет:

```text
ALL_PHOTOS > HIGH_RES
```

Все фото в стабильном качестве лучше, чем guessed high-res.

---

## Проблема B — нет доказательства на реальном multi-photo объявлении

Тесты PASS, но отчёт не доказывает, что на реальной странице Avito:

```text
найдено N реальных gallery photos
extension извлекло N
в payload ушло N
Core сохранил N
UI показал N
```

OWNER ещё не должен проверять неподтверждённую сборку.

---

## Проблема C — несоответствие идентичности объявления

В предыдущем accepted owner flow:

```text
Avito ID: 8313765236
Product ID: 58
```

ранее Product 58 фигурировал как:

```text
Игровая приставка Sony PlayStation 4 Slim 500GB CUH-2208A
```

В отчёте R8-R8 тот же Avito ID внезапно назван:

```text
HP Printer M252N
```

Нужно установить фактические данные и исключить stale/copied description.

Никаких изменений Product 58 до выяснения.

---

# 2. Цель R8-R8-R1

Нужно подтвердить фактическую реализацию multi-photo extraction на реальном Avito DOM/page data и привести код к безопасной схеме:

```text
REAL PAGE GALLERY SOURCES
→ ordered unique listing photos
→ stable best-available URL per photo
→ payload N photos
→ existing Core multi-photo pipeline
```

High-res остаётся optional.

Обязательный PASS:

```text
ALL_REAL_GALLERY_PHOTOS_DISCOVERABLE
NO_GUESSED_HIGH_RES_URLS
ORDER_PRESERVED
NON_LISTING_ASSETS_FILTERED
PAYLOAD_CAN_SEND_ALL_PHOTOS
```

---

# 3. Сначала git/read-only state

Перед изменениями:

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

Не затереть unrelated changes.

---

# 4. Аудит текущего v0.1.5 extractor

Проверить фактический код:

```text
chrome-extension/technoreboot-avito/content.js
```

Зафиксировать:

```text
PHOTO_EXTRACTION_FUNCTION
GALLERY_SOURCES
DEDUPLICATION_FUNCTION
QUALITY_SELECTION_FUNCTION
URL_REWRITE_FUNCTION
FILTER_FUNCTION
```

Особо выделить код, который преобразует URL в `1280x960`.

---

# 5. Проверить источник 1280x960

Для каждой логики high-res ответить:

```text
Откуда реально взят 1280x960 URL?
```

Допустимые доказательства:

```text
srcset
data-srcset
data-src
JSON-LD
window/page state
hydration JSON
gallery JSON
picture/source
другая структура, фактически присутствующая на странице
```

Недостаточное доказательство:

```text
URL после ручной замены вернул HTTP 200
```

HTTP 200 не делает guessed URL официально доступным source.

Если `1280x960` строится только заменой размерного токена:

```text
HIGH_RES_METHOD_RELIABLE = false
```

и эту трансформацию удалить.

---

# 6. Best available quality algorithm

Правильный алгоритм:

Для каждого уникального gallery photo:

1. Собрать ВСЕ реальные variants, которые сама страница предоставляет.
2. Если variant содержит достоверные width/height:
   - выбрать variant с наибольшей площадью/шириной.
3. Если dimensions отсутствуют:
   - использовать приоритет источников без выдумывания URL.
4. Если есть только один стабильный URL:
   - использовать его.
5. Ничего не синтезировать из guessed CDN path.

Результат:

```text
bestStableUrl
```

---

# 7. Источник всех фотографий

Проверить реальные gallery sources по приоритету:

```text
1. structured gallery/page state
2. JSON-LD if it contains all listing images
3. gallery DOM
4. srcset/data-srcset/data-src
5. script state
```

Не использовать generic:

```javascript
document.querySelectorAll("img")
```

как основной источник без контекстной фильтрации gallery.

Нужен именно текущий listing gallery.

---

# 8. Реальный listing 8313765236 — identity audit

Без изменения Product 58 установить:

```text
AVITO_ID = 8313765236
CURRENT_PAGE_TITLE if network/page access is available
CURRENT_LISTING_TITLE_SOURCE
PRODUCT_58_TITLE
PRODUCT_58_EXTERNAL_ID
PRODUCT_58_SOURCE_URL
```

Если dev environment не может открыть реальный Avito из-за anti-bot/auth:

```text
не угадывать title;
REPORT: REAL_AVITO_PAGE_DIRECT_ACCESS_BLOCKED
```

И считать предыдущую подпись `HP Printer M252N` недоказанной/stale.

Не менять Product 58 title из-за этого stage.

---

# 9. Реальный page evidence без destructive import

Если возможно получить страницу/DOM объявления в dev environment:

зафиксировать:

```text
REAL_PAGE_GALLERY_COUNT
REAL_PAGE_GALLERY_URLS
REAL_PAGE_UNIQUE_PHOTO_COUNT
REAL_PAGE_SELECTED_URLS
REAL_PAGE_SELECTED_SOURCE_TYPES
```

Не выполнять Core import.

Это read-only extraction proof.

Если прямой доступ невозможен:

подготовить diagnostic mode в extension для OWNER CHECK:

```text
Найдено фотографий: N
Уникальных фотографий: N
К отправке: N
```

и optional debug console data без токенов/cookies:

```text
index
source type
selected URL host/path summary
variant count
```

Не выводить secrets.

---

# 10. Проверка single-photo root cause

R8-R8 должен точно доказать, почему раньше была только одна фотография.

Нужно назвать конкретную причину:

например:

```text
использовался JSON-LD image[0]
querySelector selected active slide only
collector returned first matching source
```

Не писать generic «расширили extractor».

---

# 11. Multi-photo collector requirements

Collector должен возвращать:

```text
0..N ordered unique listing photos
```

Обязательные свойства:

```text
first = main Avito gallery photo
order = Avito order
no duplicates
no avatars
no logos
no recommendations
no ads
no UI icons
no placeholders
```

---

# 12. Dedupe

Не дедуплицировать только по полному URL, потому что одна фотография может иметь несколько resize variants.

Использовать подтверждённый stable identity:

- Avito media/image hash, если он реально присутствует;
- либо нормализованный media identity из source data.

Не объединять разные реальные фотографии.

Добавить тест:

```text
same image, 3 size variants → 1 photo
two different images same dimensions → 2 photos
```

---

# 13. Payload contract audit

Подтвердить:

```text
extension collector returns N
popup/content bridge sends N
avito-module forwards N
Core receives N
```

Не выполнять real Owner import.

Использовать fixtures/tests.

Зафиксировать field name:

```text
images / photos / actual existing contract
```

---

# 14. Existing backend

R8-R7 уже доказал photo backend.

Не переписывать:

```text
product_photos
storage
Core media API
Inventory gallery
Admin Shell media proxy
```

Если backend уже принимает N, оставить.

Изменять только если реальный test докажет ограничение.

---

# 15. Version

Так как v0.1.5 содержит потенциально небезопасную guessed high-res transform, итоговая исправленная сборка должна получить:

```text
0.1.6
```

Обновить:

```text
manifest
popup/version display
README
Admin Shell download page
ZIP builder
dist ZIP
admin-shell ZIP
```

---

# 16. Owner download

Проверить:

```text
http://localhost:8011/avito/extension
http://localhost:8011/avito/extension/download
```

Download:

```text
HTTP 200
ZIP manifest version = 0.1.6
```

---

# 17. Tests

Обязательно покрыть:

```text
zero gallery photos
one gallery photo
multiple gallery photos
gallery order
main photo first
same photo multiple size variants deduped
two different photos same size not deduped
non-listing images filtered
best real variant selected
no guessed 1280x960 URL construction
fallback to stable URL
JSON-LD multiple images
DOM/srcset multiple images
script state multiple images
payload forwards all N
partial failure contract preserved
repeat import no duplicate backend rows
```

Добавить explicit regression test:

```text
test_does_not_synthesize_unpublished_1280x960_url
```

или эквивалент.

---

# 18. Full regression

Запустить:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
docker compose exec -T inventory-sales-module pytest
docker compose exec -T avito-module pytest
docker compose exec -T repairs-module pytest
pytest admin-shell/tests
pytest chrome-extension/technoreboot-avito/tests
```

Указать фактические числа.

---

# 19. Runtime

Проверить:

```text
docker compose ps
Core health
Inventory health
Avito module health
Admin Shell health
extension download HTTP 200
ZIP version 0.1.6
```

---

# 20. Не выполнять Owner import

Agent НЕ должен:

```text
нажимать реальный import
изменять Product 58
создавать новый live product
удалять Product 58
```

Owner check только после отчёта.

---

# 21. Documentation

Обновить:

```text
docs/stage06a_r8_extension_photo_import.md
chrome-extension/technoreboot-avito/README.md
```

Создать:

```text
reports/stage06a_r8_r8_r1_real_gallery_source_verification_report.md
```

Обновить:

```text
logs/2026-08-13.md
```

Сохранить prompt:

```text
.agents/received_prompts/TECHNOREBOOT_STAGE06A_R8_R8_R1_REAL_GALLERY_SOURCE_VERIFICATION_PROMPT.md
```

---

# 22. Report

Отчёт должен содержать:

```text
STATUS

WHY_R8_R8_WAS_NOT_ACCEPTED

CURRENT_V015_AUDIT
SINGLE_PHOTO_OLD_ROOT_CAUSE

HIGH_RES_1280_REWRITE_FOUND
HIGH_RES_1280_REWRITE_REMOVED_OR_PROVEN
HIGH_RES_REAL_SOURCE
BEST_STABLE_QUALITY_ALGORITHM

REAL_LISTING_IDENTITY_AUDIT
PRODUCT_58_IDENTITY
AVITO_8313765236_IDENTITY_STATUS

REAL_PAGE_DIRECT_ACCESS
REAL_PAGE_GALLERY_COUNT
REAL_PAGE_UNIQUE_PHOTO_COUNT
REAL_PAGE_EXTRACTION_EVIDENCE

GALLERY_SOURCES
FILTERING
ORDERING
DEDUPLICATION

PAYLOAD_N_PHOTO_PROOF
BACKEND_N_PHOTO_PROOF

EXTENSION_VERSION
ZIP_FILENAME
OWNER_DOWNLOAD_URL

TESTS
RUNTIME
SAFETY
FILES_CHANGED
COMMIT
PUSH
FINAL_GIT_STATUS

OWNER_CHECK_GUIDE
FINAL_STATUS
```

---

# 23. Definition of Done

PASS только если:

```text
SINGLE_PHOTO_ROOT_CAUSE_IDENTIFIED: true
GUESSED_HIGH_RES_URL_REWRITE_PRESENT: false
ALL_GALLERY_PHOTOS_COLLECTOR_IMPLEMENTED: true
ORDER_PRESERVED: true
NON_LISTING_ASSETS_FILTERED: true
VARIANT_DEDUPLICATION_VERIFIED: true
BEST_STABLE_QUALITY_USED: true
PAYLOAD_MULTI_PHOTO_VERIFIED: true
BACKEND_MULTI_PHOTO_VERIFIED: true
EXTENSION_VERSION_0_1_6_READY: true
OWNER_REAL_IMPORT_PERFORMED_BY_AGENT: false
OWNER_MANUAL_CHECK_REQUIRED: true
```

High-res:

```text
HIGH_RES_RELIABLY_IMPLEMENTED: true/false
```

`false` допустимо.

---

# 24. Git

Targeted add only.

Commit message:

```text
Verify safe Avito multi-photo sources
```

или точнее по фактическому fix.

Push:

```powershell
git push origin main
```

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

---

# 25. FINAL STATUS

При успехе:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE06A_R8_R8_R1_REAL_GALLERY_READY_FOR_OWNER_CHECK

SINGLE_PHOTO_ROOT_CAUSE_IDENTIFIED: true
GUESSED_HIGH_RES_URL_REWRITE_PRESENT: false
ALL_GALLERY_PHOTOS_COLLECTOR_IMPLEMENTED: true
ORDER_PRESERVED: true
NON_LISTING_ASSETS_FILTERED: true
VARIANT_DEDUPLICATION_VERIFIED: true
BEST_STABLE_QUALITY_USED: true
HIGH_RES_RELIABLY_IMPLEMENTED: true/false
PAYLOAD_MULTI_PHOTO_VERIFIED: true
BACKEND_MULTI_PHOTO_VERIFIED: true
EXTENSION_VERSION_0_1_6_READY: true
OWNER_REAL_IMPORT_PERFORMED_BY_AGENT: false
OWNER_MANUAL_CHECK_REQUIRED: true
OWNER_ONE_ITEM_EXTENSION_IMPORT_NOT_YET_FULLY_ACCEPTED: true
FULL_ACCOUNT_IMPORT_NOT_YET_AUTHORIZED: true
DO_NOT_START_STAGE06A_R9_WITHOUT_OWNER_ACCEPTANCE: true
DO_NOT_START_STAGE06B_REVERSE_SYNC_WITHOUT_OWNER_ACCEPTANCE: true
```

Если нельзя доказать безопасный multi-photo collector:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE06A_R8_R8_R1_REAL_GALLERY_BLOCKED
```

с конкретными blockers.

После отчёта ОСТАНОВИТЬСЯ.
