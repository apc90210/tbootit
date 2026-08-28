# TECHNOREBOOT — Stage06A-R10A-R1
## Module Boundary + Extension Change Audit

Репозиторий: `C:\tbootit`

Текущий R10A commit:
`55c5a81 Add capability-based Avito integration foundation`

### Почему нужен corrective-step
R10A пока НЕ принимать:
1. `OfficialAvitoAutoloadSchemaProvider` реализован в `core/app/services`, хотя внешний Avito API/OAuth должен принадлежать `avito-module`.
2. В commit попал `chrome-extension/technoreboot-avito/content.js` и были пересобраны ZIP v0.2.17 без объяснения runtime-изменения/version bump.

НЕ начинать R10B/Stage06B/reverse publication.

## Архитектурная граница

```text
CORE
= DB owner
= product/domain owner
= canonical models
= mappings
= persisted official schema
= pure preflight/domain validation

AVITO-MODULE
= all external Avito communications
= OAuth/token
= official API client
= Autoload schema fetch
= external capability probing
= future Avito transports

CHROME EXTENSION
= browser/user-context bridge
= observed listing extraction
= future browser-assisted interaction
```

Критерии:
```text
Core MUST NOT require AVITO_CLIENT_ID / AVITO_CLIENT_SECRET.
Core MUST NOT call api.avito.ru.
```

## Precheck

```powershell
Set-Location C:\tbootit
git status --short --untracked-files=all
git branch --show-current
git rev-parse HEAD
git log --oneline -12
git diff --name-status 55c5a81^ 55c5a81
git diff --stat 55c5a81^ 55c5a81
docker compose ps
```

Не rollback весь R10A.

## 1. Audit current placement

Проверить:
```text
core/app/config.py
core/app/services/avito_capability_service.py
core/app/services/avito_canonical_service.py
core/app/services/avito_official_autoload_provider.py
core/app/services/avito_preflight_service.py
core/app/services/avito_transport.py
core/app/routers/integrations.py
avito-module/app/*
```

Таблица:
```text
COMPONENT
CURRENT_MODULE
CALLS_EXTERNAL_AVITO
USES_AVITO_SECRET
OWNS_DB
TARGET_MODULE
ACTION
```

## 2. Move official API boundary to avito-module

Перенести в `avito-module`:
```text
OfficialAvitoAutoloadSchemaProvider
OAuth/token handling
AVITO_CLIENT_ID
AVITO_CLIENT_SECRET
AVITO_API_BASE
external API capability probing
fetch_tree()
fetch_node_fields()
fetch_linked_json_values()
```

Core config не должен содержать credentials.

Проверка:
```powershell
git grep -n "AVITO_CLIENT_ID\|AVITO_CLIENT_SECRET\|api.avito.ru" core
```

После correction в Core не должно быть credential handling или outbound Avito HTTP client.

## 3. Core responsibilities to keep

Оставить в Core:
```text
AvitoCanonicalCategory
AvitoCanonicalField
AvitoCanonicalFieldRule
AvitoCanonicalFieldValue
AvitoObservedFieldMapping
canonical persistence/upsert
observed → canonical mapping
publication package
pure preflight
```

Core может хранить `official_slug`, `official_tag`, rules, values — но получает их только по internal HTTP от avito-module.

## 4. Schema ingest path

Сделать явную цепочку:
```text
avito-module
→ official Avito API
→ normalized schema payload
→ Core internal HTTP endpoint
→ canonical DB persistence
```

Core endpoint по convention, например:
```text
POST /api/integrations/avito/autoload-schema/import
```

Payload:
```text
category slug/name/path
fields
content rules
dependencies
values
raw snapshots
Last-Modified metadata
```

Никаких OAuth token/secret внутри payload.

## 5. Capability split

Core/domain capabilities:
```text
browser_bridge_available
canonical_schema_present
browser_assisted_possible
manual_possible
```

