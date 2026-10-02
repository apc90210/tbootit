# PROMPT_WEB_07B_VERIFIED_REFERENCE_CATALOG_EXPANSION

## Роль

Ты — AntiGravity.

Проекты:

- Core: `C:\tbootit`
- Web: `C:\tboot-site`

## Исходное состояние

WEB-07A CLOSED / PASS.

Уже реализовано и НЕ должно переделываться:

- Core-owned `product_reference_models`;
- `product_reference_aliases`;
- deterministic matcher;
- safe auto-enrichment;
- provenance fields в Product;
- `needs_review`;
- JSON import/export reference catalog;
- backfill;
- manual create / JSON import / Avito integration;
- категория `Техника под восстановление` имеет абсолютный приоритет;
- existing Product values > reference defaults.

## Цель WEB-07B

Массово расширить внутренний справочник моделей техники на основе АКТУАЛЬНОЙ локальной товарной базы.

Главная задача:

1. проанализировать все текущие товары;
2. найти модели, которых ещё нет в reference catalog;
3. сгруппировать одинаковые модели;
4. подготовить VERIFIED candidate manifest;
5. автоматически добавить только те reference models, которые можно доказать из уже имеющихся локальных данных;
6. всё спорное оставить в `needs_review`;
7. максимально увеличить долю товаров, которые автоматически получают:
   - brand;
   - model;
   - category;
   - specifications;
   - site_title;
   - site_description;
8. ничего не выдумывать.

Production НЕ трогать.

---

# 1. PRODUCTION BOUNDARY

ТОЛЬКО LOCAL.

Запрещено:

- production writes;
- VDS DB/media changes;
- deploy;
- production migration;
- local -> VDS;
- изменение production reference catalog.

В отчёте:

`PRODUCTION_WRITES=0`

---

# 2. SOURCE OF TRUTH

Для WEB-07B допустимые источники данных:

## A. Existing local Product data

Основной источник.

Использовать:

- title;
- site_title;
- description;
- brand;
- model;
- category;
- specifications/characteristics;
- существующие aliases;
- reference_model linkage;
- несколько одинаковых экземпляров одной модели.

## B. Existing verified Reference Catalog

27 уже проверенных моделей из WEB-07A.

## C. Existing project-owned structured data

Если в репозитории уже есть ранее сохранённые характеристики/JSON/импортированные карточки:
- можно использовать;
- provenance обязателен.

---

# 3. INTERNET / EXTERNAL DATA

На ЭТОМ этапе AntiGravity самостоятельно не должен придумывать или искать характеристики в интернете.

Если модели недостаточно описаны локальными данными:

- создать candidate;
- identity можно добавить только если brand/model доказаны;
- specifications оставить пустыми;
- status/review = `needs_external_enrichment` или эквивалент.

То есть:

`Нет доказанного значения -> не заполнять.`

---

# 4. CURRENT CATALOG ANALYSIS

Проанализировать все текущие local Products.

Зафиксировать:

- total products;
- already linked to reference;
- confidently matchable existing reference;
- currently unmatched;
- ambiguous;
- restoration;
- parts/consumables;
- bundles/multiple models.

Сгруппировать unmatched Products по normalized:

- brand;
- model;
- title signature.

---

# 5. PRIORITY CATEGORIES FOR EXPANSION

Обрабатывать в таком порядке:

1. Принтеры
2. МФУ
3. Мониторы
4. Ноутбуки
5. Компьютеры
6. Комплектующие
7. Техника под восстановление — только reference identity/spec enrichment, категория остаётся restoration
8. Без категории

Причина порядка:
принтеры/МФУ/мониторы обычно лучше определяются по стабильной модели.

---

# 6. MODEL IDENTITY RULES

Reference model можно auto-create только если модель идентифицирована однозначно.

Минимум одно из условий:

## Rule A — explicit brand + model fields

Product уже содержит:
- непустой brand;
- непустой model.

И нет конфликтов с другими Products того же signature.

## Rule B — repeated exact normalized title signature

Несколько товаров имеют однотипное название с одинаковой моделью.

## Rule C — title contains strong brand/model signature

Например концептуально:

`HP LaserJet 1320`

при отсутствии конфликтующей модели.

---

# 7. DO NOT AUTO-CREATE

Не создавать автоматически reference model для:

