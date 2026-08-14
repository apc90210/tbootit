# TECHNOREBOOT — Stage06A-R9 Avito-First Category & Attribute Model in Core

Репозиторий:

```powershell
C:\tbootit
```

Дата этапа: `2026-08-14`

Это следующий этап после принятого photo-import блока Stage06A-R8.

## 0. Gate

НЕ начинать:
- массовый импорт всех объявлений;
- Stage06B reverse sync;
- автоматическую публикацию/редактирование Avito;
- следующие этапы без Owner acceptance.

## 1. Главный принцип

Для Avito-интеграции:

```text
AVITO IS THE SOURCE OF TRUTH
FOR CATEGORY-SPECIFIC ATTRIBUTES
```

Нельзя:
- придумывать свои характеристики;
- создавать внутренние поля «на всякий случай»;
- потом пытаться сопоставлять их с Avito;
- зашивать категории цепочками if/elif по проекту.

Нужно:

```text
сначала определить реальные категории и характеристики Avito;
затем хранить их в Core универсально и без потери информации.
```

Разные категории Avito имеют разные наборы характеристик: принтеры, процессоры, системные блоки, мониторы и т.д.

## 2. Архитектурное разделение

Техноребут остаётся владельцем Product и своей БД. Но для Avito-модуля структура характеристик определяется Avito:

```text
Avito category schema
→ фиксируется в Core
→ Product хранит значения этой Avito-схемы
```

Не превращать всю внутреннюю модель Техноребута в копию Avito. Avito-схема — внешний контракт.

## 3. Цель Stage06A-R9

Создать в Core динамическую модель, эквивалентную:

```text
AvitoCategory
AvitoAttributeDefinition
AvitoAttributeOption
ProductAvitoAttributeValue
Product ↔ AvitoCategory
```

Если в проекте уже есть подходящие сущности — переиспользовать/расширить их, а не создавать параллельные.

Ключевой результат:

```text
одна категория Avito
→ свой набор характеристик
→ свои типы
→ свои допустимые значения
→ свои обязательные/необязательные поля
```

Никаких новых колонок Product под каждую характеристику категории.

## 4. Сначала аудит текущей модели

До изменений найти и описать:
- Product;
- Category;
- Brand;
- Model;
- Characteristics / Attributes / Specifications;
- Avito integration models;
- External listing models;
- generic JSON-поля характеристик, если есть;
- category mapping;
- Avito category ID;
- старые/незавершённые attribute schemas.

Не создавать вторую модель, если существующая годится для безопасного расширения.

## 5. Backward compatibility

На этом этапе:
- не переносить все старые Product fields;
- не удалять существующие характеристики;
- не менять sale/inventory/reporting semantics;
- не ломать существующие товары.

Product без Avito category/attributes остаётся валидным.

## 6. Реальная Avito-схема, не выдуманная

Использовать текущий эталон:

```text
Avito ID: 8313765236
Product ID: 58
```

Нужно определить фактическую категорию и фактические характеристики, которые Avito реально показывает/хранит для этого объявления.

Источник — только реальные данные Avito:
- DOM;
- JSON-LD;
- page state / hydration;
- уже имеющийся structured payload extension;
- другие реально присутствующие структуры страницы.

Не придумывать характеристики принтера из общих знаний.

## 7. AvitoCategory

Минимально хранить, если реально доступно:

```text
id
external_category_id
name
parent_external_category_id
path/breadcrumb
source = avito
is_active
observed_at / last_seen_at
created_at
updated_at
```

Не выдумывать external ID, если Avito его не предоставляет текущим доступным способом.

## 8. AttributeDefinition

Для каждой характеристики Avito:

```text
id
category_id
external_attribute_id / external key
name
type
required
multiple
unit (если Avito её реально даёт)
sort/display order
observed_at / last_seen_at
created_at
updated_at
```

Поддержать универсальные типы как storage abstraction:
- string/text;
- integer/number;
- decimal;
- boolean;
- single choice;
- multiple choice.

Но фактический type должен определяться реальными данными Avito.

Если type нельзя достоверно определить — сохранить безопасно без выдумывания семантики.

## 9. AttributeOption

Если Avito поле имеет фиксированные варианты, хранить варианты отдельно:

```text
attribute_definition_id
external_option_id / key
value
label
sort_order
active / last_seen
```

Не превращать перечисление Avito в свободный текст без причины.

## 10. ProductAvitoAttributeValue

Значения товара хранятся динамически.

Нельзя добавлять в Product поля вида:

```text
printer_duplex
cpu_socket
monitor_matrix
```

Нужна универсальная схема, например:

```text
product_id
attribute_definition_id
value / normalized value
option relation if enum
raw_value
source = avito
updated_at
```

Multiple-choice должен поддерживаться корректно.

## 11. Raw value обязателен

Поскольку Avito — первичный источник, нужно сохранить оригинальное значение или оригинальный payload fragment так, чтобы его можно было восстановить для будущего reverse sync.

Нельзя терять исходное значение при нормализации.

## 12. Product ↔ AvitoCategory

