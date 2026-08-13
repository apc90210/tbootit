# TECHNOREBOOT — Stage06A-R8-R8-R4 Exact Photo Identity Dedup + Manifest-Driven Extension Version

Репозиторий:

```powershell
C:\tbootit
```

Это точечный corrective-stage внутри Stage06A-R8-R8.

НЕ начинать:
- Stage06A-R9
- Stage06B
- любой следующий функциональный этап

Предыдущий статус:

```text
TECHNOREBOOT_STAGE06A_R8_R8_R3_IMPORT_500_FIXED_READY_FOR_OWNER_CHECK
```

OWNER CHECK R8-R8-R3: PARTIAL PASS.

---

# 1. Реальный OWNER результат

После установки extension 0.1.8:

```text
приложение снова работает;
импорт выполняется;
все необходимые фотографии объявления копируются;
```

Но остаются ДВЕ проблемы.

## Проблема A — одна фотография всё ещё импортируется дважды

Owner видит для одного и того же снимка:

```text
1 вариант нормального / высокого качества
+
1 вариант сверхнизкого качества, маленький и размытый
```

Низкокачественную версию импортировать НЕ НУЖНО.

Требование:

```text
ONE_AVITO_REAL_PHOTO = ONE_TECHNOREBOOT_PHOTO
```

и это должна быть:

```text
BEST_REAL_PUBLISHED_VARIANT_ONLY
```

---

## Проблема B — внутри Chrome extension показывается старая версия

При обновлении plugin/extension Owner открывает расширение и видит старую надпись версии.

Это создаёт неопределённость:

```text
какая сборка реально сейчас установлена и активна?
```

Требование:

```text
версия, отображаемая внутри расширения,
ВСЕГДА должна автоматически совпадать с manifest.json version.
```

Нельзя поддерживать version label вручную в нескольких JS/HTML местах.

---

# 2. ЦЕЛЬ R8-R8-R4

Закрыть оба OWNER defect:

## A. Фото

Гарантировать до отправки payload:

```text
для каждой физической фотографии Avito
существует ровно одна canonical media identity
и выбран ровно один лучший variant.
```

## B. Версия расширения

Гарантировать:

```text
popup displayed version
==
chrome.runtime.getManifest().version
==
manifest.json version
==
ZIP manifest version
```

---

# 3. Не считать предыдущую variant dedupe доказанной

Несмотря на тесты R8-R8-R2/R3, реальный OWNER test доказал:

```text
VARIANT_DEDUPLICATION_IN_REAL_AVITO_PAGE = FAILED
```

Поэтому нужно исследовать именно ФАКТИЧЕСКИЕ URL двух версий одного снимка.

Не ограничиваться существующим `getImageKey()` и unit fixtures.

---

# 4. Сначала read-only runtime / git audit

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

# 5. Найти реальные low/high URL pairs

Нужно установить, почему визуально одна фотография получает два разных media identity.

Использовать:

- данные текущего Product 58;
- `source_url`, если он хранится;
- extension extraction diagnostics;
- реальный DOM/page data, если доступен;
- controlled OWNER-compatible diagnostic mechanism.

Для нескольких пар зафиксировать:

```text
LOW_URL
HIGH_URL

LOW_HOST
HIGH_HOST

LOW_PATH
HIGH_PATH

LOW_QUERY
HIGH_QUERY

LOW_DERIVED_KEY
HIGH_DERIVED_KEY

WHY_CURRENT_CODE_TREATS_AS_DIFFERENT
```

Если Product 58 хранит только storage URL без source URL — определить это явно.

---

# 6. Не гадать по filename

Нужно определить устойчивую media identity Avito.

Проверить реальные URL patterns.

Возможные различия одного снимка:

```text
different CDN subdomain
dimension path segment
query params
format variant
thumbnail route vs original route
different wrapper URL
different image extension
same Avito image token/hash at different location in path
```

Нужно найти реальный общий image identifier.

Нельзя дедуплицировать только по:

```text
ширине
высоте
имени файла
порядку
полной строке URL
```

---

# 7. Canonical Avito image identity

Реализовать одну функцию с понятным контрактом, например:

```text
getCanonicalAvitoImageIdentity(url)
```

Она должна:

```text
same physical Avito photo, different size variants
→ SAME identity

different Avito photos
→ DIFFERENT identities
```

Подтвердить это на реальных URL patterns.

Если Avito URL содержит стабильный media/image token/hash — использовать именно его.

Если URL patterns несколько — поддержать их явно и тестируемо.

---

# 8. Final dedupe must happen AFTER all sources are merged