- `Принтер HP`;
- `Монитор Samsung`;
- `Ноутбук Lenovo`;
- generic title без model;
- перечисления моделей;
- комплектов;
- запчастей, если они похожи на имя устройства;
- расходников;
- неоднозначной модели;
- model family без exact model.

Такие записи:
`needs_review`.

---

# 8. SUFFIX SAFETY

Строго различать:

- `1320` / `1320n`;
- `P2040` / `P2040dn`;
- `M428fdn` / `M428fdw`;
- `T480` / `T480s`;
- любые значимые suffix.

Не объединять только потому, что начало модели совпадает.

---

# 9. GROUP CONSISTENCY AUDIT

Для каждой proposed reference group проверить:

- category consistency;
- brand consistency;
- model consistency;
- conflicting specs;
- conflicting device types.

Если конфликт:
не auto-create.

Создать reason:
`conflicting_source_products`.

---

# 10. SPECIFICATION AGGREGATION

Reference specification можно добавить только если:

1. значение уже присутствует в одном или нескольких local Products;
2. нет противоречащего значения в группе;
3. поле является model-level characteristic, а не instance-level.

## Допустимо

Например:
- технология печати;
- формат;
- интерфейсы;
- разрешение;
- диагональ;
- тип матрицы;
- стандартная модель CPU, только если она действительно фиксирована для reference model;
- manufacturer model attributes.

## Нельзя переносить в reference specs

- цена;
- закупочная цена;
- серийник;
- пробег/счётчик конкретного аппарата;
- износ;
- состояние;
- дефекты;
- комплект конкретного экземпляра;
- заметки;
- дата поступления;
- конкретные фотографии.

---

# 11. LAPTOP / PC SPECIAL SAFETY

Ноутбуки и компьютеры могут иметь разные конфигурации в рамках одной модели.

Поэтому:

- chassis/model-level характеристики можно reference;
- RAM/SSD/HDD/CPU/GPU НЕ считать default model specs, если среди local Products есть разные конфигурации;
- если Product уже имеет свои CPU/RAM/storage — reference никогда их не перетирает;
- при сомнении не переносить конфигурационный параметр.

---

# 12. SITE TITLE

Reference `site_title` может быть автоматически сформирован ТОЛЬКО из доказанных:

`device type + brand + model`

Примеры структуры:

- `Принтер HP LaserJet 1320`
- `МФУ Kyocera ECOSYS M2040dn`
- `Монитор Samsung S24F350`

Не добавлять рекламные эпитеты.

---

# 13. SITE DESCRIPTION

Не генерировать красивые маркетинговые тексты из воздуха.

На WEB-07B:

- если локальное verified description одинаково/совместимо — можно использовать;
- иначе оставить reference `site_description` пустым.

Массовую генерацию текстов вынести в отдельный будущий этап.

---

# 14. ALIASES

Для каждой новой reference model автоматически формировать только безопасные aliases:

- exact existing local Product title variant;
- `brand + model`;
- canonical_name;
- очевидная нормализация punctuation/spacing.

Не создавать:
- слишком короткие numeric-only aliases;
- generic brand-only;
- device-type-only.

Каждый alias должен иметь provenance/source.

---

# 15. CANDIDATE ARTIFACT

До apply создать:

`REFERENCE_EXPANSION_CANDIDATES.json`

Для каждого candidate:

```json
{
  "proposed_canonical_name": "...",
  "brand": "...",
  "model": "...",
  "category": "...",
  "source_product_ids": [],
  "source_titles": [],
  "aliases": [],
  "specifications": {},
  "conflicts": [],
  "decision": "auto_create|needs_review|skip",
  "reason": "...",
  "confidence": 1.0
}
```

---

# 16. DRY-RUN

Создать/расширить script:

`scripts/expand_reference_catalog.py`

Modes:

```powershell
python scripts/expand_reference_catalog.py --dry-run
python scripts/expand_reference_catalog.py --apply
```

Dry-run должен вывести:

- candidates total;
- auto-create;
- needs_review;
- skipped;
- expected new aliases;
- expected newly matchable Products.

Никаких DB writes.

---

# 17. APPLY LOCAL

После успешного dry-run:

```powershell
python scripts/expand_reference_catalog.py --apply
```

ТОЛЬКО LOCAL.

Создать reference models лишь для `auto_create`.

Для каждого:
- provenance;
- aliases;
- source Product IDs;
- specs provenance.

---

# 18. RE-RUN PRODUCT BACKFILL

После expansion:

```powershell
python scripts/backfill_product_references.py --dry-run
```

