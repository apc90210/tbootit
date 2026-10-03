# PROMPT_WEB_07D_REFERENCE_CATALOG_OWNER_REVIEW_UI

## Роль
Ты — AntiGravity.

Репозитории:
- Core: `C:\tbootit`
- Admin-Shell: внутри `C:\tbootit`
- Public Web: `C:\tboot-site`

## Контекст
WEB-07A / 07B / 07C закрыты PASS.

Сейчас:
- Core DB — единственный runtime source of truth Reference Catalog;
- 125 reference models;
- 217 Products связаны с reference;
- Batch 01 external enrichment добавил verified specs для 40 моделей;
- provenance/conflicts/unresolved уже существуют;
- public site НЕ должен становиться admin-системой.

## Цель
Сделать OWNER-only интерфейс управления Reference Catalog и review queue.

ВАЖНО:
UI размещать в существующем внутреннем Admin-Shell / owner contour, НЕ в публичном `tboot-site`.

Никакой отдельной reference DB не создавать.

---

# 1. Перед работой

Проверить:
- `git status`
- текущие Core reference API;
- Admin-Shell auth/OWNER pattern;
- существующие reference models / aliases / provenance / conflicts;
- WEB-07C artifacts.

Production не трогать.

`PRODUCTION_WRITES=0`

---

# 2. OWNER UI

Добавить внутреннюю страницу, например:

`Reference Catalog`

Функции:

### Список моделей
Показывать:
- canonical name;
- brand;
- model;
- category/device type;
- число aliases;
- число specifications;
- verification/source state;
- linked Products count;
- conflict/review status.

Фильтры:
- brand;
- category;
- verified / needs_review / conflict;
- incomplete specs;
- search by model/alias.

### Детальная карточка Reference Model
Показывать:
- canonical identity;
- aliases;
- specifications;
- provenance/source;
- linked Products;
- conflicts;
- external source URLs where present.

---

# 3. Безопасные OWNER-действия

Разрешить:

- edit canonical name/brand/model;
- add/remove/deactivate alias;
- edit/add specification;
- mark field/model verified;
- resolve conflict вручную;
- select correct reference candidate for Product;
- reject wrong reference match;
- re-run canonical enrichment preview/apply for Product;
- create reference from confirmed Product.

Все mutation actions:
- OWNER-only;
- через Core API;
- audit logged;
- no direct DB writes from Admin-Shell.

---

# 4. Product instance protection

Reference UI НИКОГДА не должен редактировать как model-level data:

- price;
- quantity;
- condition;
- serial;
- barcode;
- photos;
- defects;
- notes;
- storage location;
- Avito listing.

Показать linked Product только как отдельный instance.

---

# 5. Conflict / Review queue

Сделать отдельный блок:

`Требуют проверки`

Показывать:
- ambiguous model;
- conflicting specs;
- low confidence;
- unresolved Product;
- external enrichment conflicts.

Для каждой записи OWNER должен понимать:
- что именно неясно;
- какие candidates;
- какие source values конфликтуют;
- какое действие можно подтвердить.

---

# 6. Canonical services

UI не должен содержать matching/enrichment business logic.

Использовать:
- canonical Core matcher;
- canonical Safe Enricher;
- Core reference APIs.

Если нужного Core endpoint нет:
добавить минимальный Core endpoint.
Не реализовывать merge/scoring в Admin-Shell.

---

# 7. Product enrichment controls

Для linked/unlinked Product предусмотреть:

- `Preview enrichment`
- `Apply enrichment`
- `Reject match`
- `Select reference`

Но только через Core canonical contracts.

Existing Product values имеют приоритет.
Restoration category сохраняется.

---

# 8. Audit

Каждое OWNER mutation:
- actor;
- action;
- reference_model_id/product_id;
- before/after;
- timestamp.

Использовать существующий audit mechanism.

---

# 9. Tests

Запустить:

- Core reference tests;
- external enrichment tests;
- новые owner management API tests;
- Admin-Shell owner UI tests;
- existing Admin-Shell regression tests;
- DB quick_check;
- foreign_key_check.

Проверить:
- USER cannot mutate;
- OWNER can mutate;
- no business Product instance fields изменены;
- public `tboot-site` не получил admin endpoints/pages.

---

# 10. Outbox

Создать:

`C:\tbootit\AntiGravity\PROMPT_WEB_07D_REFERENCE_CATALOG_OWNER_REVIEW_UI\Outbox\`

Минимум:
- `WEB_07D_REPORT.md`
- screenshots/

В отчёте:

## Current API reused
## New API added
## Owner UI
## Review/conflict workflow
## Audit
## Security
## Tests
## DB health
## Git
## Production
`PRODUCTION_WRITES=0`

---

# 11. Git

Отдельный commit:

`WEB-07D add owner reference catalog review UI`

Не коммитить DB/media/secrets.

После работы tracked worktree clean.

---

# 12. PASS

PASS если:

- Reference Catalog управляется через OWNER UI;
- Core остаётся единственным source of truth;
- Admin-Shell содержит только presentation/orchestration;
- matcher/enricher не дублируются;
- conflicts/review queue видимы;
- Product instance data защищены;
- audit работает;
- USER mutation blocked;
- tests green;
- DB healthy;
- public site не превращён в admin UI;
- production writes = 0;
- repo clean.

После PASS остановиться.

Следующий этап НЕ начинать автоматически.
