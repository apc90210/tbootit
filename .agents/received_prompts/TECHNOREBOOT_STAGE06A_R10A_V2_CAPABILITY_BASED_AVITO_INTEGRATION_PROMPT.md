# TECHNOREBOOT — Stage06A-R10A V2
# Capability-Based Avito Integration Foundation
# Canonical Mapping + Preflight + Optional Official Autoload Adapter

Репозиторий:

```powershell
C:\tbootit
```

Дата:

```text
2026-08-27
```

---

# 0. КОНТЕКСТ

Текущее состояние проекта:

```text
Chrome Extension v0.2.17 — принято как рабочий baseline
Avito → Core import — работает
Фото — считаем рабочими
Характеристики — считаем рабочими
Source link Avito — работает
Plugin-only UI — принят
R9 dynamic Avito model — существует
```

Ключевой новый архитектурный принцип:

```text
Technoreboot НЕ должен зависеть от платного тарифа Avito.
```

Официальный Avito Autoload/API:
- может быть доступен не всем аккаунтам;
- не должен быть обязательным фундаментом всей интеграции;
- должен быть подключаемым capability/adapter.

---

# 1. ЦЕЛЬ ЭТАПА

Построить универсальный фундамент двусторонней интеграции:

```text
Observed Avito data
→ Canonical internal mapping
→ Publication preflight
→ Transport adapter
```

Транспорты:

```text
A. Official Autoload Adapter
   если аккаунт/API это поддерживает

B. Browser/Manual-Assisted Adapter
   если Autoload недоступен
```

В этой стадии НЕ публиковать ничего на Avito.

---

# 2. ГЛАВНЫЙ ПРИНЦИП

Архитектура должна быть:

```text
CORE DATA MODEL
      │
      ▼
CANONICAL AVITO PROJECTION
      │
      ▼
PUBLICATION PREFLIGHT
      │
      ├── Official Autoload Adapter
      │      capability-dependent
      │
      └── Browser/Manual-Assisted Adapter
             fallback path
```

То есть:

```text
API availability != system availability
Autoload availability != integration availability
```

---

# 3. CAPABILITY MODEL

Создать явную capability-модель.

Например:

```text
AVITO_API_AVAILABLE
AVITO_AUTOLOAD_AVAILABLE
AVITO_BROWSER_BRIDGE_AVAILABLE
AVITO_CANONICAL_SCHEMA_AVAILABLE
AVITO_PUBLISH_AUTOMATION_AVAILABLE
```

Не хардкодить capability как true.

Capability должна определяться runtime/configuration.

---

# 4. REQUIRED BEHAVIOR BY CAPABILITY

## Case A — API + Autoload доступны

Система может:

```text
получать официальное дерево категорий
получать официальные поля категории
сохранять canonical schema
строить preflight
в будущем публиковать через Autoload
```

## Case B — API есть, Autoload недоступен

Система может:

```text
использовать доступные API capabilities
но НЕ считать публикацию через Autoload доступной
```

## Case C — API/Autoload нет

Система всё равно должна:

```text
импортировать через Chrome Extension
хранить характеристики
строить internal canonical projection
показывать unresolved mapping
готовить publication package
использовать browser/manual-assisted workflow
```

---

# 5. НЕ ДЕЛАТЬ

НЕ начинать:

```text
Stage06B
real publish
feed upload
profile modification
массовую публикацию
реальный reverse sync
```

НЕ переписывать без необходимости:

```text
Chrome Extension extraction
photo pipeline
pairing
source link
plugin-only UI
```

---

# 6. GIT / RUNTIME AUDIT

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

Не затереть unrelated changes.

---

# 7. CURRENT R9 MODEL AUDIT

Проверить:

```text
AvitoCategory
AvitoAttributeDefinition
AvitoAttributeOption
ProductAvitoAttributeValue
```

Зафиксировать:

```text
OBSERVED_MODEL_CURRENT_FIELDS
OBSERVED_MODEL_LIMITATIONS
```

Текущую модель считать:

```text
Observed Avito Listing Data
```

а не official publication schema.

---

# 8. НОВЫЙ CANONICAL INTERNAL LAYER

Создать transport-neutral canonical слой.

Важно:

```text
он НЕ должен быть привязан только к Autoload
```

Рекомендуемые сущности:

## AvitoCanonicalCategory

```text
id
internal_key
display_name
observed_category_id nullable

official_slug nullable
official_source nullable

capability_source:
  observed
  official_api
  manual

active
created_at
updated_at
```

