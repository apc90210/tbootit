# TECHNOREBOOT — Stage06A-R9-R2: Rich-Attribute Validation + Source Avito Link in Product Card

Репозиторий:

```powershell
C:\tbootit
```

Контекст:
- Stage06A-R9-R1 V2 завершён технически.
- Structured Avito category/characteristics уже проходят:
  Extension → Avito Module → Core → R9 model → Product detail.
- Product 58 / принтер оказался слабым OWNER-эталоном: у исходного объявления мало характеристик.
- Для качественной проверки нужен реальный товар с богатым набором Avito-параметров: предпочтительно монитор или материнская плата.
- Дополнительно Owner хочет видеть в карточке товара прямую ссылку на исходное объявление Avito.

Это небольшой validation/UX step ПЕРЕД Stage06A-R10.

НЕ начинать:
- canonical schema discovery всех категорий;
- reverse sync;
- массовый импорт;
- Stage06B.

# 1. ЦЕЛЬ

Сделать две вещи:

1. Добавить в карточку товара кликабельную ссылку:
   `Открыть объявление на Avito`
   ведущую на реальный `external_url`, из которого товар был импортирован.

2. Подготовить и выполнить техническую проверку structured characteristics на товаре с богатым набором параметров:
   `монитор` ИЛИ `материнская плата`
   если такой реальный Avito-import уже существует в БД.

Если такого товара в БД нет:
- НЕ выдумывать real fixture;
- НЕ подменять synthetic данные под видом реальных;
- подготовить OWNER-check, чтобы Owner импортировал один реальный монитор/материнскую плату через текущий extension.

# 2. ГЛАВНЫЙ ПРИНЦИП

Источник ссылки:
`ProductExternalListing.external_url`
или фактическое эквивалентное поле текущей модели.

Нельзя:
- строить Avito URL из title;
- угадывать URL по external_item_id, если реальный URL уже хранится;
- хардкодить avito.ru/item/{id};
- использовать тестовый URL в production UI.

Использовать только реально сохранённый source URL.

# 3. GIT/RUNTIME AUDIT

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

# 4. ПРОВЕРИТЬ ТЕКУЩУЮ МОДЕЛЬ EXTERNAL LISTING

Найти:
```text
ProductExternalListing
external_url
external_item_id
product_id
source/platform
```

Зафиксировать:
```text
SOURCE_LINK_MODEL
SOURCE_LINK_FIELD
```

Проверить, что для Product 58 уже есть реальный URL.

# 5. PRODUCT DETAILS API

Если `GET /api/products/{id}/details` сейчас не отдаёт source Avito URL:

добавить минимально:
```json
{
  "avito_source_url": "https://www.avito.ru/..."
}
```

или более структурированно:
```json
{
  "external_listing": {
    "source": "avito",
    "external_item_id": "...",
    "external_url": "..."
  }
}
```

Предпочесть структуру, которая не мешает будущим другим площадкам.

# 6. PRODUCT DETAIL UI

В карточке товара `/inventory/products/{id}` добавить компактный блок рядом с Avito-характеристиками:

```text
Источник: Avito
[Открыть объявление на Avito ↗]
```

Требования:
- кликабельно;
- `target="_blank"`;
- `rel="noopener noreferrer"`;
- URL не показывать длинной строкой;
- полностью русское описание;
- не показывать внутренние ID Owner-у.

Если source URL отсутствует:
```text
Ссылка на исходное объявление Avito не сохранена
```
или блок скрывается — выбрать более чистый вариант и покрыть тестом.

# 7. НЕ ЛОМАТЬ PLUGIN-ONLY UI

Главное меню остаётся:
`Расширение Avito`

Не возвращать старые import/sync/parser страницы.

Ссылка внутри карточки товара НЕ считается отдельным механизмом интеграции — это source reference.

# 8. НАЙТИ БОГАТЫЙ REAL TEST ITEM

Read-only проверить текущую БД на Avito-импортированные товары.

Искать по:
```text
title/category/source_attributes
```

Предпочтительно:
```text
monitor / монитор
motherboard / материнская плата
```

Для каждого кандидата посчитать:
```text
number of structured Avito attributes
```

Выбрать реальный товар с максимальным количеством подтверждённых характеристик.

Отчёт:
```text
RICH_TEST_PRODUCT_FOUND: true/false
RICH_TEST_PRODUCT_ID
RICH_TEST_EXTERNAL_ITEM_ID
RICH_TEST_CATEGORY
RICH_TEST_ATTRIBUTE_COUNT
```

# 9. ЕСЛИ REAL ITEM НЕ НАЙДЕН

Не создавать фальшивый production item.

Разрешены synthetic unit tests для pipeline, но OWNER-check должен быть:
`Owner импортирует через extension один реальный монитор или материнскую плату.`

В отчёте явно:
`RICH_REAL_OWNER_IMPORT_REQUIRED: true`

# 10. ЕСЛИ REAL ITEM НАЙДЕН

Для него проверить:
```text
category
source URL
brand
model
all structured characteristics
```

