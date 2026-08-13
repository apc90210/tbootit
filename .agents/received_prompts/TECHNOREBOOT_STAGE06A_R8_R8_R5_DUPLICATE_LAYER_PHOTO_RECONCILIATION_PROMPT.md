# TECHNOREBOOT — Stage06A-R8-R8-R5 Exact Duplicate Layer Proof + Avito Photo Set Reconciliation

Репозиторий:

```powershell
C:\tbootit
```

Это corrective-stage внутри Stage06A-R8-R8.

НЕ начинать:
- Stage06A-R9
- Stage06B
- любой следующий функциональный этап

Предыдущий статус:

```text
TECHNOREBOOT_STAGE06A_R8_R8_R4_EXACT_PHOTO_IDENTITY_DYNAMIC_VERSION_READY_FOR_OWNER_CHECK
```

OWNER CHECK R8-R8-R4: PARTIAL PASS.

---

# 1. OWNER RESULT

Owner подтвердил:

```text
VERSION_DISPLAY = PASS
```

Версия внутри Chrome extension теперь отображается правильно.

ЭТУ ЧАСТЬ СЧИТАТЬ ПРИНЯТОЙ.

Не переделывать version display без необходимости.

Но фото по-прежнему FAIL:

```text
одна и та же фотография видна в Техноребуте дважды:
- нормальная / хорошая версия;
- сверхмаленькая / размытая версия.
```

Owner говорит:

```text
ничего не изменилось по фотографиям;
low-res копия всё ещё присутствует.
```

---

# 2. КРИТИЧЕСКИ ВАЖНО: НЕ ДЕЛАТЬ ЕЩЁ ОДНУ ДЕДУПЛИКАЦИЮ НАУГАД

После R8-R8-R2, R3 и R4 уже было несколько попыток исправить variant dedupe.

Поэтому сейчас задача №1:

```text
ДОКАЗАТЬ, НА КАКОМ СЛОЕ ВОЗНИКАЕТ ВТОРАЯ ФОТОГРАФИЯ.
```

Есть минимум две разные гипотезы.

## H1 — extension всё ещё отправляет две версии

```text
real Avito photo
→ high URL + low URL
→ extension final payload contains both
→ backend честно сохраняет обе
```

## H2 — extension уже отправляет одну хорошую версию, но backend сохраняет старую low-res запись

```text
старые импорты уже создали:
high + low

новый extension payload:
high only

backend update semantics:
добавляет/обновляет high,
НО НЕ УДАЛЯЕТ obsolete low

UI поэтому всё ещё показывает:
high + old low
```

Эти причины требуют РАЗНЫХ исправлений.

Нельзя писать новый dedupe fix, пока H1/H2 не доказана.

---

# 3. ЦЕЛЬ R8-R8-R5

Получить доказанную цепочку для реального listing:

```text
Avito ID: 8313765236
Product ID: 58
```

Нужно сравнить:

```text
A. final extension payload
B. Avito module received payload
C. Core received photo set
D. DB rows after import
E. physical stored files
F. UI result
```

И ответить:

```text
ГДЕ ВПЕРВЫЕ count становится в 2 раза больше реального количества фотографий?
```

После этого исправить именно этот слой.

---

# 4. OWNER VERSION REQUIREMENT ALREADY ACCEPTED

Version display теперь работает.

Сохранить:

```text
popup version = chrome.runtime.getManifest().version
```

Не возвращать hardcoded version.

Если extension code будет изменён в этом этапе:

```text
bump 0.1.9 → 0.1.10
```

Если extension code НЕ меняется и root cause только backend:

```text
НЕ bump extension version без причины.
```

В отчёте явно указать:

```text
EXTENSION_CHANGED: true/false
EXTENSION_VERSION: ...
```

---

# 5. Сначала git/runtime audit

До изменений:

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

Не затереть unrelated changes.

---

# 6. Read-only audit Product 58 — ОБЯЗАТЕЛЬНО

До любых изменений Product 58:

```text
Product ID = 58
Avito ID = 8313765236
```

Получить ВСЕ `product_photos` rows.

Для каждой строки зафиксировать:

```text
photo_id
product_id
filename
media_url
source_url (если поле есть)
sort_order
created_at / updated_at if available
content_hash if available
file path/reference
physical file exists
file size
actual width
actual height
mime
```

Если каких-то колонок нет — написать `NOT_AVAILABLE`.

---

# 7. Классифицировать high/low пары в текущем Product 58

По фактическим файлам и source URLs определить:

```text
REAL_PHOTO_GROUP_1:
  high row
  low row

REAL_PHOTO_GROUP_2:
  high row
  low row
...
```

Для каждой пары показать доказательство, что это одна физическая фотография:

```text
same Avito media token/hash
или
pixel/image similarity if available safely
или
same canonical source identity
```

Не использовать OCR.

---

# 8. Временная безопасная диагностика final extension payload

Нужно доказать, что именно отправляет текущая установленная логика.

Предпочтительный способ:

- unit/runtime fixture using same real URL patterns;
- либо безопасный debug logging in extension;
- либо diagnostic function callable in tests.

Нужно получить до отправки:

```text
FINAL_PAYLOAD_PHOTO_COUNT
FINAL_PAYLOAD_URLS
FINAL_PAYLOAD_IDENTITIES
FINAL_PAYLOAD_QUALITY
```

Для реального listing, если агент не может открыть Owner Chrome page:

не притворяться, что real live payload известен.

В таком случае подготовить diagnostic data в extension, которое OWNER сможет увидеть/скопировать БЕЗ повторного изменения товара.

Но прежде использовать всё, что уже есть в logs/request traces.

---

# 9. Проверить Avito module received payload

На входе bridge/import endpoint зафиксировать:

```text
RECEIVED_PHOTO_COUNT
RECEIVED_URLS or safe URL identities
```

Если production logging URLs нежелателен:

логировать безопасно:

```text
index
canonical identity
quality/dimensions
```

Не логировать токены/cookies.

---

# 10. Проверить Core received set

Перед DB reconciliation:

```text
CORE_INPUT_PHOTO_COUNT
CORE_INPUT_IDENTITIES
```

После reconciliation:

```text
CORE_FINAL_AVITO_PHOTO_COUNT
CORE_FINAL_AVITO_IDENTITIES
```

---

# 11. Найти FIRST DUPLICATION LAYER

Отчёт обязан выбрать РОВНО один или несколько доказанных вариантов:

```text
DUPLICATION_FIRST_APPEARS_AT:
- extension_final_payload
- admin_shell_proxy
- avito_module_bridge
- core_input
- core_reconciliation
- stale_existing_db_rows
- ui_rendering
```

Не писать «скорее всего».

Нужны count/evidence.

---

# 12. Если H1: extension payload содержит high + low

Тогда исправить extension.

Требование:

```text
all source collectors
→ one combined candidate list
→ canonical identity
→ group
→ choose best
→ FINAL ARRAY
→ assert identities unique
```

Перед отправкой:

```text
len(final_images)
==
len(unique(canonical_identity(final_images)))
```

Если нет — это программная ошибка, low sibling не должен уходить.

---

# 13. Если H2: payload clean, но stale low rows остаются

Тогда основной fix — BACKEND PHOTO SET RECONCILIATION.

Текущий import должен быть не append-only.

Для фотографий, полученных из одного Avito listing:

```text
incoming clean Avito photo set
должен стать текущим Avito-managed photo set товара.
```

То есть:

```text
old Avito low
old Avito high
incoming high only

AFTER:
high only
```

---

# 14. Avito-managed subset — не удалять manual photos

КРИТИЧЕСКАЯ SAFETY.

Нельзя делать:

```text
DELETE all product_photos WHERE product_id=58
```

Нужно различать:

```text
Avito-managed photos
manual/local/other-source photos
```

Исследовать текущую модель.

Возможные признаки Avito-owned:

```text
source_url host img.avito.st
source type/origin column
external listing relation
import metadata
```

Использовать только ДОКАЗАННЫЙ признак.

---

# 15. Если provenance в модели недостаточно

Если невозможно надёжно отличить manual photo от Avito photo:

НЕ удалять существующие строки вслепую.

Тогда создать минимальную backward-compatible provenance модель, например:

```text
source_type = avito/manual/...
source_external_id = 8313765236
```

или существующий архитектурно подходящий эквивалент.

Но сначала проверить, возможно ли обойтись существующими полями.

Не усложнять модель без необходимости.

---

# 16. Atomic reconciliation

Reconciliation Avito photo set должна быть transaction-safe:

```text
1. validate/download incoming best variants
2. establish new clean set
3. DB transaction switches Avito-managed subset
4. obsolete Avito rows removed
5. obsolete Avito files cleaned safely
6. manual photos untouched
7. sort_order normalized
```

Если download новой фотографии не удался:

не уничтожать старый хороший набор до того, как новый набор валиден.