## AvitoCanonicalField

```text
id
category_id
internal_key
display_name

official_tag nullable
official_source nullable

data_type nullable
field_type nullable

active
created_at
updated_at
```

## AvitoCanonicalFieldRule

```text
id
field_id
ordinal
rule_source:
  official_api
  manual
  inferred_disabled

required nullable
required_by_dependency nullable
dependencies_json nullable
values_range_json nullable
raw_json nullable
```

Важно:

```text
inferred_disabled
```

не должен участвовать в production publish validation.

## AvitoCanonicalFieldValue

```text
id
field_id or rule_id
value
description nullable
official_value nullable
source
active
```

---

# 9. OBSERVED → CANONICAL MAPPING

Создать:

```text
AvitoObservedFieldMapping
```

Поля:

```text
id
category_id
observed_name
observed_name_normalized
canonical_field_id

mapping_source:
  exact_label
  manual
  official_tag_match

confidence
active
created_at
updated_at
```

Автоматически разрешить только:

```text
exact normalized label
within same category
```

Не делать:

```text
fuzzy mapping
LLM mapping
synonym guessing
```

в production flow.

---

# 10. CATEGORY MAPPING

Observed category:

```text
"Материнские платы"
```

не должна автоматически считаться официальной Avito category identity.

Canonical category может иметь:

```text
display_name = Материнские платы
official_slug = null
```

до тех пор, пока официальный slug не подтвержден.

---

# 11. OFFICIAL AUTOLOAD ADAPTER — OPTIONAL

Создать отдельный adapter/service:

```text
OfficialAvitoAutoloadSchemaProvider
```

Он включается только если:

```text
AVITO_CLIENT_ID present
AVITO_CLIENT_SECRET present
API access works
autoload endpoints accessible
```

Config:

```text
AVITO_CLIENT_ID
AVITO_CLIENT_SECRET
AVITO_API_BASE=https://api.avito.ru
```

Секреты:
- только server-side;
- не в Extension;
- не в Core DB;
- не в git;
- не в logs.

---

# 12. OFFICIAL AUTH CLIENT

Если configured:

```http
POST https://api.avito.ru/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
client_id=...
client_secret=...
```

Token cache по `expires_in`.

Не логировать token/secret.

---

# 13. OFFICIAL TREE CLIENT

Если capability доступна:

```http
GET /autoload/v1/user-docs/tree
Authorization: Bearer ...
```

Support:

```text
Last-Modified
If-Modified-Since
304
```

Parse recursively:

```text
name
slug
nested
path
raw
```

---

# 14. OFFICIAL CATEGORY FIELDS CLIENT

Если capability доступна:

```http
GET /autoload/v1/user-docs/node/{node_slug}/fields
Authorization: Bearer ...
```

Support:

```text
Last-Modified
If-Modified-Since
304
```

---

# 15. OFFICIAL FIELD MODEL

Если official schema реально доступна:

```text
category canonical key = node.slug
field publication key = APIField.tag
```

Парсить:

```text
tag
label
descriptions
feed_format[]
content[]
children[]
```

---

# 16. CONTENT RULES

Каждый `content[]` сохранять как отдельный rule.

Поддержать:

```text
field_type:
  input
  select
  checkbox

data_type:
  string
  integer
  float

required
required_by_dependency
default
dependencies
dependencies_text
is_catalog
name_in_catalog
values
values_link_json
values_link_xml
values_range
warnings
```

Не flatten в один type/required.

---

# 17. DEPENDENCY MODEL

Сохранять:

```text
action:
  visible
  required
  hidden

clause:
  and
  or

pairs:
  source_field_tag
  clause:
    value
    filled
    empty
  values[]
```

---

# 18. VALUES

Priority:

```text
1. inline values
2. values_link_json
3. values_link_xml = raw/unresolved
```

Для `values_link_json`:

```text
HTTPS only
Avito API host allowlist
Bearer auth
timeout
response-size limit
raw snapshot
```

---

# 19. CAPABILITY DETECTION

Создать service:

```text
get_avito_capabilities()
```

Пример output:

```json
{
  "browser_bridge": true,
  "api_configured": false,
  "api_authenticated": false,
  "autoload_schema_read": false,
  "autoload_publish": false,
  "canonical_schema_source": "observed_only"
}
```

Если credentials отсутствуют:

```text
api_configured = false
```

