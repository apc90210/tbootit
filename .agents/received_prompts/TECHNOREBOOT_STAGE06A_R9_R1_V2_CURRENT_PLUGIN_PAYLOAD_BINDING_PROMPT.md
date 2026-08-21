# TECHNOREBOOT — Stage06A-R9-R1 V2: Audit Current v0.2.10 Structured Payload and Bind It to Avito-First Core Model

Репозиторий:

```powershell
C:\tbootit
```

Контекст:
- Stage06A-R9 Core Avito-first model уже реализован.
- По актуальному отчету Chrome Extension уже v0.2.10 и умеет извлекать category, brand, model, characteristics, photos.
- Поэтому старый план "сначала научить extension извлекать характеристики" устарел.

НЕ начинать:
- массовый импорт всех объявлений;
- reverse sync;
- Stage06B;
- публикацию/редактирование Avito;
- поддержку нерелевантных категорий.

# 1. Главный принцип

Для Avito-интеграции:

```text
AVITO IS THE SOURCE OF TRUTH
FOR CATEGORY-SPECIFIC ATTRIBUTES
```

Нельзя придумывать свои Avito-характеристики, ID или типы без доказательства.

# 2. Приоритетные категории Техноребута

Работать сейчас только с:
1. Принтеры
2. МФУ
3. Компьютеры / системные блоки
4. Компьютерные комплектующие — по фактическим отдельным категориям Avito

# 3. Цель этапа

Проверить фактический текущий payload extension и связать его с R9-моделью Core.

Нужно ответить:
- что extension реально отправляет;
- как реально представлены category / brand / model / characteristics;
- есть ли реальные Avito external IDs / keys;
- чего достаточно для Avito → Core;
- чего не хватает для будущего Core → Avito.

# 4. Git/runtime audit

```powershell
Set-Location C:\tbootit
git status --short --untracked-files=all
git branch --show-current
git rev-parse HEAD
git log --oneline -15
git diff --name-status
git diff --stat
docker compose ps
```

Определить фактическую текущую extension version из manifest.json.

# 5. Audit actual extension payload

Найти production code, который формирует payload.

Зафиксировать:
```text
PAYLOAD_BUILDER_FILE
PAYLOAD_BUILDER_FUNCTION
CURRENT_SCHEMA_VERSION
CURRENT_EXTENSION_VERSION
```

Проверить фактический формат:
```text
listing.category
listing.brand
listing.model
listing.characteristics
listing.photos
```

# 6. Characteristics format

Критически определить, что сейчас реально используется:
```text
A. plain object {"name":"value"}
B. array with name/value
C. array with external keys/ids
D. richer structure
```

Не опираться на отчет — проверить код.

# 7. Реальные Avito identifiers

Для category и attributes исследовать реальные источники:
```text
JSON-LD
__initialData__
__NEXT_DATA__
DOM
React state
widgets
```

Для каждого определить:
```text
external category id/key available: true/false
external attribute id/key available: true/false
external option id/key available: true/false
source
example
```

Не выдумывать ID.

# 8. Первый эталон — Product 58

Использовать:
```text
Avito listing: 8313765236
Product ID: 58
```

Read-only audit.

Получить реальные:
```text
category
brand
model
characteristics
```

Если live browser context недоступен — использовать сохраненные raw payload/logs/fixtures и честно это отметить.

# 9. Provenance table

Для каждого поля:
```text
FIELD
VALUE
SOURCE_LAYER
SOURCE_PATH
EXTERNAL_ID_AVAILABLE
RAW_FRAGMENT_AVAILABLE
CONFIRMED_REAL_AVITO_DATA
```

Особенно:
- category
- brand
- model
- each characteristic

# 10. Brand/model source

Проверить:
```text
brand/model реально приходят как отдельные Avito fields
или extension выводит их эвристически?
```

Если эвристика — не выдавать за официальный Avito attribute.

# 11. Audit R9 Core model

Подтвердить:
```text
AvitoCategory
AvitoAttributeDefinition
AvitoAttributeOption
ProductAvitoAttributeValue
```

Проверить migrations, constraints, raw_value strategy, unknown attribute handling, APIs.

# 12. Bind current payload to R9 model

Если current payload содержит только display name/value:

```text
external_category_id = null if unknown
external_attribute_id = null if unknown
name = actual Avito display name
raw_value = exact captured value
source = avito
```

Нельзя генерировать фальшивый Avito ID.

# 13. Provisional identity

Если official external attribute ID сейчас недоступен, можно использовать внутренний stable key, например normalized display name scoped to category, но он должен быть явно internal/provisional, а не avito_attribute_id.

# 14. Unknown type

Если официальный тип неизвестен, не утверждать, что это официальный string.

Предпочтительно хранить честный fallback:
```text
unknown/raw
```
или документированный internal fallback с сохранением raw_value.

# 15. Attribute options

Если Avito реально публикует option IDs/choices — сохранить.
Если текущая страница показывает только выбранный label — не выдумывать полный список вариантов.

# 16. Structured ingest path

Проверить/реализовать:
```text
Extension payload
→ Admin Shell
→ Avito Module
→ Core
→ R9 models
→ Product
```

category/characteristics должны сохраняться структурированно, а не только в legacy JSON blob.

# 17. Preserve raw payload

Сохранить:
```text
raw category fragment
raw characteristic name
raw value
raw external key/id if present
captured_at
schema_version
extension_version
```

# 18. Legacy fields

Проверить существующие:
```text
avito_category_path
avito_goods_type
avito_params_json
source_attributes_json
source_json
```

Не удалять. Определить роль compatibility/raw vs normalized R9 model.

# 19. Idempotency

Повторный import одного listing:
```text
same category stays one
same attribute definitions stay one
values update
duplicates do not multiply
```