Product может быть связан с конкретной категорией Avito, но Avito не становится обязательным для всех товаров Техноребута.

Если у проекта уже есть внутренняя Category, не заменять её автоматически на AvitoCategory.

Предпочтительно:

```text
Product internal category
+
Product Avito category binding
```

## 13. Avito schema changes

Avito может менять характеристики категории.

Предусмотреть минимум:
- observed_at / last_seen_at;
- optional schema hash;
- active/inactive semantics при необходимости.

Повторное наблюдение схемы не должно плодить дубли.

Если появляется новое поле — его нужно уметь сохранить без DB migration новой колонки.

Если поле исчезает — не удалять его бездумно; лучше помечать как неактуальное/не наблюдавшееся.

## 14. Unknown attribute safety

Если Avito добавляет неизвестное поле:
- не должно быть 500;
- поле не должно молча теряться;
- не должна требоваться новая колонка Product.

Реализовать безопасное динамическое сохранение definition + raw value или эквивалент.

## 15. Первый реальный эталон — принтер

Для `8313765236`:
1. получить фактическую Avito category;
2. получить фактический список Avito-характеристик;
3. сохранить definitions/options;
4. сохранить значения Product 58 только если это можно сделать безопасно без повторного Owner import;
5. иначе подготовить схему к следующему Owner import.

Product 58 не удалять и не дублировать.

## 16. Модель должна быть общей

Она должна одинаково поддерживать категории вроде:
- CPU;
- системный блок;
- монитор;
- ноутбук;
- принтер;
- МФУ;
- другие категории.

Без новой таблицы/колонки для каждой категории.

Synthetic tests разрешены для проверки универсальности модели, но реальные поля принтера не выдумывать.

## 17. Core API

Добавить/расширить API для чтения:

```text
GET Avito categories
GET Avito category schema
GET Product Avito category
GET Product Avito attributes
```

И service layer для:

```text
upsert category schema
upsert attribute definitions/options
upsert product attribute values
```

Не создавать хаотичные duplicate endpoints, если можно расширить текущие integration endpoints.

## 18. Будущий import contract

Подготовить структурированный contract Avito → Core, содержащий минимум:

```text
category
attribute definitions
attribute values
raw values
```

Фактический JSON должен соответствовать существующей архитектуре проекта.

Не делать production extractor всех категорий раньше, чем Core способен корректно сохранить эту структуру.

## 19. Extension scope на этом этапе

Главный фокус — Core/data model.

Extension менять только если нужно read-only получить/доказать реальную category/attributes структуру.

Если extension изменён:
- bump version;
- dynamic version display сохранить;
- собрать ZIP;
- протестировать.

Если extension не менялся — version не bump.

## 20. Минимальный UI

Полноценный dynamic editor будет следующим этапом.

На R9 допустимо/желательно добавить read-only блок в Product detail:

```text
Категория Avito
Характеристики Avito
```

Если значений нет:

```text
Характеристики Avito не импортированы
```

UI полностью на русском.

## 21. Миграции

Все изменения БД:
- backward-compatible;
- non-destructive.

Запрещено:
- DROP existing product tables;
- reset live DB;
- mass delete;
- разрушительная миграция старых товаров.

## 22. Constraints / indexes

Продумать уникальность:
- Avito category external ID;
- attribute within category;
- option within attribute;
- Product attribute values.

Повторный импорт одной схемы не должен размножать definitions/options.

## 23. Idempotency

Повторный import одной schema:

```text
1 category stays 1
N attributes stay N
options stay unique
```

Повторный import Product attributes:
- значения обновляются;
- дубли не появляются.

## 24. Tests — model

Минимум:

```text
category can have different schemas
printer schema != cpu schema
attribute definitions unique per category
single choice options
multiple choice options
numeric/text/bool values
unknown attribute preserved
product without Avito data remains valid
```

## 25. Tests — idempotency/schema changes

Минимум:

```text
repeat category schema import no duplicate category
repeat attribute import no duplicate definitions
repeat options no duplicate options
repeat product attribute import updates values
schema adds new field safely
schema missing old field does not destructive-delete history
```

## 26. Real printer fixture

Для фактически наблюдавшихся данных listing `8313765236` создать fixture только из реальных Avito fields.

Не дополнять fixture характеристиками из головы.

Тест:

```text
real observed Avito category schema
→ stored
→ read back without information loss
```

## 27. API/UI tests

Проверить:
- чтение category/schema;
- чтение Product Avito attributes;
- empty state;
- разные категории дают разные наборы полей.

## 28. Full regression

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

## 29. Runtime/safety

Проверить:

```text
docker compose ps
Core healthy
Inventory healthy
Avito module healthy
Admin Shell healthy
```

Product 58:
- не удалять;
- не дублировать;
- не менять цену/title/status без необходимости.

Mass import не запускать.

## 30. Documentation

Создать:

```text
docs/stage06a_r9_avito_category_attribute_model.md
reports/stage06a_r9_avito_first_category_attribute_model_report.md
```

Обновить:

```text
logs/2026-08-14.md
README.md
```

