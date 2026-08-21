# TECHNOREBOOT — Stage06A-R9-R3: Fix Real Avito Characteristics Extraction / Transport

Репозиторий:

```powershell
C:\tbootit
```

Контекст:
- Stage06A-R9-R1 V2 технически завершён.
- Stage06A-R9-R2 добавил:
  - ссылку «Открыть объявление на Avito»;
  - отображение structured Avito attributes в карточке товара;
  - synthetic rich-monitor test.
- OWNER CHECK на реальных товарах выявил системный дефект.

Реально проверено Owner:

```text
1. Материнская плата:
   - фотографии передаются;
   - кнопки/ссылка работают;
   - характеристики НЕ передаются.

2. Компьютер / системный блок:
   - фотографии передаются;
   - кнопки/ссылка работают;
   - характеристики НЕ передаются.
```

Следовательно:

```text
R9_R2_OWNER_ACCEPTED = false
REAL_CHARACTERISTICS_FLOW_BROKEN = true
MULTI_CATEGORY_REPRODUCED = true
PHOTO_FLOW_WORKS = true
```

Это отдельный corrective step.

НЕ начинать:
- Stage06A-R10;
- canonical schema discovery;
- reverse sync;
- массовый импорт;
- Stage06B.

---

# 1. ЦЕЛЬ

Найти ПЕРВЫЙ слой, на котором характеристики реального Avito-объявления исчезают, и исправить только этот дефект.

Полная цепочка:

```text
Avito page
→ extraction source
→ extension extractListingData()/extractListingDataMultiPass()
→ listing.characteristics
→ extension POST payload
→ Admin Shell proxy
→ Avito Module
→ Core import endpoint
→ R9 model
→ Product detail API
→ Product detail UI
```

Нельзя гадать.

---

# 2. OWNER FACTS

Зафиксировать:

```text
OWNER_TEST_MOTHERBOARD_FAILED = true
OWNER_TEST_COMPUTER_FAILED = true
PHOTOS_TRANSFER = true
BUTTONS_WORK = true
AVITO_SOURCE_LINK_WORKS = true
REAL_CHARACTERISTICS_VISIBLE_ON_AVITO = true
REAL_CHARACTERISTICS_VISIBLE_IN_TECHNOREBOOT = false
```

Поскольку баг воспроизводится на двух разных категориях, сначала искать общий systemic failure.

---

# 3. GIT/RUNTIME AUDIT

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

Не затирать unrelated changes.

---

# 4. ФАКТИЧЕСКАЯ EXTENSION VERSION

Проверить:

```text
chrome-extension/technoreboot-avito/manifest.json
```

Зафиксировать:

```text
CURRENT_EXTENSION_VERSION
```

Не предполагать номер.

---

# 5. SYNTHETIC TEST НЕ СЧИТАТЬ ДОКАЗАТЕЛЬСТВОМ

Старый synthetic rich-monitor test доказывает только:

```text
если characteristics уже пришли в Core,
Core умеет их сохранить и показать.
```

Он НЕ доказывает:

```text
реальный Avito extractor умеет их извлечь.
```

На этом этапе нужен реальный runtime path audit.

---

# 6. НАЙТИ CURRENT CHARACTERISTICS EXTRACTOR

Найти production code:

```text
extractListingData
extractListingDataMultiPass
extractCharacteristics
extractParameters
parseJsonLd...
embedded state parser
DOM parameter parser
```

Зафиксировать:

```text
CHARACTERISTICS_EXTRACTOR_FILE
CHARACTERISTICS_EXTRACTOR_FUNCTIONS
CURRENT_SELECTORS
CURRENT_STATE_PATHS
CURRENT_FALLBACK_ORDER
```

---

# 7. НАЙТИ ПЕРВЫЙ FAILURE LAYER

Для реального объявления материнской платы ИЛИ компьютера, не меняя сам Avito item, получить diagnostic evidence по этапам.

Минимум:

```text
A. REAL_AVITO_PAGE_HAS_CHARACTERISTICS_COUNT
B. EXTENSION_EXTRACTED_CHARACTERISTICS_COUNT
C. EXTENSION_FINAL_PAYLOAD_CHARACTERISTICS_COUNT
D. AVITO_MODULE_RECEIVED_CHARACTERISTICS_COUNT
E. CORE_RECEIVED_CHARACTERISTICS_COUNT
F. CORE_SAVED_CHARACTERISTICS_COUNT
G. PRODUCT_DETAILS_API_CHARACTERISTICS_COUNT
```