И дать provenance table:
```text
ATTRIBUTE_NAME
VALUE
SOURCE_RAW_PRESENT
STRUCTURED_VALUE_PRESENT
DISPLAYED_IN_PRODUCT_UI
```

# 11. НЕ ИЗМЕНЯТЬ EXTRACTION ЛОГИКУ БЕЗ ДОКАЗАННОЙ НЕОБХОДИМОСТИ

Этот stage НЕ должен снова переписывать extension extractor.

Если обнаружится, что monitor/motherboard characteristics не приходят:
- диагностировать;
- не делать большой R10 внутри этого step;
- указать blocker и остановиться.

# 12. TESTS

Добавить минимум:
```text
product details returns Avito source URL when saved
product details handles missing source URL
product detail renders "Открыть объявление на Avito"
source link has target=_blank
source link uses exact persisted external_url
product with no external_url does not render broken link
Avito characteristics block still renders
```

Если в БД/fixtures есть rich item:
`rich Avito attributes render as expected`

# 13. SECURITY

Перед выводом ссылки:
- использовать только persisted HTTP/HTTPS URL;
- желательно разрешать только `avito.ru` / `www.avito.ru` для Avito source UI;
- не выводить javascript/data URLs;
- URL экранируется шаблонизатором.

Если URL невалиден:
`не делать кликабельную ссылку`

# 14. FULL REGRESSION

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
docker compose exec -T inventory-sales-module pytest
docker compose exec -T avito-module pytest
docker compose exec -T repairs-module pytest
pytest admin-shell/tests
pytest chrome-extension/technoreboot-avito/tests
```

Указать фактические counts.

# 15. RUNTIME

Проверить:
```text
/inventory/products/58 → 200
/avito/extension → 200
```

Если найден rich product:
`/inventory/products/{rich_product_id} → 200`

# 16. EXTENSION VERSION

Если extension runtime code НЕ меняется:
`НЕ bump version`

Этот step в норме должен быть Core/UI-only.

# 17. DOCUMENTATION

Создать:
```text
reports/stage06a_r9_r2_rich_attribute_validation_source_link_report.md
```

Обновить:
`logs/2026-08-21.md`

Сохранить prompt:
`.agents/received_prompts/TECHNOREBOOT_STAGE06A_R9_R2_RICH_ATTRIBUTE_VALIDATION_SOURCE_LINK_PROMPT.md`

# 18. REPORT STRUCTURE

```text
STATUS
SOURCE_LINK_MODEL
SOURCE_LINK_FIELD
PRODUCT_58_SOURCE_URL_PRESENT
PRODUCT_DETAILS_API_CHANGE
PRODUCT_UI_CHANGE
URL_VALIDATION
RICH_TEST_PRODUCT_FOUND
RICH_TEST_PRODUCT_ID
RICH_TEST_EXTERNAL_ITEM_ID
RICH_TEST_CATEGORY
RICH_TEST_ATTRIBUTE_COUNT
RICH_ATTRIBUTE_PROVENANCE
RICH_REAL_OWNER_IMPORT_REQUIRED
PLUGIN_ONLY_UI_PRESERVED
EXTENSION_CHANGED
EXTENSION_VERSION
TESTS
RUNTIME
FILES_CHANGED
COMMIT
PUSH
FINAL_GIT_STATUS
OWNER_CHECK_GUIDE
FINAL_STATUS
```

# 19. DEFINITION OF DONE

PASS only if:
```text
AVITO_SOURCE_LINK_AVAILABLE_IN_PRODUCT_CARD: true
SOURCE_LINK_USES_PERSISTED_EXTERNAL_URL: true
SOURCE_LINK_SAFE_AND_CLICKABLE: true
PRODUCT_DETAIL_STILL_WORKS: true
AVITO_CHARACTERISTICS_STILL_RENDER: true
PLUGIN_ONLY_UI_PRESERVED: true
NO_INVENTED_REAL_AVITO_DATA: true
OWNER_MANUAL_CHECK_REQUIRED: true
```

И одно из двух:
```text
RICH_TEST_PRODUCT_FOUND: true
```
или:
```text
RICH_REAL_OWNER_IMPORT_REQUIRED: true
```

# 20. OWNER CHECK GUIDE

Если rich real item уже найден:
```text
1. Открыть его карточку в Техноребуте.
2. Нажать «Открыть объявление на Avito».
3. Убедиться, что открывается именно исходное объявление.
4. Сравнить 5–10 характеристик на Avito и в Техноребуте.
5. Проверить brand/model/category.
```

Если rich item НЕ найден:
```text
1. Найти на Avito реальный монитор или материнскую плату с большим количеством характеристик.
2. Импортировать через extension v0.2.10.
3. Открыть созданный товар.
4. Нажать ссылку на исходное Avito.
5. Сравнить характеристики side-by-side.
```

После OWNER acceptance:
`Stage06A-R10 — Canonical Avito schema discovery`

# 21. GIT SAFETY

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
`Add Avito source link and rich attribute validation`

После отчёта ОСТАНОВИТЬСЯ.