Критически важно.

Если фото собираются из:

```text
JSON-LD
DOM gallery
srcset
script state
```

нельзя дедуплицировать каждый источник отдельно и потом просто concatenation.

Правильный pipeline:

```text
collect candidates from ALL sources
→ normalize
→ derive canonical media identity
→ group across ALL sources
→ choose ONE best variant per identity
→ restore gallery order
→ final payload
```

---

# 9. One identity = one selected variant

После grouping:

```text
group A:
  low
  medium
  high
→ selected: high only

group B:
  low
  high
→ selected: high only
```

В финальном `images`/`photos` массиве не может быть siblings одной identity.

Добавить runtime assertion / development-safe guard:

```text
final identities are unique
```

Если duplicate identity обнаружена после selection — исправлять до payload, не отправлять обе.

---

# 10. Quality selection

Выбирать лучший variant только среди реально опубликованных Avito URLs.

Приоритет:

1. direct original published asset, если доказано, что это original;
2. variant с максимальными опубликованными dimensions;
3. максимальный stable quality source;
4. fallback один URL, если качество нельзя определить.

Низкий variant не отправлять, если существует лучший sibling.

---

# 11. Минимальный quality floor

OWNER явно не хочет сверхмаленькие изображения.

После identity grouping проверить возможность ввести безопасный quality floor ТОЛЬКО как дополнительную защиту.

Например:

```text
если одна identity имеет high + 140x105
→ 140x105 discarded anyway
```

Но:

```text
если у реальной фотографии доступен только один 208x156 source
```

не удалять всю фотографию без отдельного решения.

Главный механизм — identity dedupe, а не слепой фильтр по размеру.

---

# 12. Final payload diagnostics

Добавить безопасную диагностическую статистику, чтобы доказать fix:

```text
candidate_count
unique_identity_count
selected_count
discarded_variant_count
```

Должно быть:

```text
selected_count == unique_identity_count
```

В popup необязательно показывать все технические детали.

В debug/test logs можно.

Не логировать cookies/tokens.

---

# 13. Backend current-state audit

Проверить Product 58 read-only:

```text
current product_photos count
sort_order
storage file size
stored dimensions if obtainable
source provenance if available
```

Определить:

```text
сколько high/low pairs уже накоплено
```

---

# 14. Existing low-res duplicates

Важно: даже если extension начнёт присылать правильный clean set, старые low-res копии могут остаться в Product 58.

Нужно исследовать текущую update semantics.

Требование для импортированных Avito photos:

```text
повторный импорт same listing
→ итоговый Avito photo set должен соответствовать текущему clean payload
```

То есть obsolete low-res Avito variants должны исчезнуть БЕЗ удаления manual/non-Avito photos.

---

# 15. Provenance safety

Если модель умеет достоверно определить:

```text
Avito-imported photo
vs
manual/local photo
```

реализовать reconciliation:

```text
replace/sync only Avito photo subset
```

Если provenance недостаточно:

```text
НЕ удалять фотографии вслепую.
```

В таком случае:
- исправить future imports;
- отчёт должен явно сказать, что existing low-res cleanup требует отдельного безопасного migration/cleanup step.

Но сначала проверить, возможно ли safe reconciliation по существующим данным.

---

# 16. Backend idempotency

Проверить:

```text
clean payload N
first import → N Avito photos
second import → N
third import → N
```

И:

```text
no low/high siblings
```

---

# 17. Version display — единственный source of truth

Сейчас нужно найти все места, где version отображается пользователю.

Проверить:

```text
popup.html
popup.js
content.js
service_worker.js
README
manifest.json
```

и любые другие runtime UI места.

---

# 18. Popup version MUST come from manifest dynamically

В runtime UI использовать:

```javascript
chrome.runtime.getManifest().version
```

или эквивалент Manifest V3 API.

Например:

```text
Техноребут Avito
Версия 0.1.9
```

значение `0.1.9` должно подставляться динамически.

НЕЛЬЗЯ:

```javascript
const VERSION = "0.1.9";
```

для owner-visible label.

НЕЛЬЗЯ вручную писать version в popup HTML.

---

# 19. Version consistency contract

После fix:

```text
chrome.runtime.getManifest().version
==
popup displayed version
```

Всегда.

При будущем изменении:

```text
manifest version 0.1.10
```

popup автоматически показывает:

```text
0.1.10
```

без отдельного изменения JS label.

---

# 20. Новый patch version

Так как extension снова изменяется:

```text
0.1.8 → 0.1.9
```

Но owner-facing version label должен уже быть dynamic.