И:

```text
FIRST_FAILURE_LAYER = ...
```

Это обязательный результат.

---

# 8. DIAGNOSTIC MODE В EXTENSION

Если сейчас невозможно увидеть payload до POST, добавить временную/безопасную dev-диагностику:

```javascript
console.debug("[Technoreboot][characteristics]", {...})
```

или helper/test hook.

Логи НЕ должны:
- содержать токены;
- содержать секреты;
- ломать production flow.

В финале debug можно оставить только если он безопасен и уместен, иначе убрать после диагностики.

---

# 9. ПРОВЕРИТЬ РЕАЛЬНУЮ DOM РАЗМЕТКУ AVITO

Ранее код мог полагаться на:

```text
[data-marker="item-params/list"] li
```

Проверить, существует ли этот selector на текущих страницах Avito.

Не предполагать.

Нужно исследовать реальные элементы характеристик для:
- материнской платы;
- компьютера.

Зафиксировать:

```text
MOTHERBOARD_REAL_SELECTOR
COMPUTER_REAL_SELECTOR
SELECTOR_SHARED = true/false
```

---

# 10. ПРОВЕРИТЬ collapsed/expanded characteristics

Avito может прятать часть или все параметры под:

```text
Показать ещё
Все характеристики
Развернуть
```

Проверить:

```text
CHARACTERISTICS_COLLAPSED_BY_DEFAULT
EXPAND_CONTROL_PRESENT
PARAMETERS_IN_DOM_BEFORE_EXPAND
PARAMETERS_IN_DOM_AFTER_EXPAND
```

Если параметры становятся доступны только после раскрытия:
- безопасно раскрыть;
- дождаться DOM hydration;
- собрать;
- не менять страницу необратимо.

---

# 11. ПРОВЕРИТЬ EMBEDDED STATE

Исследовать реальные:

```text
window.__initialData__
__NEXT_DATA__
React state
widgets
```

Найти, где реально лежат параметры текущего item.

Зафиксировать:

```text
STATE_CHARACTERISTICS_AVAILABLE
STATE_PATH
REAL_RAW_FRAGMENT
```

Если embedded state содержит полный набор и надёжнее DOM — использовать его как primary source.

---

# 12. НЕ СОБИРАТЬ ХАРАКТЕРИСТИКИ ИЗ РЕКОМЕНДАЦИЙ

Сохранить isolation:

```text
только текущий item
не recommendations
не seller items
не similar items
не ads
```

Если параметры извлекаются из embedded state:
- ограничить data.item / текущим listing id;
- не делать широкую рекурсивную выборку всей страницы.

---

# 13. ПРОВЕРИТЬ JSON-LD

JSON-LD может:
- не содержать характеристик;
- содержать только name/price/brand;
- содержать урезанный Product.

Не полагаться на JSON-LD как единственный источник.

Зафиксировать:

```text
JSON_LD_CHARACTERISTICS_AVAILABLE
JSON_LD_CHARACTERISTICS_COUNT
```

---

# 14. НОРМАЛИЗАЦИЯ NAME/VALUE

Реальный extractor должен поддерживать разные структуры:

```text
Название: Значение
dt/dd
li with label/value spans
structured object
array of {name, value}
```

Но нормализацию делать только после доказанного источника.

Финальный contract:

```json
"characteristics": {
  "Название параметра": "Значение"
}
```

или текущий фактический contract, если он уже richer.

---

# 15. НЕ ТЕРЯТЬ MULTI-VALUE

Если параметр имеет несколько значений:

```text
Интерфейсы: HDMI, DisplayPort, USB-C
```

не обрезать до первого.

Сохранить:
```text
полный human-readable value
```

и raw.

---

# 16. BRAND / MODEL

Проверить, не исчезают ли вместе с characteristics:

```text
brand
model
```

Если brand/model извлекаются из characteristics, баг может объяснять и их отсутствие.

Зафиксировать:

```text
BRAND_BEFORE_FIX
MODEL_BEFORE_FIX
BRAND_AFTER_FIX
MODEL_AFTER_FIX
```

---

# 17. ПРОВЕРИТЬ EXTENSION FINAL PAYLOAD