---

# 17. Existing Product 58 cleanup

OWNER хочет реальный результат без старых low-res дублей.

Если безопасная provenance/reconciliation доказана:

следующий OWNER re-import должен автоматически привести Product 58 к clean set:

```text
N real Avito photos
→ N Avito photo rows
```

Никаких старых low-res siblings.

Agent сам реальный import Product 58 НЕ выполняет.

Owner сделает это после отчёта.

---

# 18. Если old low rows не имеют provenance, но их identity доказана

Можно реализовать targeted reconciliation по:

```text
same external listing
+
same canonical Avito media identity
+
source_url evidence
```

Но только если это безопасно.

Нельзя удалять local/manual photos на основании размера файла.

---

# 19. Backend canonical identity

Даже если extension dedupe clean, Core желательно должен защищаться от:

```text
same Avito media identity
high URL + low URL
```

Результат:

```text
one Avito-managed photo
best quality wins
```

Это defense-in-depth.

Использовать canonical Avito identity based on proven URL token/hash.

---

# 20. Не использовать только file size как identity

Запрещено:

```text
small file = duplicate
large file = original
```

File size/dimensions помогают выбрать quality, но НЕ доказывают identity.

---

# 21. Sort order

После reconciliation:

```text
Avito gallery order preserved
0..N-1 contiguous
main photo first
```

Если manual photos coexist:

определить текущую принятую semantics и не ломать её.

---

# 22. Tests — stale low row scenario ОБЯЗАТЕЛЬНО

Создать regression test, отражающий реальный OWNER state:

Initial DB:

```text
photo A high
photo A low
photo B high
photo B low
```

Incoming clean payload:

```text
photo A high
photo B high
```

Expected DB:

```text
photo A high
photo B high
```

Low obsolete variants removed.

---

# 23. Tests — manual photo safety

Initial:

```text
manual photo M
Avito photo A high
Avito photo A low
```

Incoming:

```text
Avito photo A high
```

Expected:

```text
manual M remains
Avito A high remains
Avito A low removed
```

---

# 24. Tests — current clean import

Cover:

```text
0 Avito photos
1 real photo / multiple variants
N real photos / variants
repeat import
changed Avito gallery (photo removed)
changed Avito gallery (photo added)
```

Expected current Avito-managed set matches incoming canonical set.

---

# 25. Tests — extension final payload, only if extension changed

If H1 proven:

add exact real-pattern test:

```text
real low URL + real high URL
→ one final payload item
```

If H2 proven and extension payload already clean:

do NOT rewrite extension unnecessarily.

Add test proving current final payload is already clean.

---

# 26. Version behavior preserve

Version display already PASS.

Regression test must remain:

```text
popup reads chrome.runtime.getManifest().version
```

If extension bumped to 0.1.10:

```text
popup automatically shows 0.1.10
```

No hardcoded owner-visible version.

---

# 27. Full regression

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

# 28. Runtime verification

Проверить:

```text
docker compose ps
Core healthy
Avito module healthy
Inventory healthy
Admin Shell healthy
```

Если extension changed:

```text
download ZIP HTTP 200
manifest version correct
popup dynamic version contract intact
```

---

# 29. Не выполнять live owner import

Agent НЕ должен:

```text
реально импортировать listing 8313765236
мутировать Product 58
удалять photos Product 58 вручную
```

Read-only audit разрешён.

Фактическую cleanup/reconciliation Product 58 запускает Owner обычным повторным импортом после отчёта.

---

# 30. Documentation

Обновить:

```text
docs/stage06a_r8_extension_photo_import.md
```

и extension README только если extension реально менялся.

Создать:

```text
reports/stage06a_r8_r8_r5_duplicate_layer_and_photo_reconciliation_report.md
```

Обновить:

```text
logs/2026-08-13.md
```

Сохранить prompt:

```text
.agents/received_prompts/TECHNOREBOOT_STAGE06A_R8_R8_R5_DUPLICATE_LAYER_PHOTO_RECONCILIATION_PROMPT.md
```

---

# 31. Report structure

Обязательно:

```text
STATUS

OWNER_RESULT_R8_R8_R4

PRODUCT_58_PHOTO_ROWS_BEFORE
HIGH_LOW_PAIR_EVIDENCE

EXTENSION_FINAL_PAYLOAD_COUNT
EXTENSION_FINAL_IDENTITIES

AVITO_MODULE_RECEIVED_COUNT
CORE_INPUT_COUNT
DB_EXISTING_COUNT

DUPLICATION_FIRST_APPEARS_AT
H1_EXTENSION_DUPLICATES: true/false
H2_STALE_DB_DUPLICATES: true/false

ROOT_CAUSE

FIX_LAYER
EXTENSION_CHANGES
BACKEND_RECONCILIATION_CHANGES
PROVENANCE_METHOD
MANUAL_PHOTO_SAFETY
ATOMICITY
SORT_ORDER

STALE_LOW_CLEANUP_ON_NEXT_OWNER_IMPORT

VERSION_DISPLAY_REGRESSION
EXTENSION_CHANGED
EXTENSION_VERSION

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

# 32. Definition of Done

PASS только если:

```text
DUPLICATION_LAYER_PROVEN: true
NO_GUESSING_ABOUT_DUPLICATE_SOURCE: true

IF H1:
EXTENSION_FINAL_PAYLOAD_ONE_PER_IDENTITY: true

IF H2:
AVITO_PHOTO_SET_RECONCILIATION_IMPLEMENTED: true
OBSOLETE_LOW_AVITO_VARIANTS_REMOVED_ON_REIMPORT: true
MANUAL_PHOTOS_PRESERVED: true

ONE_REAL_AVITO_PHOTO_ONE_FINAL_DB_ROW: true
BEST_VARIANT_ONLY: true
PHOTO_ORDER_PRESERVED: true
REPEAT_IMPORT_IDEMPOTENT: true

VERSION_DISPLAY_STILL_DYNAMIC: true

OWNER_PRODUCT_58_MUTATED_BY_AGENT: false
OWNER_MANUAL_CHECK_REQUIRED: true
```

---

# 33. Git safety

Перед/после:

```powershell
git status --short --untracked-files=all
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

Commit message по фактической причине, например:

```text
Reconcile Avito photo set on reimport
```

или:

```text
Fix final Avito photo variant dedup
```

Push:

```powershell
git push origin main
```

---

# 34. OWNER CHECK GUIDE

После успешного отчёта ОСТАНОВИТЬСЯ.

Owner должен получить сценарий:

```text
1. Если extension менялся — скачать новую версию и проверить version label.
   Если extension НЕ менялся — оставить текущую установленную 0.1.9.

2. Открыть listing 8313765236.

3. Нажать импорт ОДИН РАЗ.

4. Открыть Product 58.

5. Проверить:
   - количество реальных фото на Avito = количеству Avito-фото в товаре;
   - каждая фотография ровно одна;
   - low-res/размытые siblings исчезли;
   - хорошие версии остались;
   - порядок нормальный;
   - Product ID остался 58.

6. Повторить импорт ещё один раз.
   Количество фотографий не должно измениться.
```

---

# 35. FINAL STATUS

При успехе:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE06A_R8_R8_R5_DUPLICATE_LAYER_FIXED_READY_FOR_OWNER_CHECK

DUPLICATION_LAYER_PROVEN: true
H1_EXTENSION_DUPLICATES: true/false
H2_STALE_DB_DUPLICATES: true/false
EXTENSION_FINAL_PAYLOAD_ONE_PER_IDENTITY: true
AVITO_PHOTO_SET_RECONCILIATION_IMPLEMENTED: true/false
OBSOLETE_LOW_AVITO_VARIANTS_REMOVED_ON_REIMPORT: true/false
MANUAL_PHOTOS_PRESERVED: true
ONE_REAL_AVITO_PHOTO_ONE_FINAL_DB_ROW: true
BEST_VARIANT_ONLY: true
REPEAT_IMPORT_IDEMPOTENT: true
VERSION_DISPLAY_STILL_DYNAMIC: true
OWNER_PRODUCT_58_MUTATED_BY_AGENT: false
OWNER_MANUAL_CHECK_REQUIRED: true
OWNER_ONE_ITEM_EXTENSION_IMPORT_NOT_YET_FULLY_ACCEPTED: true
FULL_ACCOUNT_IMPORT_NOT_YET_AUTHORIZED: true
DO_NOT_START_STAGE06A_R9_WITHOUT_OWNER_ACCEPTANCE: true
DO_NOT_START_STAGE06B_REVERSE_SYNC_WITHOUT_OWNER_ACCEPTANCE: true
```

Если слой возникновения дубля не доказан:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE06A_R8_R8_R5_DUPLICATE_LAYER_BLOCKED
```

с конкретными blockers.

После отчёта ОСТАНОВИТЬСЯ.