# 20. Category-specific separation

Одноименные характеристики разных категорий не должны случайно сливаться глобально, если контракт Avito category-scoped.

# 21. Priority category scaffolding

Generic model должен поддерживать разные схемы для:
```text
Printers
MFP
Computers/System Units
Components
```

через synthetic fixtures, без исследования всего каталога Avito.

# 22. Photo/media code не трогать

Не переписывать photo extraction / quality / dedupe / hydration без необходимости.

# 23. Batch import

Не запускать массовый Owner import. Проверить только contract и совместимость schema/attributes с batch.

# 24. Reverse sync readiness assessment

НЕ реализовывать reverse sync.

В отчете дать таблицу:
```text
FIELD
AVITO→CORE READY
CORE→AVITO READY
MISSING FOR REVERSE
```

Для:
- category
- brand
- model
- characteristics
- photos
- title
- description
- price

# 25. UI

Если structured values уже можно безопасно читать:
```text
Категория Avito
Характеристики Avito
```

только подтвержденные данные.

Если данных нет:
```text
Характеристики Avito не импортированы
```

Не показывать debug/internal IDs Owner-у.

# 26. Plugin-only UI сохранить

В owner-facing UI по-прежнему только «Расширение Avito».
Read-only attributes внутри Product detail допустимы.

# 27. Tests

Добавить минимум:
```text
current extension listing payload contract parses
category saved
characteristics saved
raw values preserved
unknown external IDs remain null/provisional
repeat import idempotent
different categories keep separate schemas
product without Avito data still valid
```

# 28. Real fixture

Создать fixture только из реально наблюдавшихся данных.
Не дополнять характеристиками из головы.

# 29. Full regression

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
docker compose exec -T inventory-sales-module pytest
docker compose exec -T avito-module pytest
docker compose exec -T repairs-module pytest
pytest admin-shell/tests
pytest chrome-extension/technoreboot-avito/tests
```

# 30. Runtime

Проверить:
```text
Core healthy
Inventory healthy
Avito module healthy
Repairs healthy
Admin Shell healthy
```

И рабочие routes:
```text
/inventory/products/58
/avito/extension
```

# 31. Safety

НЕ:
```text
mass import all listings
delete Product 58
reset DB
DROP TABLE
reverse sync
publish to Avito
edit Avito listing
```

# 32. Extension version

Если extension runtime code не меняется — не bump version.
Если нужен code change для structured characteristic payload — bump patch from actual manifest version.
Dynamic popup version сохранить.

# 33. Documentation

Создать:
```text
docs/stage06a_r9_r1_v2_current_plugin_payload_binding.md
reports/stage06a_r9_r1_v2_current_plugin_payload_binding_report.md
```

Обновить:
```text
logs/2026-08-21.md
```

Сохранить prompt:
```text
.agents/received_prompts/TECHNOREBOOT_STAGE06A_R9_R1_V2_CURRENT_PLUGIN_PAYLOAD_BINDING_PROMPT.md
```

# 34. Report structure

```text
STATUS
CURRENT_EXTENSION_VERSION
ACTUAL_PAYLOAD_CONTRACT
CATEGORY_FORMAT
CHARACTERISTICS_FORMAT
BRAND_SOURCE
MODEL_SOURCE
REAL_EXTERNAL_CATEGORY_ID_AVAILABLE
REAL_EXTERNAL_ATTRIBUTE_IDS_AVAILABLE
REAL_EXTERNAL_OPTION_IDS_AVAILABLE
PRODUCT_58_REAL_PROVENANCE
R9_MODEL_AUDIT
R9_MODEL_CHANGES
NORMALIZED_INGEST_PATH
RAW_PAYLOAD_PRESERVATION
PROVISIONAL_KEY_STRATEGY
UNKNOWN_TYPE_STRATEGY
IDEMPOTENCY
PRIORITY_CATEGORY_SCOPE
AVITO_TO_CORE_READINESS
CORE_TO_AVITO_GAPS
UI
PLUGIN_ONLY_UI_PRESERVED
TESTS
RUNTIME
SAFETY
FILES_CHANGED
COMMIT
PUSH
FINAL_GIT_STATUS
OWNER_CHECK_GUIDE
NEXT_RECOMMENDED_STAGE
FINAL_STATUS
```

# 35. Definition of Done

PASS only if:
```text
CURRENT_PLUGIN_PAYLOAD_AUDITED: true
NO_INVENTED_AVITO_IDS: true
NO_INVENTED_AVITO_ATTRIBUTES: true
REAL_PROVENANCE_DISTINGUISHED_FROM_SYNTHETIC: true
STRUCTURED_CATEGORY_INGEST_TO_R9_MODEL: true
STRUCTURED_CHARACTERISTICS_INGEST_TO_R9_MODEL: true
RAW_VALUES_PRESERVED: true
UNKNOWN_IDS_HANDLED_HONESTLY: true
REPEAT_IMPORT_IDEMPOTENT: true
PRIORITY_CATEGORY_SCOPE_PRESERVED: true
PLUGIN_ONLY_UI_PRESERVED: true
MASS_IMPORT_NOT_STARTED: true
REVERSE_SYNC_NOT_STARTED: true
OWNER_MANUAL_CHECK_REQUIRED: true
```

# 36. Expected next stage

После Owner acceptance:
```text
Stage06A-R10 — Canonical Avito schema discovery for supported categories
```

Смысл:
```text
real category identity
real attribute identities if available
real value/options metadata
schema persistence
```

Очередность:
```text
1. Принтеры
2. МФУ
3. Компьютеры/системные блоки
4. Комплектующие по отдельным Avito-категориям
```

# 37. Git safety

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
Bind current Avito extension payload to Core attribute model
```

После отчёта ОСТАНОВИТЬСЯ.