Обновить только те места, где version является build/package metadata:

```text
manifest.json
build_extension_zip.py
Admin Shell download artifact/config
dist ZIP naming
tests expecting current downloadable version
docs where historical/current version is documented
```

Не дублировать runtime popup version вручную.

---

# 21. Admin Shell extension page

На:

```text
http://localhost:8011/avito/extension
```

тоже желательно исключить лишнее ручное дублирование версии.

Если возможно с существующей архитектурой:

```text
Admin Shell current extension version
берётся из единого server-side constant/config или manifest ZIP
```

Не обязательно читать ZIP на каждый HTTP request.

Но version должна иметь один централизованный build source, а не правиться в 5 местах вручную.

Минимум:
- popup dynamic from manifest — обязательно;
- server download page consistency — протестировать.

---

# 22. Extension cache/update UX

OWNER должен после установки понимать активную версию.

Добавить/сохранить в popup явную строку:

```text
Версия: X.Y.Z
```

полученную динамически.

При открытии popup она должна быть видна сразу.

Не требовать Developer Tools.

---

# 23. Tests — canonical photo identity

Добавить реальные-pattern regression fixtures минимум:

```text
same photo high + low → same identity
same photo different CDN host → same identity if real Avito pattern proves this
same photo thumbnail path + original path → same identity
different real photos → different identity
same dimensions different photos → different identity
```

---

# 24. Tests — final cross-source dedupe

Обязательно:

```text
JSON-LD low + DOM high same photo → one high
DOM low + srcset high same photo → one high
script-state high + thumbnail low same photo → one high
same photo present in all 4 sources → one selected
N real photos with 2 variants each → exactly N selected
```

---

# 25. Explicit OWNER regression test

Добавить тест, отражающий реальный дефект:

```text
test_owner_duplicate_high_and_super_low_variant_collapses_to_one_best_photo
```

или эквивалент.

Тест должен использовать URL structure, максимально близкую к фактической найденной паре.

---

# 26. Tests — version display

Добавить тесты:

```text
popup version is not hardcoded
popup reads chrome.runtime.getManifest().version
manifest version 0.1.9
download ZIP manifest version 0.1.9
```

Если popup code легко тестируется статически — допустимо.

Главное доказать:

```text
changing manifest version alone changes popup displayed version
```

Можно fixture/mock `chrome.runtime.getManifest()`.

---

# 27. No stale runtime version literals

После изменений выполнить поиск по extension runtime files.

Если старые literals:

```text
0.1.6
0.1.7
0.1.8
```

остались в комментариях/history docs — допустимо.

Но в runtime owner-visible UI не должно быть stale version strings.

Зафиксировать audit.

---

# 28. Extension error handling 0.1.8 сохранить

Не сломать уже исправленное:

```text
plain text 500 handling
JSON error handling
timeout handling
no Unexpected token
```

---

# 29. Full regression

Запустить:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
docker compose exec -T inventory-sales-module pytest
docker compose exec -T avito-module pytest
docker compose exec -T repairs-module pytest
pytest admin-shell/tests
pytest chrome-extension/technoreboot-avito/tests
```

Указать ФАКТИЧЕСКИЕ counts.

---

# 30. Runtime proof

Проверить:

```text
docker compose ps
Core health
Avito health
Inventory health
Admin Shell health
```

Extension:

```text
download HTTP 200
ZIP manifest = 0.1.9
```

И automated/runtime proof:

```text
manifest version → popup version = 0.1.9
```

---

# 31. Не выполнять Owner import автоматически

Agent НЕ должен нажимать real import listing 8313765236.

Product 58 не мутировать автоматически.

OWNER снова проверит extension после отчёта.

---

# 32. Documentation

Обновить:

```text
docs/stage06a_r8_extension_photo_import.md
chrome-extension/technoreboot-avito/README.md
```

Создать:

```text
reports/stage06a_r8_r8_r4_exact_photo_identity_and_dynamic_version_report.md
```

Обновить:

```text
logs/2026-08-13.md
```

Сохранить prompt:

```text
.agents/received_prompts/TECHNOREBOOT_STAGE06A_R8_R8_R4_EXACT_PHOTO_IDENTITY_DYNAMIC_VERSION_PROMPT.md
```

---

# 33. Report structure

Обязательно:

```text
STATUS

OWNER_RESULT_R8_R8_R3

REAL_DUPLICATE_PAIR_AUDIT
LOW_HIGH_URL_EXAMPLES
CURRENT_DERIVED_KEYS
ROOT_CAUSE

