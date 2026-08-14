# TECHNOREBOOT — Avito Extension Photo Quality R1: Select Best Variant by Actual Image Dimensions

Репозиторий:

```powershell
C:\tbootit
```

Дата:

```text
2026-08-14
```

Это отдельный hotfix текущего рабочего Chrome extension.

Проектный этап:

```text
Stage06A-R9-R1
TECHNOREBOOT_STAGE06A_R9_R1_ATTRIBUTE_PROVENANCE_EXTENSION_SCOPE_AUDIT_PROMPT.md
```

ОСТАЁТСЯ НА ПАУЗЕ до завершения этого hotfix.

НЕ начинать:
- R9-R1;
- R10;
- mass import;
- reverse sync;
- Stage06B.

---

# 1. РЕАЛЬНЫЙ OWNER BUG

Текущий extension:

```text
передаёт ВЕРНОЕ количество физических фотографий;
дубликатов по количеству больше нет.
```

Но Owner обнаружил новый дефект качества:

```text
фото 1 → high quality
фото 2 → low quality
фото 3 → high quality
фото 4 → иногда low quality
...
```

То есть:

```text
ONE_REAL_PHOTO_ONE_SELECTED_VARIANT = mostly true
```

но:

```text
SELECTED_VARIANT_IS_BEST_QUALITY = false
```

Ключевой момент:

```text
низкое качество выбирается НЕ ВСЕГДА,
а только для некоторых фотографий.
```

Следовательно, проблема сейчас НЕ в количестве фотографий и НЕ обязательно в canonical identity.

Главная зона расследования:

```text
quality ranking / best-variant selection
```

---

# 2. ГЛАВНАЯ ГИПОТЕЗА, КОТОРУЮ НУЖНО ПРОВЕРИТЬ

В предыдущих шагах качество определялось через URL-pattern / Avito suffix/token, например:

```text
La1
La2
La3
La4
dimension path
direct/original URL priority
```

Это могло оказаться неверным универсальным правилом.

НЕЛЬЗЯ считать:

```text
La4 всегда лучше La2
La2 всегда лучше La1
direct URL всегда high-res
первый URL всегда лучший
последний URL всегда лучший
```

без фактического подтверждения.

Нужно проверить реальные размеры изображений.

---

# 3. ЦЕЛЬ HOTFIX

Для КАЖДОЙ физической фотографии объявления:

```text
collect all real published variants
→ group by canonical physical photo identity
→ determine actual quality of every candidate
→ select candidate with maximum real image resolution
→ send exactly one URL
```

Ожидаемо:

```text
1 real Avito photo
=
1 Technoreboot photo
=
best actually available Avito image variant
```

---

# 4. ВАЖНО: НЕ ЛОМАТЬ УЖЕ ИСПРАВЛЕННОЕ

Сохранить:

```text
правильное количество фотографий;
canonical photo identity;
cross-source dedupe;
порядок галереи;
main photo first;
server timeout fix;
robust non-JSON error handling;
dynamic popup version;
plugin-only Avito UI;
backend photo reconciliation.
```

Не переписывать весь photo pipeline.

---

# 5. СНАЧАЛА GIT/RUNTIME AUDIT

```powershell
Set-Location C:\tbootit

git status --short --untracked-files=all
git branch --show-current
git rev-parse HEAD
git log --oneline -12
git diff --name-status
git diff --stat
docker compose ps
```

Зафиксировать текущую extension version из:

```text
chrome-extension/technoreboot-avito/manifest.json
```

Не предполагать номер по старым отчётам.

---

# 6. НАЙТИ CURRENT QUALITY SELECTION CODE

Найти функции типа:

```text
getImageQualityScore
selectBestVariant
getCanonicalAvitoImageIdentity
getImageKey
collectPhotoCandidates
extractPhotos
```

или фактические эквиваленты.

Задокументировать текущую формулу выбора:

```text
CURRENT_QUALITY_RANKING_RULE = ...
```

---

# 7. ДОКАЗАТЬ ROOT CAUSE НА НЕСКОЛЬКИХ ФОТО

Нужно получить минимум:

```text
1 фото, где выбирается high корректно;
1 фото, где выбирается low ошибочно;
лучше 2-3 ошибочных примера.
```

Для каждой физической фотографии собрать все candidate URL.

Таблица:

```text
PHOTO_IDENTITY
CANDIDATE_INDEX
SOURCE
URL_PATTERN
CURRENT_SCORE
KNOWN_DECLARED_WIDTH
KNOWN_DECLARED_HEIGHT
ACTUAL_WIDTH
ACTUAL_HEIGHT
ACTUAL_PIXEL_AREA
SELECTED_BY_CURRENT_CODE
SHOULD_BE_SELECTED
```