Avito-module external capabilities:
```text
api_configured
api_authenticated
autoload_schema_endpoint_accessible
autoload_publish_accessible
```

Если нужен aggregate endpoint — объединять на уровне Avito Module/Admin Shell, не через чтение secret в Core.

## 6. Transport placement

Проаудировать `core/app/services/avito_transport.py`.

Правило:
`actual publication transport belongs to avito-module`.

Предпочтительно:
```text
OfficialAutoloadTransport → avito-module
BrowserAssistedTransport coordination → avito-module/extension bridge
```

Core оставляет только pure package/preflight.

Если текущие transport classes полностью stub/no-network и остаются в Core — это нужно обосновать. Ничего не публиковать.

## 7. Audit unexpected extension change

Обязательно:
```powershell
git diff 55c5a81^ 55c5a81 -- chrome-extension/technoreboot-avito/content.js
git diff --word-diff 55c5a81^ 55c5a81 -- chrome-extension/technoreboot-avito/content.js
```

Отчёт:
```text
EXTENSION_CONTENT_CHANGED
EXACT_CHANGE
WHY_CHANGED
RUNTIME_BEHAVIOR_CHANGED
VERSION_BUMP_REQUIRED
```

Case A — accidental/unrelated:
follow-up commit возвращает только accidental change к pre-R10A behavior.

Case B — required runtime bugfix:
объяснить bug, добавить regression test, bump patch version, rebuild ZIP.

Case C — comment/non-runtime only:
доказать `RUNTIME_BEHAVIOR_CHANGED=false`, version bump не нужен.

Нельзя менять runtime extension и оставлять тот же `0.2.17` без объяснения.

## 8. ZIP audit

Проверить:
```text
admin-shell/app/technoreboot-avito-extension-0.2.17.zip
admin-shell/app/technoreboot-avito-extension.zip
dist/technoreboot-avito-extension-0.2.17.zip
```

Зафиксировать:
```text
MANIFEST_VERSION
CONTENT_JS_SHA256_SOURCE
CONTENT_JS_SHA256_ZIP
ZIP_SOURCE_MATCHES_EXTENSION_TREE
```

## 9. Test-count audit

R10A report заявил:
```text
Core 208
Inventory 114
Repairs 83
Avito 84
Admin 55
Extension 57
Total 601
```

Проверить, не перепутаны ли Inventory/Repairs labels.

В отчёте:
```text
COMMAND
ACTUAL_TEST_DIRECTORY
COUNT
PASS
```

## 10. Security tests

Добавить/обновить:
```text
test_core_does_not_require_avito_client_credentials
test_core_has_no_outbound_avito_api_client
test_avito_module_owns_api_credentials
test_avito_module_token_not_logged
test_avito_module_official_provider_disabled_without_credentials
test_schema_import_to_core_does_not_include_secret_or_token
```

Architecture contract:
```text
core source must not reference AVITO_CLIENT_SECRET
core source must not instantiate official Avito HTTP provider
avito-module owns official provider
```

## 11. No-API regression

Без credentials должно продолжать работать:
```text
normal Avito import
observed canonical layer
preflight
browser-assisted capability
manual capability
official autoload = false
```

## 12. Current owner flows preserve

Проверить:
```text
/avito/extension → 200
/inventory/products/58 → 200
/inventory/products/103 → 200 if exists
```

Import/characteristics/photos/source link должны сохраниться.

## 13. Full regression

