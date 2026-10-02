# PROMPT_WEB_07C_EXTERNAL_VERIFIED_REFERENCE_ENRICHMENT

## Роль

Ты — AntiGravity.

Проекты:

- Core: `C:\tbootit`
- Web: `C:\tboot-site`

## Исходное состояние

WEB-07A CLOSED / PASS.
WEB-07B функционально принят как база для следующего этапа.

После WEB-07B заявлено:

- reference models: 125;
- aliases: 579;
- linked Products: 217 / 421 = 51.5%;
- structured-category coverage: 65.4%;
- Принтеры: 91.4%;
- МФУ: 92.2%;
- Мониторы: 30.4%;
- Ноутбуки: 78.6%;
- Компьютеры: 40.0%;
- Комплектующие: 15.5%;
- Техника под восстановление: 92.3%;
- Без категории: 0%.

Архитектуру WEB-07A/07B НЕ переделывать.

---

# 0. ОБЯЗАТЕЛЬНЫЙ PREFLIGHT CLOSEOUT WEB-07B

Перед любой новой разработкой закрыть две отчётные неоднозначности.

## 0.1. needs_review semantics

В WEB-07B одновременно указано:

- `needs_review = 60`;
- `199 unresolved`.

Нужно дать точное определение каждого числа.

Например:
- 60 review groups/candidates;
- 199 Products unresolved;

или другое фактическое значение.

Вывести таблицу:

| Metric | Count | Meaning |
|---|---:|---|
| Review candidate groups | | |
| Unresolved Products | | |
| Linked Products | | |
| Total Products | 421 | |

Проверить арифметику:
`linked + unresolved == total` если множества действительно комплементарны.

Если нет — объяснить остальные состояния.

## 0.2. repair_orders safety

WEB-07B prompt запрещал изменение repair records.

В trace был отдельный forensic check `repair_orders`, но итоговый safety-report его не зафиксировал.

Нужно ДОКАЗАТЬ:

- WEB-07B не изменял `repair_orders`;
- WEB-07B не изменял repair history/status tables;
- если текущий `safety_baseline.json` старый и уже не соответствует состоянию перед WEB-07B — это явно доказать через:
  - git/timestamps;
  - pre-stage snapshot;
  - staging snapshot;
  - audit logs;
  - либо другой надёжный источник.

Если обнаружено изменение, которое мог внести WEB-07B:
`STOP — BUSINESS_DATA_SAFETY_NOT_PROVEN`

Не продолжать WEB-07C.

---

# 1. ЦЕЛЬ WEB-07C

Создать контролируемый процесс внешнего VERIFIED enrichment для внутреннего reference catalog.

Основная задача:

1. взять unresolved/needs-review модели и reference models с неполными specifications;
2. точно идентифицировать модель;
3. получить технические характеристики из внешних проверяемых источников;
4. сохранить provenance источников;
5. подготовить verified JSON enrichment packages;
6. импортировать только доказанные данные;
7. повысить качество карточек сайта и процент автоматически заполненных характеристик;
8. не выдумывать ни одного технического параметра.

---

# 2. PRODUCTION BOUNDARY

Весь этап — LOCAL ONLY.

Запрещено:

- production deploy;
- production DB writes;
- VDS schema changes;
- VDS reference catalog changes;
- local -> VDS copy.

`PRODUCTION_WRITES=0`

---

# 3. ПРИОРИТЕТ РАБОТЫ

Не пытаться исследовать все 199 unresolved Products одновременно.

Работать BATCH-ами.

## Batch 1

Приоритет:

1. Принтеры
2. МФУ
3. Мониторы

Цель Batch 1:

- максимум 40 уникальных reference models/candidates;
- выбирать модели с точной идентификацией;
- предпочтительно модели, встречающиеся более одного раза;
- затем одиночные, если exact model очевидна.

Но если unresolved принтеров/МФУ уже мало:
- добрать мониторами;
- потом ноутбуками.

---