---

# 8. ACTUAL DIMENSIONS — ГЛАВНЫЙ КРИТЕРИЙ

Если candidate image URL доступен:

получить реальное изображение и определить:

```text
actual_width
actual_height
```

по decoded image metadata.

Использовать:

```text
pixel_area = width * height
```

как основной объективный критерий качества.

При равной площади:

```text
prefer greater width/height;
then stable source priority;
then deterministic URL order.
```

Не использовать file byte size как главный критерий.

---

# 9. НЕ ИСПОЛЬЗОВАТЬ OCR

OCR не нужен.

Нужно только:

```text
image dimensions / image metadata
```

---

# 10. ВАЖНО: ГДЕ ОПРЕДЕЛЯТЬ ACTUAL DIMENSIONS

Исследовать архитектуру.

Chrome extension не должен бездумно скачивать десятки огромных изображений только ради сравнения, если данные о dimensions уже есть в:

```text
srcset
DOM attributes
JSON-LD
embedded page state
Avito image metadata
URL metadata
```

Приоритет определения качества:

```text
A. explicit width/height published by Avito page
B. reliable srcset descriptor (e.g. 1280w)
C. actual decoded image dimensions
D. proven URL quality token only as fallback
```

Но для этого hotfix нужно ДОКАЗАТЬ, что selected URL соответствует actual best image.

---

# 11. ЕСЛИ PAGE ALREADY PUBLISHES DIMENSIONS

Если Avito отдаёт:

```text
srcset="... 208w, ... 640w, ... 1280w"
```

или JSON с:

```text
width
height
```

нужно сохранять dimensions вместе с candidate с момента extraction.

Не терять quality metadata при merge/dedupe.

Candidate structure желательно:

```text
{
  url,
  identity,
  source,
  width,
  height,
  qualityEvidence,
  galleryIndex
}
```

или архитектурный эквивалент.

---

# 12. ЕСЛИ URL TOKEN QUALITY НЕМОНОТОНЕН

Если выяснится:

```text
La4 не всегда high
La1 не всегда low
```

убрать этот ranking как primary criterion.

Можно оставить:

```text
token heuristic only as fallback
```

если dimensions неизвестны.

Но в отчёте должно быть явно:

```text
AVITO_TOKEN_QUALITY_ORDER_RELIABLE: true/false
```

---

# 13. BEST VARIANT SELECTION CONTRACT

Для каждого identity:

```text
variants = all candidates of this physical photo
best = max(variants, real_quality)
```

Финальный payload:

```text
exactly one candidate per identity
```

И:

```text
selected candidate must have maximum known pixel area
```

если dimensions доступны.

---

# 14. LOW-RES GUARD

Добавить safety guard:

Если одна identity имеет:

```text
candidate 1280x960
candidate 208x156
```

финальный selection НЕ МОЖЕТ выбрать:

```text
208x156
```

Независимо от source order.

---

# 15. НЕ УДАЛЯТЬ ФОТО, ЕСЛИ ДОСТУПЕН ТОЛЬКО LOW

Если конкретная реальная фотография имеет только один опубликованный low-res candidate:

```text
не терять фотографию.
```

Правило:

```text
BEST AVAILABLE
```

а не:

```text
ONLY HIGH-RES OR NOTHING.
```

---

# 16. ПОРЯДОК ГАЛЕРЕИ

Quality selection не должен менять logical photo order.

Если:

```text
photo A gallery index 0
photo B gallery index 1
photo C gallery index 2
```

после выбора high variants остаётся:

```text
A, B, C
```

а не сортировка по quality/URL.

---

# 17. MAIN PHOTO

Первая физическая фотография Avito должна оставаться:

```text
sort_order = 0
```

и тоже использовать лучший доступный variant.

---

# 18. НОВЫЕ/СТАРЫЕ ФОТО В BACKEND

Backend reconciliation уже отвечает за удаление старых obsolete Avito variants.

Не менять его без доказанной необходимости.

Этот bug относится к тому, какой URL приходит как canonical selected variant.

Но проверить:

```text
backend не заменяет high incoming URL на stale low URL.
```

Если backend участвует — доказать.

---

# 19. ПРОВЕРИТЬ FIRST QUALITY DEGRADATION LAYER

Сравнить:

```text
extension selected candidate
extension final payload URL
Avito module received URL
Core downloaded image dimensions
stored file dimensions
```

Для одного ошибочного фото.

Ответить:

```text
QUALITY_FIRST_DEGRADES_AT:
- extension selection
- extension payload
- backend download redirect
- Core storage
- other
```

Не предполагать.

---

# 20. HTTP REDIRECT / CDN CHECK

Особенно проверить:

```text
selected high URL
→ HTTP redirect?
→ final CDN URL?
→ actual returned image dimensions?
```

Возможна ситуация:

```text
URL выглядит high
но сервер Avito возвращает thumbnail.
```

Поэтому для ошибочного примера проверить final HTTP response.

---

# 21. TESTS — QUALITY RANKING

Добавить минимум:

```text
test_selects_largest_actual_dimensions_regardless_of_candidate_order
test_high_then_low_returns_high
test_low_then_high_returns_high
test_three_variants_returns_largest
test_same_identity_different_sources_returns_largest
test_low_only_photo_is_preserved
test_quality_selection_does_not_change_gallery_order
test_main_photo_best_variant_stays_first
```

---

# 22. REGRESSION — INTERMITTENT OWNER PATTERN

Обязательный тест:

```text
photo1: high + low
photo2: low + high
photo3: medium + high + low
photo4: only high
```

Expected:

```text
photo1 high
photo2 high
photo3 high
photo4 high
```

То есть качество не должно зависеть от:

```text
candidate order
source order
odd/even photo position
DOM order
JSON-LD order
```

---

# 23. REAL AVITO PATTERN FIXTURES

Использовать реальные URL patterns, найденные в текущем листинге/сохранённых source data.

Не придумывать только synthetic:

```text
high.jpg / low.jpg
```

Хотя synthetic tests тоже можно оставить.

Нужен regression fixture максимально близкий к фактическому Avito CDN pattern.

---

# 24. DIAGNOSTIC ASSERTION

В development/test code желательно иметь проверку:

Для identity с известными dimensions:

```text
selected_area == max(candidate_areas)
```

Это должно падать тестом, если выбор снова деградирует.

---

# 25. EXTENSION VERSION

Так как runtime extension меняется:

```text
bump patch version от ФАКТИЧЕСКОЙ текущей версии.
```

Например:

```text
0.1.11 → 0.1.12
```

только если текущая manifest version действительно 0.1.11.

Не предполагать.

Popup version остаётся dynamic:

```javascript
chrome.runtime.getManifest().version
```

Никакого hardcoded version label.

---

# 26. VERSION PACKAGING

Обновить необходимые build/package metadata:

```text
manifest.json
build_extension_zip.py
Admin Shell download artifact/config
dist ZIP
admin-shell ZIP
download tests
README current version
```

Owner-visible popup version НЕ писать вручную.

---

# 27. OWNER DOWNLOAD

Проверить:

```text
http://localhost:8011/avito/extension
```

показывает корректную downloadable version.

И:

```text
GET /avito/extension/download
→ HTTP 200
→ ZIP manifest version == current version
```

---

# 28. PLUGIN-ONLY UI НЕ ЛОМАТЬ

Cleanup уже выполнен.

Сохранить:

```text
в UI только «Расширение Avito»
старые sync/import/parser owner controls не возвращать.
```

---

# 29. PRODUCT DETAIL BUG FIX НЕ ЛОМАТЬ

Сохранить миграцию:

```text
products.avito_category_id
```

и working product detail route.

Проверить:

```text
GET /inventory/products/58 → 200
```

---

# 30. R9/R9-R1 НЕ ТРОГАТЬ

Не продолжать attribute provenance audit.

Не менять R9 model без необходимости для photo bug.

---

# 31. FULL REGRESSION

Запустить:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
docker compose exec -T inventory-sales-module pytest
docker compose exec -T avito-module pytest
docker compose exec -T repairs-module pytest
pytest admin-shell/tests
pytest chrome-extension/technoreboot-avito/tests
```

Фактические counts.

---

# 32. RUNTIME

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
GET /inventory/products/58 → 200
GET /avito/extension → 200
GET /avito/extension/download → 200
```

---

# 33. LIVE OWNER DATA SAFETY

Agent НЕ должен:

```text
выполнять реальный импорт listing 8313765236
изменять Product 58 через Avito
удалять фотографии Product 58 вручную
```

Read-only audit разрешён.

Owner выполнит реальный импорт после отчёта.

---

# 34. DOCUMENTATION

Создать:

```text
reports/avito_extension_photo_quality_r1_actual_dimensions_report.md
```

Обновить:

```text
docs/stage06a_r8_extension_photo_import.md
chrome-extension/technoreboot-avito/README.md
logs/2026-08-14.md
```

Сохранить prompt:

```text
.agents/received_prompts/TECHNOREBOOT_AVITO_EXTENSION_PHOTO_QUALITY_R1_ACTUAL_DIMENSIONS_PROMPT.md
```

---

# 35. REPORT STRUCTURE

Обязательно:

```text
STATUS

OWNER_BUG
CURRENT_EXTENSION_VERSION

CURRENT_QUALITY_RANKING_RULE

REAL_GOOD_PHOTO_CANDIDATE_AUDIT
REAL_BAD_PHOTO_CANDIDATE_AUDIT

AVITO_TOKEN_QUALITY_ORDER_RELIABLE

QUALITY_FIRST_DEGRADES_AT
ROOT_CAUSE

NEW_CANDIDATE_QUALITY_MODEL
ACTUAL_DIMENSION_SOURCE
BEST_VARIANT_SELECTION_RULE
LOW_ONLY_FALLBACK
ORDER_PRESERVATION
MAIN_PHOTO_BEHAVIOR

BACKEND_DOWNLOAD_REDIRECT_AUDIT
STORED_DIMENSION_VERIFICATION

EXTENSION_VERSION
ZIP_FILENAME
OWNER_DOWNLOAD_URL

PLUGIN_ONLY_UI_PRESERVED
PRODUCT_DETAIL_ROUTE_PRESERVED
R9_PAUSED

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

# 36. DEFINITION OF DONE

PASS только если:

```text
INTERMITTENT_LOW_RES_ROOT_CAUSE_IDENTIFIED: true
QUALITY_FIRST_DEGRADATION_LAYER_PROVEN: true

BEST_VARIANT_SELECTED_BY_REAL_QUALITY_EVIDENCE: true
CANDIDATE_ORDER_DOES_NOT_AFFECT_QUALITY: true
SOURCE_ORDER_DOES_NOT_AFFECT_QUALITY: true
LOW_RES_NOT_SELECTED_WHEN_HIGHER_RES_EXISTS: true
LOW_ONLY_PHOTO_PRESERVED: true

ONE_REAL_PHOTO_ONE_SELECTED_VARIANT: true
PHOTO_COUNT_PRESERVED: true
GALLERY_ORDER_PRESERVED: true
MAIN_PHOTO_FIRST: true

DYNAMIC_VERSION_DISPLAY_PRESERVED: true
PLUGIN_ONLY_UI_PRESERVED: true
PRODUCT_DETAIL_ROUTE_200: true

OWNER_REAL_IMPORT_PERFORMED_BY_AGENT: false
OWNER_MANUAL_CHECK_REQUIRED: true
R9_R1_STILL_PAUSED: true
```

---

# 37. GIT SAFETY

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

Commit message по фактической причине, например:

```text
Select best Avito photo variant by actual dimensions
```

Push:

```powershell
git push origin main
```

---

# 38. OWNER CHECK GUIDE

После успешного отчёта ОСТАНОВИТЬСЯ.

Owner:

```text
1. Скачать новую extension version.
2. Обновить extension в Chrome.
3. Проверить номер версии в popup.
4. Открыть listing 8313765236.
5. Нажать импорт ОДИН РАЗ.
6. Открыть Product 58.
7. Проверить:
   - количество фото правильное;
   - ВСЕ фотографии хорошего качества;
   - нет ситуации high / low / high / low;
   - low-res не выбран там, где Avito имеет high-res;
   - порядок фото совпадает с Avito.
8. Повторить импорт при необходимости:
   качество/количество не должны деградировать.
```

После OWNER acceptance hotfix:

```text
закончить cleanup acceptance,
затем вернуться к
TECHNOREBOOT_STAGE06A_R9_R1_ATTRIBUTE_PROVENANCE_EXTENSION_SCOPE_AUDIT_PROMPT.md
```

---

# 39. FINAL STATUS

При успехе:

```text
FINAL_STATUS:
TECHNOREBOOT_AVITO_EXTENSION_PHOTO_QUALITY_R1_READY_FOR_OWNER_CHECK

INTERMITTENT_LOW_RES_ROOT_CAUSE_IDENTIFIED: true
QUALITY_FIRST_DEGRADATION_LAYER_PROVEN: true
BEST_VARIANT_SELECTED_BY_REAL_QUALITY_EVIDENCE: true
LOW_RES_NOT_SELECTED_WHEN_HIGHER_RES_EXISTS: true
ONE_REAL_PHOTO_ONE_SELECTED_VARIANT: true
PHOTO_COUNT_PRESERVED: true
GALLERY_ORDER_PRESERVED: true
DYNAMIC_VERSION_DISPLAY_PRESERVED: true
PLUGIN_ONLY_UI_PRESERVED: true
PRODUCT_DETAIL_ROUTE_200: true
OWNER_MANUAL_CHECK_REQUIRED: true
R9_R1_STILL_PAUSED: true
```

Если quality layer не доказан:

```text
FINAL_STATUS:
TECHNOREBOOT_AVITO_EXTENSION_PHOTO_QUALITY_R1_BLOCKED
```

с конкретными blockers.

После отчёта ОСТАНОВИТЬСЯ.