Запускать отдельно и записать фактические counts:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
docker compose exec -T inventory-sales-module pytest
docker compose exec -T avito-module pytest
docker compose exec -T repairs-module pytest
pytest admin-shell/tests
pytest chrome-extension/technoreboot-avito/tests
```

## 14. Documentation

Создать:
```text
reports/stage06a_r10a_r1_module_boundary_extension_audit_report.md
```

Обновить:
```text
docs/stage06a_r10a_capability_based_avito_architecture.md
logs/2026-08-28.md
```

Сохранить:
```text
.agents/received_prompts/TECHNOREBOOT_STAGE06A_R10A_R1_MODULE_BOUNDARY_EXTENSION_AUDIT_PROMPT.md
```

## 15. Report structure

```text
STATUS
BASE_COMMIT
CURRENT_HEAD
MODULE_BOUNDARY_AUDIT
OFFICIAL_PROVIDER_BEFORE
OFFICIAL_PROVIDER_AFTER
CORE_SECRET_REFERENCES_BEFORE
CORE_SECRET_REFERENCES_AFTER
CORE_EXTERNAL_AVITO_CALLS_AFTER
AVITO_MODULE_PROVIDER
AVITO_MODULE_CREDENTIAL_CONFIG
SCHEMA_INGEST_PATH
CORE_CANONICAL_MODEL_PRESERVED
CORE_PREFLIGHT_PRESERVED
CAPABILITY_SPLIT
NO_API_MODE_PRESERVED
TRANSPORT_INTERFACE_AUDIT
TRANSPORT_INTERFACE_FINAL_PLACEMENT
EXTENSION_CONTENT_CHANGED
EXTENSION_DIFF
EXTENSION_CHANGE_REASON
RUNTIME_BEHAVIOR_CHANGED
VERSION_DECISION
ZIP_AUDIT
ZIP_VERSION
ZIP_SOURCE_MATCH
TEST_COUNTS_AUDIT
FULL_REGRESSION
SECURITY_TESTS
CURRENT_IMPORT_PRESERVED
PHOTO_FLOW_PRESERVED
CHARACTERISTICS_FLOW_PRESERVED
SOURCE_LINK_PRESERVED
PLUGIN_ONLY_UI_PRESERVED
FILES_CHANGED
COMMIT
PUSH
FINAL_GIT_STATUS
OWNER_CHECK_GUIDE
NEXT_STEP
FINAL_STATUS
```

## 16. Definition of Done

```text
CORE_OWNS_NO_AVITO_CREDENTIALS: true
CORE_PERFORMS_NO_OUTBOUND_AVITO_API_CALLS: true
AVITO_MODULE_OWNS_OFFICIAL_API_PROVIDER: true
AVITO_MODULE_OWNS_OAUTH_TOKEN: true
CORE_CANONICAL_DB_MODEL_PRESERVED: true
CORE_MAPPING_PRESERVED: true
CORE_PURE_PREFLIGHT_PRESERVED: true
SCHEMA_FLOW_IS_AVITO_MODULE_TO_CORE_HTTP: true
NO_API_MODE_PRESERVED: true
SYSTEM_WORKS_WITHOUT_AUTOLOAD: true
UNEXPECTED_EXTENSION_CHANGE_AUDITED: true
EXTENSION_VERSION_DISCIPLINE_CORRECT: true
ZIP_SOURCE_MATCH: true
NO_REAL_AVITO_WRITES: true
CURRENT_IMPORT_PRESERVED: true
PHOTO_FLOW_PRESERVED: true
CHARACTERISTICS_FLOW_PRESERVED: true
SOURCE_LINK_PRESERVED: true
PLUGIN_ONLY_UI_PRESERVED: true
OWNER_MANUAL_CHECK_REQUIRED: true
```

## 17. Owner check

После отчёта остановиться. Owner проверяет только:
1. `/avito/extension`;
2. popup extension;
3. импорт одного товара;
4. карточку товара;
5. characteristics/photos/source link.

Архитектурный перенос provider/OAuth подтверждается report/tests.

## 18. Next step

Только после acceptance:
```text
Stage06A-R10B — Browser-Assisted Reverse Publication Prototype
```

Сначала dry-run + form-fill preparation, NO submit.

## Git safety

Forbidden:
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

Suggested commit:
`Move Avito external API boundary to avito-module`

После отчёта ОСТАНОВИТЬСЯ.