Это НЕ ошибка системы.

---

# 20. MANUAL / BROWSER-ASSISTED FALLBACK

Создать интерфейс/сервис publication package:

```text
build_avito_publication_package(product_id)
```

Он НЕ публикует.

Возвращает:

```json
{
  "product_id": 123,
  "category": "...",
  "title": "...",
  "description": "...",
  "price": 1000,
  "characteristics": {
    "...": "..."
  },
  "photos": [],
  "canonical_fields": {},
  "unresolved_fields": [],
  "transport_options": {
    "official_autoload": false,
    "browser_assisted": true,
    "manual": true
  }
}
```

Этот package должен быть usable:
- для browser-assisted adapter;
- для manual copy workflow;
- для future Official Autoload adapter.

---

# 21. PUBLICATION PREFLIGHT

Создать:

```text
preflight_product_for_avito(product_id)
```

Transport-neutral.

Output:

```json
{
  "ready_for_any_publication": true,
  "ready_for_official_autoload": false,
  "ready_for_browser_assisted": true,

  "product_id": 123,
  "canonical_category": "...",

  "fields": {},
  "errors": [],
  "warnings": [],
  "unresolved_fields": []
}
```

---

# 22. PREFLIGHT RULES

Transport-neutral validation:

```text
title present
description present
price valid
photos available
category resolved internally
observed characteristics preserved
```

Official Autoload-specific validation применяется ТОЛЬКО если official schema capability доступна.

---

# 23. OFFICIAL PREFLIGHT

Если official schema available:

```text
resolve official category slug
map canonical fields to official tags
evaluate dependencies
validate required
validate data_type
validate field_type
validate values
validate ranges
```

Если official schema unavailable:

```text
ready_for_official_autoload = false
warning = AUTOLOAD_SCHEMA_UNAVAILABLE
```

Но:

```text
ready_for_browser_assisted
```

может быть true.

---

# 24. FIRST TARGET CATEGORY

Для R10A использовать:

```text
Материнские платы
```

Но:

```text
official slug НЕ хардкодить
```

Если official schema недоступна:

```text
canonical category remains internal/observed
official_slug = null
```

Это корректный результат.

---

# 25. EXISTING PRODUCT IMPORT НЕ ЛОМАТЬ

Существующий Avito → Core flow должен продолжать работать:

```text
title
price
description
brand
model
condition
characteristics
photos
source URL
```

---

# 26. PHOTO FLOW НЕ ТРОГАТЬ

Не менять:

```text
gallery walker
HD extraction
SHA-256 dedupe
reconciliation
```

---

# 27. CHARACTERISTICS FLOW НЕ ТРОГАТЬ

Текущий characteristics import считать baseline.

R10A занимается:

```text
canonicalization
mapping
capability
preflight
```

---

# 28. FUTURE TRANSPORT INTERFACE

Создать абстракцию:

```text
AvitoPublicationTransport
```

Методы минимум:

```text
capabilities()
prepare(product_id)
validate(product_id)
publish(product_id)  # NOT IMPLEMENTED / disabled in R10A
```

Adapters:

```text
OfficialAutoloadTransport
BrowserAssistedTransport
ManualTransport
```

В R10A:

```text
publish() must raise NOT_IMPLEMENTED / DISABLED
```

---

# 29. NO REAL AVITO WRITES

Запрещено:

```text
POST /autoload/v1/upload
profile update
feed publication
create ad
edit ad
delete ad
upload photos
```

---

# 30. TESTS

Добавить минимум:

```text
test_capabilities_without_api_credentials
test_capabilities_with_mock_api_credentials
test_browser_assisted_available_without_autoload

test_observed_category_can_exist_without_official_slug
test_observed_field_mapping_exact_label
test_unresolved_field_preserved

test_publication_package_builds_without_api
test_preflight_browser_ready_without_autoload
test_preflight_official_not_ready_without_schema

test_official_tree_parser
test_official_fields_parser
test_content_rules_not_flattened
test_dependencies_preserved
test_inline_values_preserved
test_linked_json_values_supported

test_transport_publish_disabled
test_no_avito_write_calls

test_existing_listing_import_still_works
test_product_detail_still_works
test_source_link_still_works
test_photo_flow_unchanged
```

---

# 31. FULL REGRESSION

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

# 32. DOCUMENTATION

Создать:

```text
docs/stage06a_r10a_capability_based_avito_architecture.md
reports/stage06a_r10a_capability_based_avito_report.md
```