# 4. SOURCE QUALITY HIERARCHY

Использовать источники строго по приоритету:

## Tier A — предпочтительно

1. официальный сайт производителя;
2. официальная support/product page;
3. официальный datasheet;
4. официальный manual/user guide/service manual;
5. официальный archived support page.

## Tier B — допустимо при отсутствии Tier A

- официальные региональные сайты производителя;
- официальные PDF-зеркала производителя;
- vendor documentation repositories с доказанным manufacturer origin.

## Tier C — только как вспомогательная сверка

- крупные технические каталоги;
- reputable distributors;
- reputable review/spec databases.

Tier C НЕ должен быть единственным источником критичного параметра, если Tier A/B доступен.

---

# 5. ЗАПРЕЩЁННЫЕ ИСТОЧНИКИ

Не использовать как proof:

- маркетплейсы;
- объявления;
- Avito;
- случайные интернет-магазины;
- SEO-generated specs;
- форумы;
- Reddit;
- AI-generated pages;
- агрегаторы без source provenance;
- snippets поисковика без открытия источника.

---

# 6. EXACT MODEL IDENTITY FIRST

Перед сбором specs модель должна быть идентифицирована.

Для каждого candidate:

- brand;
- exact model;
- suffix;
- revision/variant если значимо;
- device type.

Нельзя смешивать:

- 1320 vs 1320n;
- M428fdn vs M428fdw;
- P2040dn vs P2040dw;
- T480 vs T480s;
- разные regional variants, если specs различаются.

Если identity uncertain:
`needs_identity_review`
и НИКАКОГО enrichment.

---

# 7. FIELD-LEVEL PROVENANCE

Внешний enrichment должен иметь provenance для КАЖДОГО поля.

Создать/использовать структуру вроде:

```json
{
  "stable_key": "hp|laserjet-1320",
  "canonical_name": "HP LaserJet 1320",
  "sources": [
    {
      "source_id": "src1",
      "url": "https://...",
      "publisher": "HP",
      "source_type": "official_datasheet",
      "retrieved_at": "2026-10-02"
    }
  ],
  "fields": {
    "print_technology": {
      "value": "laser",
      "source_ids": ["src1"]
    },
    "max_print_resolution": {
      "value": "1200 x 1200 dpi",
      "source_ids": ["src1"]
    }
  }
}
```

Схема может отличаться, но provenance должен быть machine-readable.

---

# 8. RAW SOURCE ARCHIVE

Для каждого Batch сохранить:

`Outbox/sources/`

Минимум:

- source manifest;
- URLs;
- title/publisher;
- retrieval date;
- sha256 скачанного PDF/HTML snapshot, если файл сохраняется локально.

НЕ коммитить огромные PDF-файлы без необходимости.

Можно хранить manifest + hashes + URLs.

---

# 9. CANONICAL CHARACTERISTIC KEYS

Не плодить сотни названий одного поля.

Создать canonical characteristic vocabulary.

Для принтеров/МФУ минимум:

- device_type
- print_technology
- color_mode
- max_format
- print_speed_a4_mono
- print_speed_a4_color
- print_resolution
- duplex
- network_ethernet
- wifi
- usb
- scanner
- scanner_resolution
- adf
- fax
- monthly_duty_cycle
- recommended_monthly_volume
- first_page_time
- memory
- dimensions
- weight

Заполнять только реально подтверждённые поля.

Для мониторов минимум:

- diagonal
- native_resolution
- panel_type
- aspect_ratio
- refresh_rate
- response_time
- brightness
- contrast
- video_inputs
- vesa
- speakers
- dimensions
- weight

Для ноутбуков/ПК:
осторожно с конфигурационными параметрами.

---

# 10. MODEL-LEVEL VS INSTANCE-LEVEL

Reference catalog хранит model-level facts.

НЕ переносить из внешнего источника в конкретный Product:

- цену;
- состояние;
- defects;
- serial;
- photos;
- пробег;
- счётчик;
- текущую RAM/SSD, если модель продавалась в разных конфигурациях;
- конкретный CPU/GPU, если серия имеет варианты.

Если характеристика вариативна:
- либо не добавлять;
- либо хранить как model family capability/range только если schema это поддерживает;
- Product existing config имеет абсолютный приоритет.

---

# 11. VERIFIED ENRICHMENT PACKAGE

Для каждого Batch создать:

`EXTERNAL_ENRICHMENT_BATCH_01.json`

Состав:

- stable_key;
- canonical_name;
- identity proof;
- aliases if externally confirmed;
- category/device_type;
- specifications;
- sources;
- field-level provenance;
- conflicts;
- decision:
  - `verified_apply`
  - `identity_only`
  - `needs_review`
  - `rejected`

---

# 12. VALIDATOR

Создать:

`scripts/validate_external_reference_enrichment.py`

Проверки:

- JSON schema;
- stable_key exists/valid;
- no duplicate stable_key;
- every specification has source;
- every source has URL/publisher/type;
- no forbidden fields;
- no instance-level values;
- no unsupported alias;
- no conflicting source values silently merged.

---

# 13. DRY-RUN IMPORT

Создать/расширить import workflow:

```powershell
python scripts/import_external_reference_enrichment.py EXTERNAL_ENRICHMENT_BATCH_01.json --dry-run
```

Вывести:

- models updated;
- models created;
- fields added;
- aliases added;
- conflicts;
- skipped;
- affected Products;
- Products that would gain visible specs.

Никаких writes.

---

# 14. APPLY LOCAL

После green validation + dry-run:

```powershell
python scripts/import_external_reference_enrichment.py EXTERNAL_ENRICHMENT_BATCH_01.json --apply
```

ТОЛЬКО LOCAL.

Rules:

- Product existing values win;
- existing verified reference field не перетирать другим значением автоматически;
- conflict -> needs_review;
- restoration category untouched.

---

# 15. EXTERNAL FIELD CONFLICTS

Если два официальных источника расходятся:

НЕ выбирать молча.

Создать:

```json
{
  "status": "conflict",
  "field": "...",
  "values": [
    {"value": "...", "source": "..."},
    {"value": "...", "source": "..."}
  ]
}
```

Не применять поле до resolution.

---

# 16. DESCRIPTION GENERATION

На WEB-07C допускается создание нейтрального `site_description` ТОЛЬКО из verified structured facts.

Текст должен быть:

- короткий;
- технический;
- без маркетинговых обещаний;
- без invented claims;
- без состояния конкретного экземпляра.

Пример структуры:

`Монохромный лазерный принтер формата A4 с автоматической двусторонней печатью и Ethernet.`

Только если все перечисленные свойства подтверждены.

---

# 17. SOURCE LABEL

Reference model должен различать:

- `local_existing_products`
- `external_verified`
- `mixed_verified`

Если модель уже была создана локально и позже enrichment пришёл извне:
`source = mixed_verified` или эквивалент.

Не потерять первоначальный provenance.

---

# 18. WEBSITE RESULT

После apply Web автоматически использует enriched Core Product.

Проверить:

- specifications table;
- site_title;
- site_description;
- categories;
- photos;
- prices;
- restoration.

Не создавать внешнюю DB внутри Web.

---

# 19. WEB VERIFICATION

Проверить минимум 20 enriched Products Batch 1.

Для каждого:

- exact model;
- visible technical characteristics;
- no contradictory instance data;
- photo still works;
- price unchanged;
- status unchanged.

Сделать screenshots минимум:

- 3 printer details;
- 3 MFP details;
- 3 monitor details;
- 1 restoration item.

---

# 20. COVERAGE METRICS

До/после Batch 1:

- reference models with >=5 verified specs;
- Products with >=5 displayed specs;
- Products linked to references;
- unresolved Products;
- needs_identity_review;
- external_verified models.

По категориям.

---

# 21. QUALITY TARGET