только если README реально содержит roadmap/current-stage info.

Сохранить prompt:

```text
.agents/received_prompts/TECHNOREBOOT_STAGE06A_R9_AVITO_FIRST_CATEGORY_ATTRIBUTE_MODEL_PROMPT.md
```

## 31. Report structure

Отчёт должен содержать:

```text
STATUS
PRE_STAGE_AUDIT
EXISTING_CATEGORY_MODELS
EXISTING_ATTRIBUTE_MODELS
REUSED_COMPONENTS
NEW_COMPONENTS

AVITO_SOURCE_OF_TRUTH_RULE

REAL_LISTING_8313765236_CATEGORY
REAL_OBSERVED_AVITO_ATTRIBUTES
REAL_SCHEMA_SOURCE

DATA_MODEL
CATEGORY_MODEL
ATTRIBUTE_DEFINITION_MODEL
ATTRIBUTE_OPTION_MODEL
PRODUCT_ATTRIBUTE_VALUE_MODEL

RAW_VALUE_STRATEGY
UNKNOWN_ATTRIBUTE_STRATEGY
SCHEMA_CHANGE_STRATEGY
IDEMPOTENCY
CONSTRAINTS

CORE_API
UI_READ_ONLY_VIEW

MIGRATIONS
BACKWARD_COMPATIBILITY

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

## 32. Owner check

После реализации остановиться.

Owner check:

```text
1. Открыть Product 58.
2. Убедиться, что товар работает как раньше.
3. Если реальная Avito schema уже безопасно привязана:
   - увидеть «Категория Avito»;
   - увидеть реальные Avito-характеристики.
4. Если значения ещё не импортированы:
   - увидеть корректный empty state;
   - следующий этап будет extraction/import characteristics.
```

## 33. Next stage — только предложить

После R9 не начинать автоматически.

Предполагаемый следующий этап:

```text
Stage06A-R10:
Avito characteristic extraction + structured import
for one real category/listing
```

То есть:

```text
extension/page
→ real Avito category
→ real characteristics
→ Core schema/values
→ Product detail
```

## 34. Git safety

Перед работой:

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

## 35. Commit

При успехе:

```text
Add Avito-first category attribute model
```

или точнее по фактическим изменениям.

Push:

```powershell
git push origin main
```

## 36. Definition of Done

PASS только если:

```text
AVITO_IS_ATTRIBUTE_SOURCE_OF_TRUTH: true
NO_INVENTED_AVITO_ATTRIBUTES: true
DYNAMIC_CATEGORY_SCHEMA_IMPLEMENTED: true
CATEGORY_SPECIFIC_ATTRIBUTES_SUPPORTED: true
ATTRIBUTE_OPTIONS_SUPPORTED: true
PRODUCT_DYNAMIC_AVITO_VALUES_SUPPORTED: true
UNKNOWN_AVITO_ATTRIBUTE_PRESERVABLE: true
RAW_AVITO_VALUE_PRESERVED: true
REPEAT_SCHEMA_IMPORT_IDEMPOTENT: true
PRODUCT_WITHOUT_AVITO_DATA_STILL_VALID: true
BACKWARD_COMPATIBLE: true
FULL_REGRESSION_PASS: true
OWNER_MANUAL_CHECK_REQUIRED: true
MASS_IMPORT_NOT_STARTED: true
REVERSE_SYNC_NOT_STARTED: true
```

## 37. Final status

При успехе:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE06A_R9_AVITO_FIRST_CATEGORY_ATTRIBUTE_MODEL_READY_FOR_OWNER_CHECK

AVITO_IS_ATTRIBUTE_SOURCE_OF_TRUTH: true
NO_INVENTED_AVITO_ATTRIBUTES: true
DYNAMIC_CATEGORY_SCHEMA_IMPLEMENTED: true
CATEGORY_SPECIFIC_ATTRIBUTES_SUPPORTED: true
ATTRIBUTE_OPTIONS_SUPPORTED: true
PRODUCT_DYNAMIC_AVITO_VALUES_SUPPORTED: true
UNKNOWN_AVITO_ATTRIBUTE_PRESERVABLE: true
RAW_AVITO_VALUE_PRESERVED: true
REPEAT_SCHEMA_IMPORT_IDEMPOTENT: true
PRODUCT_WITHOUT_AVITO_DATA_STILL_VALID: true
BACKWARD_COMPATIBLE: true
OWNER_MANUAL_CHECK_REQUIRED: true
MASS_IMPORT_NOT_AUTHORIZED: true
REVERSE_SYNC_NOT_AUTHORIZED: true
DO_NOT_START_STAGE06A_R10_WITHOUT_OWNER_ACCEPTANCE: true
DO_NOT_START_STAGE06B_WITHOUT_OWNER_ACCEPTANCE: true
```

Если фундамент нельзя безопасно внедрить:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE06A_R9_AVITO_FIRST_CATEGORY_ATTRIBUTE_MODEL_BLOCKED
```

с конкретными blockers.

После отчёта ОСТАНОВИТЬСЯ.