Обновить:

```text
logs/2026-08-27.md
```

Сохранить prompt:

```text
.agents/received_prompts/TECHNOREBOOT_STAGE06A_R10A_V2_CAPABILITY_BASED_AVITO_INTEGRATION_PROMPT.md
```

---

# 33. REPORT STRUCTURE

```text
STATUS

CURRENT_EXTENSION_VERSION

CAPABILITY_MODEL
AVITO_API_CONFIGURED
AVITO_API_AUTHENTICATED
AVITO_AUTOLOAD_SCHEMA_AVAILABLE
AVITO_BROWSER_BRIDGE_AVAILABLE
AVITO_BROWSER_ASSISTED_AVAILABLE

OBSERVED_MODEL_AUDIT
CANONICAL_MODEL
MIGRATIONS

OFFICIAL_AUTOLOAD_ADAPTER
OFFICIAL_TREE_CLIENT
OFFICIAL_FIELDS_CLIENT

CATEGORY_MAPPING
FIELD_MAPPING
UNRESOLVED_MAPPING_BEHAVIOR

PUBLICATION_PACKAGE
PREFLIGHT

TRANSPORT_INTERFACE
OFFICIAL_AUTOLOAD_TRANSPORT
BROWSER_ASSISTED_TRANSPORT
MANUAL_TRANSPORT

NO_REAL_AVITO_WRITES

MOTHERBOARD_CANONICAL_STATE
MOTHERBOARD_OFFICIAL_SLUG
MOTHERBOARD_OFFICIAL_SCHEMA_STATUS

CURRENT_IMPORT_PRESERVED
PHOTO_FLOW_PRESERVED
CHARACTERISTICS_FLOW_PRESERVED
SOURCE_LINK_PRESERVED
PLUGIN_ONLY_UI_PRESERVED

TESTS
RUNTIME

FILES_CHANGED
COMMIT
PUSH
FINAL_GIT_STATUS

OWNER_CHECK_GUIDE
NEXT_STEP
FINAL_STATUS
```

---

# 34. DEFINITION OF DONE

PASS infrastructure only if:

```text
CAPABILITY_MODEL_IMPLEMENTED: true

SYSTEM_WORKS_WITHOUT_AVITO_API: true
SYSTEM_WORKS_WITHOUT_AUTOLOAD: true

OBSERVED_MODEL_PRESERVED: true
CANONICAL_LAYER_IMPLEMENTED: true

EXACT_LABEL_MAPPING_SUPPORTED: true
UNRESOLVED_FIELDS_PRESERVED: true

PUBLICATION_PACKAGE_IMPLEMENTED: true
TRANSPORT_NEUTRAL_PREFLIGHT_IMPLEMENTED: true

OFFICIAL_AUTOLOAD_ADAPTER_OPTIONAL: true
BROWSER_ASSISTED_FALLBACK_AVAILABLE: true
MANUAL_FALLBACK_AVAILABLE: true

NO_REAL_AVITO_WRITES_PERFORMED: true

CURRENT_IMPORT_PRESERVED: true
PHOTO_FLOW_PRESERVED: true
CHARACTERISTICS_FLOW_PRESERVED: true
SOURCE_LINK_PRESERVED: true
PLUGIN_ONLY_UI_PRESERVED: true

OWNER_MANUAL_CHECK_REQUIRED: true
```

Если API credentials отсутствуют:

```text
OFFICIAL_AUTOLOAD_LIVE_SYNC:
NOT_CONFIGURED
```

Это НЕ blocker.

---

# 35. OWNER CHECK

После отчёта ОСТАНОВИТЬСЯ.

Owner проверяет:

```text
1. Обычный Avito import работает.
2. Материнская плата импортируется.
3. Характеристики отображаются.
4. Фото работают.
5. Source link работает.
6. В UI нет лишних Avito страниц.
7. Система не требует платного/API режима для обычной работы.
```

---

# 36. NEXT STEP

После acceptance:

```text
R10B
```

Следующий смысл:

```text
Browser-Assisted Reverse Publication Prototype
```

НО только dry-run / form-fill preparation,
без автоматического submit.

Параллельно, если официальный Autoload доступен:

```text
OfficialAutoloadTransport
```

можно развивать как отдельный adapter.

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

Commit:

```text
Add capability-based Avito integration foundation
```

После отчёта ОСТАНОВИТЬСЯ.