Перед POST для реального item payload должен содержать:

```json
{
  "listing": {
    "category": "...",
    "brand": "...",
    "model": "...",
    "characteristics": {
      "...": "..."
    }
  }
}
```

Зафиксировать:
```text
EXTENSION_PAYLOAD_HAS_CHARACTERISTICS = true/false
EXTENSION_PAYLOAD_CHARACTERISTICS_COUNT
```

---

# 18. ПРОВЕРИТЬ AVITO MODULE CONTRACT

Если extension payload уже правильный, проверить:

```text
Pydantic/schema/dataclass
request parsing
serialization
field naming
```

Особенно возможные несовпадения:

```text
characteristics
parameters
params
attributes
source_attributes
```

Зафиксировать:
```text
AVITO_MODULE_INPUT_FIELD
AVITO_MODULE_OUTPUT_FIELD
```

---

# 19. ПРОВЕРИТЬ CORE IMPORT CONTRACT

Если Avito Module получает характеристики, проверить Core:

```text
POST /api/integrations/avito/import-item
```

или фактический endpoint.

Зафиксировать:
```text
CORE_INPUT_CHARACTERISTICS_COUNT
CORE_SCHEMA_FIELD
CORE_MAPPING_FUNCTION
```

---

# 20. ПРОВЕРИТЬ R9 SAVE

После import:

```text
AvitoCategory
AvitoAttributeDefinition
ProductAvitoAttributeValue
```

Зафиксировать:
```text
SAVED_DEFINITION_COUNT
SAVED_VALUE_COUNT
```

Если 0 при непустом payload — исправлять Core binding.

---

# 21. ПРОВЕРИТЬ PRODUCT DETAILS API

После save:

```text
GET /api/products/{id}/details
```

должен вернуть полный набор Avito characteristics.

Зафиксировать:
```text
DETAILS_API_ATTRIBUTE_COUNT
```

---

# 22. ПРОВЕРИТЬ UI

Если API отдаёт характеристики, а UI пишет:

```text
Характеристики Avito не импортированы
```

исправить template mapping.

Но backend/UI не трогать, если первый failure раньше.

---

# 23. ИСПРАВЛЕНИЕ — МИНИМАЛЬНОЕ

Исправлять только proven failure layer.

Не переписывать:
- photo extraction;
- photo quality;
- SHA-256 dedupe;
- source link;
- plugin pairing;
- batch import;
- R9 model без необходимости.

---

# 24. REALISTIC TEST FIXTURES

Добавить regression fixtures на реальные DOM/state patterns текущего Avito.

Нужно минимум 2 fixtures:

```text
motherboard-like real structure
computer-like real structure
```

Они должны отражать реально увиденную структуру страницы, а не придуманный HTML.

Можно обезличить значения, но структура должна быть реальной.

---

# 25. ОБЯЗАТЕЛЬНЫЕ TESTS

Добавить минимум:

```text
test_realistic_motherboard_characteristics_extracted
test_realistic_computer_characteristics_extracted
test_characteristics_survive_final_extension_payload
test_characteristics_survive_avito_module_transport
test_characteristics_saved_to_r9_model
test_characteristics_returned_in_product_details
test_product_ui_displays_characteristics
```

Если failure только в extension — transport/backend tests всё равно должны подтверждать существующий контракт.

---

# 26. CHARACTERISTICS COUNT CONTRACT

Для каждого realistic fixture:

```text
expected_count > 1
actual_count == expected_count
```

Не принимать тест, где expected_count = 1.

Нам нужен rich-attribute scenario.

---

# 27. НЕ ЛОМАТЬ PHOTO FLOW

Regression:
```text
photo count preserved
photo high-res preserved
gallery order preserved
```

---

# 28. НЕ ЛОМАТЬ SOURCE LINK

Regression:
```text
«Открыть объявление на Avito» работает
```

---

# 29. EXTENSION VERSION

Если runtime extension code меняется:
```text
bump patch version от фактической текущей версии
```

Popup version остаётся dynamic.

Если extension code НЕ меняется, version не bump.

---

# 30. BUILD / DOWNLOAD

Если version bump:
- rebuild ZIP;
- обновить Admin Shell download artifact;
- проверить manifest внутри ZIP;
- `/avito/extension/download` → 200;
- версия ZIP = manifest version.

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