CANONICAL_MEDIA_IDENTITY
CROSS_SOURCE_GROUPING
BEST_VARIANT_SELECTION
FINAL_PAYLOAD_COUNTS

PRODUCT_58_READ_ONLY_PHOTO_STATE
EXISTING_LOW_RES_RECONCILIATION

VERSION_DISPLAY_OLD_ROOT_CAUSE
OLD_HARDCODED_VERSION_LOCATIONS
NEW_MANIFEST_DRIVEN_VERSION
VERSION_SINGLE_SOURCE_OF_TRUTH

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

# 34. Definition of Done

PASS только если:

```text
REAL_LOW_HIGH_DUPLICATE_ROOT_CAUSE_IDENTIFIED: true
CANONICAL_AVITO_MEDIA_IDENTITY_VERIFIED: true
CROSS_SOURCE_VARIANT_DEDUP_VERIFIED: true
ONE_REAL_PHOTO_ONE_SELECTED_VARIANT: true
SUPER_LOW_VARIANT_EXCLUDED_WHEN_BETTER_EXISTS: true
ALL_REAL_PHOTOS_STILL_IMPORTED: true
PHOTO_ORDER_PRESERVED: true
REPEAT_IMPORT_NO_VARIANT_DUPLICATES: true

POPUP_VERSION_HARDCODE_REMOVED: true
POPUP_VERSION_READS_MANIFEST: true
POPUP_VERSION_EQUALS_MANIFEST_VERSION: true
EXTENSION_VERSION_0_1_9_READY: true

OWNER_REAL_IMPORT_PERFORMED_BY_AGENT: false
OWNER_MANUAL_CHECK_REQUIRED: true
```

---

# 35. Git safety

Перед/после:

```powershell
git status --short --untracked-files=all
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
DROP TABLE
drop_all
mass DELETE
```

Targeted add only.

Commit message:

```text
Fix Avito photo identity and extension version display
```

или точнее по фактическому root cause.

Push:

```powershell
git push origin main
```

---

# 36. OWNER CHECK GUIDE

После успешного отчёта остановиться.

Дать Owner сценарий:

```text
1. Скачать extension 0.1.9.
2. Установить/обновить extension.
3. Сразу открыть popup.
4. Проверить, что внутри явно написано:
   Версия: 0.1.9
5. Открыть listing 8313765236.
6. Нажать импорт ОДИН РАЗ.
7. Проверить Product ID 58.
8. Открыть Product 58.
9. Проверить:
   - все реальные фотографии объявления присутствуют;
   - каждая ровно один раз;
   - сверхмаленьких/размытых дублей нет;
   - остаются только хорошие варианты;
   - порядок нормальный.
10. При повторном импорте количество не должно увеличиться.
```

---

# 37. FINAL STATUS

При успехе:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE06A_R8_R8_R4_EXACT_PHOTO_IDENTITY_DYNAMIC_VERSION_READY_FOR_OWNER_CHECK

REAL_LOW_HIGH_DUPLICATE_ROOT_CAUSE_IDENTIFIED: true
CANONICAL_AVITO_MEDIA_IDENTITY_VERIFIED: true
CROSS_SOURCE_VARIANT_DEDUP_VERIFIED: true
ONE_REAL_PHOTO_ONE_SELECTED_VARIANT: true
SUPER_LOW_VARIANT_EXCLUDED_WHEN_BETTER_EXISTS: true
ALL_REAL_PHOTOS_STILL_IMPORTED: true
REPEAT_IMPORT_NO_VARIANT_DUPLICATES: true

POPUP_VERSION_HARDCODE_REMOVED: true
POPUP_VERSION_READS_MANIFEST: true
POPUP_VERSION_EQUALS_MANIFEST_VERSION: true
EXTENSION_VERSION_0_1_9_READY: true

OWNER_REAL_IMPORT_PERFORMED_BY_AGENT: false
OWNER_MANUAL_CHECK_REQUIRED: true
OWNER_ONE_ITEM_EXTENSION_IMPORT_NOT_YET_FULLY_ACCEPTED: true
FULL_ACCOUNT_IMPORT_NOT_YET_AUTHORIZED: true
DO_NOT_START_STAGE06A_R9_WITHOUT_OWNER_ACCEPTANCE: true
DO_NOT_START_STAGE06B_REVERSE_SYNC_WITHOUT_OWNER_ACCEPTANCE: true
```

Если реальный low/high duplicate identity всё ещё не доказан:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE06A_R8_R8_R4_BLOCKED
```

с конкретными blockers.

После отчёта ОСТАНОВИТЬСЯ.