Затем apply разрешён локально для high-confidence matches:

```powershell
python scripts/backfill_product_references.py --apply
```

Сохранить before/after metrics.

---

# 19. METRICS

Обязательно показать:

## Before

- reference models;
- aliases;
- linked Products;
- unlinked;
- needs_review.

## After

- reference models;
- aliases;
- linked Products;
- unlinked;
- needs_review.

И:

`coverage = linked_products / eligible_products`

Отдельно по категориям.

---

# 20. COVERAGE BY CATEGORY

Таблица:

| Category | Products | Linked before | Linked after | Coverage |
|---|---:|---:|---:|---:|
| Принтеры | | | | |
| МФУ | | | | |
| Мониторы | | | | |
| Ноутбуки | | | | |
| Компьютеры | | | | |
| Комплектующие | | | | |
| Техника под восстановление | | | | |
| Без категории | | | | |

---

# 21. NEEDS REVIEW QUEUE

Сформировать:

`REFERENCE_NEEDS_REVIEW.json`

Причины минимум:

- missing_model;
- ambiguous_model;
- conflicting_specs;
- multiple_models;
- parts_or_consumable;
- generic_title;
- unsafe_alias;
- unknown_brand.

Owner не должен разбирать это сейчас вручную.

Артефакт нужен для будущих этапов.

---

# 22. WEB VERIFICATION

После apply открыть:

`http://localhost:8090`

Проверить минимум:

- 10 newly linked printers/MFP;
- 5 monitors;
- 5 laptops/PC if available;
- restoration products.

Для каждого:
- title;
- category;
- brand;
- model;
- specifications;
- photo;
- price;
- restoration category preservation.

---

# 23. NO PRODUCT DAMAGE

Проверить, что expansion/backfill НЕ изменили:

- prices;
- stock;
- statuses;
- sales;
- repair records;
- reservation records;
- photos;
- serial numbers;
- condition;
- individual notes.

Сделать before/after checksum/field comparison для этих полей.

---

# 24. TESTS

Запустить:

- all product-reference tests;
- product create/import tests;
- Avito integration relevant tests;
- relevant Web catalog/product tests.

Все green.

---

# 25. DB HEALTH

После apply:

- `PRAGMA quick_check = ok`
- `PRAGMA integrity_check = ok`
- `PRAGMA foreign_key_check = []`

---

# 26. GIT

Коммитить только:

- code;
- scripts;
- docs;
- reference JSON catalog;
- Outbox candidate/review artifacts, если policy проекта это допускает.

НЕ коммитить:

- DB;
- media;
- backups;
- secrets.

Рекомендуемый Core commit:

`WEB-07B expand verified product reference catalog`

Web/Outbox:

`WEB-07B add reference expansion audit artifacts`

Оба repo clean.

---

# 27. OUTBOX

Создать:

`C:\tboot-site\AntiGravity\PROMPT_WEB_07B_VERIFIED_REFERENCE_CATALOG_EXPANSION\Outbox\`

Минимум:

- `WEB_07B_REPORT.md`
- `REFERENCE_EXPANSION_CANDIDATES.json`
- `REFERENCE_NEEDS_REVIEW.json`

Отчёт:

## Before
metrics.

## Candidate analysis
counts.

## Added reference models
count/list.

## Added aliases
count.

## Specifications provenance
count/source.

## Backfill
before/after.

## Coverage
overall + by category.

## Safety
unchanged business fields.

## Tests
exact results.

## DB health
exact results.

## Production
`PRODUCTION_WRITES=0`

## Git
commits/clean.

## Кто исполнял
AntiGravity.

---

# 28. ACCEPTANCE CRITERIA — WEB-07B PASS

PASS только если:

- WEB-07A architecture не сломана;
- новые reference models доказаны local source data;
- no invented characteristics;
- all aliases safe/provenanced;
- ambiguity stays needs_review;
- meaningful coverage increase achieved;
- restoration rule preserved;
- instance Product values not overwritten;
- tests green;
- DB healthy;
- production writes = 0;
- repos clean;
- Outbox complete.

После PASS:

ОСТАНОВИТЬСЯ.

Следующий этап:
`WEB-07C — External Verified Enrichment`

Там уже можно будет использовать внешний web-research/ChatGPT для заполнения недостающих характеристик по моделям из `REFERENCE_NEEDS_REVIEW.json`, с обязательным source provenance.