Указать фактические counts.

---

# 32. RUNTIME

Проверить:

```text
/inventory/products/58 → 200
/avito/extension → 200
```

И новый test product route, если используется read-only существующий product.

---

# 33. LIVE DATA SAFETY

Agent НЕ должен:
- массово импортировать объявления;
- редактировать Avito;
- удалять товары;
- удалять фото;
- reset DB.

Если для доказательства нужен реальный Owner page context, подготовить OWNER diagnostic step, а не притворяться, что live данные доступны.

---

# 34. DOCUMENTATION

Создать:

```text
reports/stage06a_r9_r3_real_characteristics_flow_fix_report.md
```

Обновить:
```text
logs/2026-08-21.md
```

Сохранить prompt:
```text
.agents/received_prompts/TECHNOREBOOT_STAGE06A_R9_R3_REAL_CHARACTERISTICS_FLOW_FIX_PROMPT.md
```

---

# 35. REPORT STRUCTURE

Обязательно:

```text
STATUS

OWNER_REPRO
CURRENT_EXTENSION_VERSION

CHARACTERISTICS_EXTRACTOR_FILE
CHARACTERISTICS_EXTRACTOR_FUNCTIONS
CURRENT_SELECTORS
CURRENT_STATE_PATHS

MOTHERBOARD_REAL_PATTERN
COMPUTER_REAL_PATTERN

REAL_AVITO_PAGE_CHARACTERISTICS_COUNT
EXTENSION_EXTRACTED_CHARACTERISTICS_COUNT
EXTENSION_FINAL_PAYLOAD_CHARACTERISTICS_COUNT
AVITO_MODULE_RECEIVED_CHARACTERISTICS_COUNT
CORE_RECEIVED_CHARACTERISTICS_COUNT
CORE_SAVED_CHARACTERISTICS_COUNT
PRODUCT_DETAILS_API_CHARACTERISTICS_COUNT

FIRST_FAILURE_LAYER
ROOT_CAUSE

FIX
FILES_CHANGED

BRAND_MODEL_BEHAVIOR
PHOTO_FLOW_PRESERVED
SOURCE_LINK_PRESERVED
PLUGIN_ONLY_UI_PRESERVED

EXTENSION_VERSION
ZIP_FILENAME

TESTS
RUNTIME
SAFETY

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
MULTI_CATEGORY_REAL_BUG_REPRODUCED_OR_PROVEN: true
FIRST_FAILURE_LAYER_IDENTIFIED: true
ROOT_CAUSE_IDENTIFIED: true

REALISTIC_MOTHERBOARD_CHARACTERISTICS_EXTRACTED: true
REALISTIC_COMPUTER_CHARACTERISTICS_EXTRACTED: true

CHARACTERISTICS_SURVIVE_EXTENSION_PAYLOAD: true
CHARACTERISTICS_SURVIVE_TRANSPORT: true
CHARACTERISTICS_SAVED_TO_R9_MODEL: true
CHARACTERISTICS_RETURNED_BY_DETAILS_API: true
CHARACTERISTICS_DISPLAYED_IN_UI: true

PHOTO_FLOW_PRESERVED: true
SOURCE_LINK_PRESERVED: true
PLUGIN_ONLY_UI_PRESERVED: true

OWNER_MANUAL_CHECK_REQUIRED: true
R10_NOT_STARTED: true
```

---

# 37. OWNER CHECK GUIDE

После успешного отчёта ОСТАНОВИТЬСЯ.

Owner повторяет 2 реальных теста:

### Материнская плата
```text
1. Открыть реальное объявление.
2. Посчитать/визуально отметить характеристики Avito.
3. Импортировать через новую extension version.
4. Открыть товар.
5. Сравнить все характеристики.
6. Проверить фото.
7. Проверить ссылку на исходное Avito.
```

### Компьютер / системный блок
```text
1. Повторить тот же сценарий.
2. Убедиться, что характеристики также передались.
```

Критерий:
```text
не одна характеристика,
а rich набор из нескольких реальных параметров.
```

Только после OWNER acceptance:
```text
Stage06A-R10 — Canonical Avito schema discovery
```

---

# 38. GIT SAFETY

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

Commit:
```text
Fix real Avito characteristics extraction flow
```

или точнее по фактической root cause.

После отчёта ОСТАНОВИТЬСЯ.