Не гнаться за 100% любой ценой.

Приоритет:

`точность > количество`.

PASS возможен даже если часть моделей осталась unresolved.

Нельзя снижать threshold ради процента coverage.

---

# 22. SAFETY SNAPSHOT BEFORE APPLY

Перед external apply создать локальный safety snapshot:

- canonical DB backup;
- hashes:
  - product business fields;
  - sales;
  - sale_items;
  - repair_orders;
  - repair history/status tables;
  - reservation_requests;
  - product_photos.

После apply сравнить.

Все таблицы business data должны совпасть, кроме разрешённых reference/enrichment fields.

---

# 23. TESTS

Запустить:

- all reference tests;
- product create/import tests;
- Avito tests;
- Web catalog/product tests;
- external enrichment validator tests.

Добавить tests:

- missing provenance rejected;
- conflicting source rejected;
- forbidden instance field rejected;
- verified field accepted;
- existing Product value wins;
- restoration preserved.

---

# 24. DB HEALTH

После apply:

- quick_check = ok;
- integrity_check = ok;
- foreign_key_check = clean.

---

# 25. GIT

Коммитить:

- scripts;
- schema/services;
- JSON enrichment packages;
- source manifests;
- docs;
- Outbox reports.

НЕ коммитить:

- DB;
- downloaded huge source PDFs unless explicitly justified;
- media;
- secrets;
- backups.

Core commit:

`WEB-07C add externally verified reference enrichment pipeline`

Batch data commit:

`WEB-07C add verified reference enrichment batch 01`

Web/Outbox:

`WEB-07C add external enrichment audit artifacts`

Оба repo clean.

---

# 26. OUTBOX

Создать:

`C:\tboot-site\AntiGravity\PROMPT_WEB_07C_EXTERNAL_VERIFIED_REFERENCE_ENRICHMENT\Outbox\`

Минимум:

- `WEB_07C_REPORT.md`
- `EXTERNAL_ENRICHMENT_BATCH_01.json`
- `EXTERNAL_SOURCE_MANIFEST.json`
- `EXTERNAL_ENRICHMENT_CONFLICTS.json`
- `UNRESOLVED_AFTER_BATCH_01.json`
- screenshots/

---

# 27. REPORT

## WEB-07B preflight closeout
- needs_review semantics;
- unresolved arithmetic;
- repair data safety proof.

## Research scope
- number of models researched;
- categories.

## Source quality
- Tier A/B/C counts.

## Applied
- models created/updated;
- fields added;
- aliases added.

## Conflicts
- unresolved fields/models.

## Coverage
- before/after.

## Website
- exact examples verified.

## Business safety
- pre/post hashes including repairs.

## Tests
- exact results.

## DB
- integrity.

## Production
`PRODUCTION_WRITES=0`

## Git
- commits;
- clean.

## Кто исполнял
AntiGravity.

---

# 28. STOP CONDITIONS

Немедленно STOP если:

- repair/business safety WEB-07B не доказана;
- external source provenance отсутствует;
- model identity ambiguous;
- source conflicts нельзя разрешить;
- importer пытается перезаписать instance Product data;
- production write detected.

---

# 29. ACCEPTANCE — WEB-07C PASS

PASS только если:

- WEB-07B safety ambiguity закрыта;
- external research имеет machine-readable provenance;
- exact model identity доказана;
- no invented specs;
- field-level sources сохранены;
- validator работает;
- dry-run/import работают;
- conflicts безопасно блокируются;
- Product explicit values preserved;
- restoration preserved;
- business tables including repairs unchanged;
- site реально показывает enriched specs;
- tests green;
- DB healthy;
- production writes = 0;
- repos clean.

После PASS остановиться.

Следующий этап:
`WEB-07D — Reference Catalog Review UI / Owner Management`

Цель будущего 07D:
дать Owner удобный веб-интерфейс для просмотра reference models, needs_review, conflicts, ручного подтверждения и редактирования справочника без CLI.
