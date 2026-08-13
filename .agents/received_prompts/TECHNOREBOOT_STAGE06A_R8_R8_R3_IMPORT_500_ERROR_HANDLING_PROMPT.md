# TECHNOREBOOT — Stage06A-R8-R8-R3 Import 500 Root Cause + Robust Extension Error Handling

Репозиторий:

```powershell
C:\tbootit
```

Это corrective-stage внутри Stage06A-R8-R8.

НЕ начинать:
- Stage06A-R9
- Stage06B
- любой следующий функциональный этап

Предыдущий этап:

```text
TECHNOREBOOT_STAGE06A_R8_R8_R2_BEST_QUALITY_ONLY_READY_FOR_OWNER_CHECK
```

OWNER CHECK R8-R8-R2: FAILED WITH SERVER ERROR.

---

# 1. Реальный OWNER результат

Owner использовал extension 0.1.7 и объявление:

```text
Avito ID: 8313765236
Title: Лазерный цветной принтер hp m252n на запчасти
Price: 6900 ₽
```

Extension status:

```text
✓ Сервер доступен. Расширение привязано к Техноребут.
```

При нажатии:

```text
Передать объявление в Техноребут
```

получен результат:

```text
✕ Объявление получено, но импорт товара завершился ошибкой.
Ошибка при передаче: Unexpected token 'I', "Internal S"... is not valid JSON
```

Это означает:

```text
server returned non-JSON response
likely "Internal Server Error"
HTTP status likely 500
popup/content bridge tried JSON.parse / response.json()
```

---

# 2. ЦЕЛЬ R8-R8-R3

Нужно решить ДВЕ отдельные проблемы:

## A. Найти и исправить реальный backend 500

Проследить полный import path:

```text
Chrome extension
→ Admin Shell / Avito module endpoint
→ Avito bridge
→ Core API
→ product update
→ photo reconciliation
→ DB/storage
```

Найти конкретный exception/traceback.

НЕ маскировать 500.

---

## B. Исправить error handling расширения

Даже если сервер когда-либо снова вернёт:

```text
500 Internal Server Error
502 Bad Gateway
plain text
HTML error page
empty body
invalid JSON
```

расширение НЕ должно показывать:

```text
Unexpected token 'I'
```

Оно должно показывать нормальную диагностическую ошибку, например:

```text
Ошибка сервера 500: Internal Server Error
```

или существующий русский эквивалент.

---

# 3. Сначала runtime logs — БЕЗ изменений

Перед кодом:

```powershell
Set-Location C:\tbootit

git status --short --untracked-files=all
git branch --show-current
git rev-parse HEAD
git log --oneline -10
docker compose ps
```

Затем получить логи relevant services:

```powershell
docker compose logs --tail=300 avito-module
docker compose logs --tail=300 core
docker compose logs --tail=300 admin-shell
```

Если service names отличаются — определить реальные names через:

```powershell
docker compose ps
```

Найти traceback около последней OWNER попытки импорта.

---

# 4. Обязательно установить точный HTTP endpoint

Определить:

```text
EXTENSION_REQUEST_URL
HTTP_METHOD
REQUEST_BODY
RESPONSE_STATUS
RESPONSE_CONTENT_TYPE
RESPONSE_BODY
```

Нужно точно знать, кто вернул `Internal Server Error`:

```text
Admin Shell
Avito module
Core
reverse proxy
```

---

# 5. Не воспроизводить через live Owner data без необходимости

Сначала использовать:

```text
existing logs
isolated test payload
test DB / safe fixtures
```

Не выполнять повторный импорт Product 58 автоматически, если root cause можно воспроизвести fixture-тестом.

Owner listing:

```text
8313765236
Product 58
```

не мутировать без необходимости.

---

# 6. Особое внимание: R8-R8-R2 reconciliation

Проверить код, добавленный/изменённый для:

```text
best-quality-only
photo deduplication
photo reconciliation
obsolete inferior variants
sort_order compaction
```

Наиболее вероятные классы проблем:

```text
unique constraint violation
null/None handling
duplicate key
list mutation
missing DB column
unexpected photo provenance
invalid source_url
filesystem delete/update failure
transaction rollback
stale object
wrong response schema
```

Не предполагать — подтвердить traceback.

---

# 7. Backend root cause report

Отчёт должен содержать:

```text
EXCEPTION_TYPE
EXCEPTION_MESSAGE
FILE
FUNCTION
LINE
INPUT_CONDITION
WHY_OWNER_FLOW_TRIGGERED_IT
```

Если root cause связан с существующими low/high дублями Product 58, это нужно явно указать.

---

# 8. Исправление backend

Исправление должно:

```text
preserve Product 58
preserve all good photos
not create duplicate product
not delete manual/non-Avito photos
not corrupt sort_order
remain idempotent
```

После fix:

```text
same listing import
→ HTTP 2xx / expected JSON
→ same Product ID
→ all real photos
→ one best variant per photo
```

---

# 9. Transaction safety

Если photo reconciliation выполняет:

```text
delete old
insert new
reorder
```

это должно быть transaction-safe.

При ошибке:

```text
не оставлять half-updated photo set
```

Проверить rollback behavior.

---

# 10. Extension robust response parsing

Найти все места в extension:

```text
response.json()
JSON.parse(...)
```

в import flow.

Заменить на безопасную схему:

```text
read status
read content-type
read raw text/body
if JSON → parse
else → preserve body as server error
```

Логика:

```text
2xx + valid JSON → normal success handling

non-2xx + valid JSON → show backend message

non-2xx + plain text → show:
"Ошибка сервера <status>: <text>"

2xx + invalid JSON → show:
"Некорректный ответ сервера"

network exception → existing network error
```

---

# 11. Не скрывать полезный backend detail

Если backend возвращает safe user-facing JSON:

```json
{"detail":"..."}
```

расширение должно показывать `detail`.

Но НЕ выводить:

```text
traceback
filesystem path
SQL
token
secret
cookie
internal stack
```

в popup.

Traceback остаётся только в server logs.

---

# 12. Avito/Admin/Core API error contract

Проверить endpoint, через который extension передаёт карточку.

Предпочтительно backend должен возвращать ошибки как JSON:

```json
{
  "ok": false,
  "error": "...",
  "detail": "..."
}
```

с правильным HTTP status.

Если сейчас unhandled exception превращается в plain `Internal Server Error`, устранить конкретный exception.

Не нужно глобально перехватывать вообще все exceptions и возвращать HTTP 200.

---

# 13. HTTP status semantics

Не делать:

```text
HTTP 200 + {"error": "..."}
```

для настоящего server failure, если текущая архитектура уже использует status codes.

Сохранить корректные:

```text
4xx client/input
5xx unexpected server
2xx success
```

---

# 14. Tests — backend regression

Добавить точный regression test на найденный OWNER exception.

Обязательно:

```text
test_owner_r8_r8_r2_payload_no_longer_500s
```

или эквивалент с понятным naming.

Также:

```text
multi-photo best-only import succeeds
same Product external ID updates same product
repeat import idempotent
existing low/high duplicate state does not crash reconciliation
sort_order valid
```

---

# 15. Tests — extension error handling

Добавить минимум:

```text
500 plain text Internal Server Error
500 JSON detail
502 HTML/plain response
200 invalid JSON
200 valid success JSON
network failure
```

Ожидаемо:

```text
never "Unexpected token"
never raw JSON.parse syntax error to Owner
```

---

# 16. Product 58 current-state audit

Read-only до Owner re-test:

```text
product id
external listing id
photo row count
photo source URLs
sort_order
file existence
```

Не выполнять destructive cleanup.

Если backend fix требует safe reconciliation при следующем Owner import — оставить это на Owner action.

---

# 17. Extension version

Так как меняется extension error handling:

```text
0.1.7 → 0.1.8
```

Обновить:

```text
manifest.json
popup.js/version UI
README
Admin Shell extension page
download handler
build_extension_zip.py
dist ZIP
admin-shell ZIP
tests
```

---

# 18. Owner download

Проверить:

```text
http://localhost:8011/avito/extension
```

показывает:

```text
0.1.8
```

и:

```text
http://localhost:8011/avito/extension/download
```

возвращает:

```text
HTTP 200
manifest version 0.1.8
```

---

# 19. Full regression

Запустить:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
docker compose exec -T inventory-sales-module pytest
docker compose exec -T avito-module pytest
docker compose exec -T repairs-module pytest
pytest admin-shell/tests
pytest chrome-extension/technoreboot-avito/tests
```

Указать ФАКТИЧЕСКИЕ counts.

---

# 20. Runtime proof

После fix:

```powershell
docker compose ps
```

Проверить:

```text
Core healthy
Avito module healthy
Inventory healthy
Admin Shell healthy
extension ZIP 0.1.8 HTTP 200
```

Также выполнить isolated HTTP request к import endpoint с fixture payload, максимально близким к Owner case.

Зафиксировать:

```text
HTTP_STATUS
CONTENT_TYPE
JSON_VALID
PRODUCT_UPDATE_RESULT
PHOTO_RESULT
```

Не использовать live Product 58, если можно fixture.

---

# 21. Safety

Запрещено:

```text
DROP TABLE
drop_all
mass DELETE
delete Product 58
create duplicate Product 58
git add .
git add -A
git add -u
git reset
git clean
git rebase
git commit --amend
force push
```

Targeted add only.

---

# 22. Documentation

Обновить:

```text
docs/stage06a_r8_extension_photo_import.md
chrome-extension/technoreboot-avito/README.md
```

Создать:

```text
reports/stage06a_r8_r8_r3_import_500_error_handling_report.md
```

Обновить:

```text
logs/2026-08-13.md
```

Сохранить prompt:

```text
.agents/received_prompts/TECHNOREBOOT_STAGE06A_R8_R8_R3_IMPORT_500_ERROR_HANDLING_PROMPT.md
```

---

# 23. Report structure

Обязательно:

```text
STATUS

OWNER_ERROR

HTTP_ENDPOINT
HTTP_STATUS
RESPONSE_CONTENT_TYPE
RESPONSE_BODY_TYPE

SERVER_TRACEBACK
ROOT_CAUSE

R8_R8_R2_RECONCILIATION_RELATION

BACKEND_FIX
TRANSACTION_SAFETY
IDEMPOTENCY

EXTENSION_ERROR_HANDLING_FIX
PLAIN_TEXT_500_BEHAVIOR
JSON_ERROR_BEHAVIOR
INVALID_JSON_BEHAVIOR

PRODUCT_58_READ_ONLY_STATE

EXTENSION_VERSION
ZIP_FILENAME
OWNER_DOWNLOAD_URL

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

# 24. Definition of Done

PASS только если:

```text
OWNER_500_ROOT_CAUSE_IDENTIFIED: true
OWNER_500_FIXED: true
IMPORT_ENDPOINT_RETURNS_VALID_JSON_ON_SUCCESS: true
PLAIN_TEXT_ERROR_NO_LONGER_CAUSES_JSON_PARSE_EXCEPTION: true
EXTENSION_SHOWS_HUMAN_READABLE_SERVER_ERROR: true
BEST_QUALITY_ONLY_MULTI_PHOTO_PRESERVED: true
REPEAT_IMPORT_IDEMPOTENT: true
PRODUCT_58_NOT_MUTATED_BY_AGENT: true
EXTENSION_VERSION_0_1_8_READY: true
OWNER_MANUAL_CHECK_REQUIRED: true
```

---

# 25. Git

Commit message:

```text
Fix Avito import 500 and response parsing
```

или точнее по фактическому root cause.

После:

```powershell
git push origin main
git status --short --untracked-files=all
git rev-parse HEAD
git log --oneline -5
```

---

# 26. OWNER CHECK GUIDE

После отчёта остановиться.

Owner сценарий:

```text
1. Скачать extension 0.1.8.
2. Обновить extension в Chrome.
3. Открыть Avito listing 8313765236.
4. Нажать «Передать объявление в Техноребут» ОДИН РАЗ.
5. Проверить:
   - нет Unexpected token;
   - import success;
   - Product ID = 58;
   - все реальные фото импортированы;
   - low-res дублей нет;
   - только лучшие варианты;
   - порядок нормальный.
6. Открыть Product 58.
7. Сообщить Owner result.
```

---

# 27. FINAL STATUS

При успехе:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE06A_R8_R8_R3_IMPORT_500_FIXED_READY_FOR_OWNER_CHECK

OWNER_500_ROOT_CAUSE_IDENTIFIED: true
OWNER_500_FIXED: true
IMPORT_ENDPOINT_SUCCESS_JSON_VALID: true
EXTENSION_PLAIN_TEXT_ERROR_HANDLING_FIXED: true
UNEXPECTED_TOKEN_ERROR_ELIMINATED: true
BEST_QUALITY_ONLY_MULTI_PHOTO_PRESERVED: true
REPEAT_IMPORT_IDEMPOTENT: true
PRODUCT_58_MUTATED_BY_AGENT: false
EXTENSION_VERSION_0_1_8_READY: true
OWNER_MANUAL_CHECK_REQUIRED: true
OWNER_ONE_ITEM_EXTENSION_IMPORT_NOT_YET_FULLY_ACCEPTED: true
FULL_ACCOUNT_IMPORT_NOT_YET_AUTHORIZED: true
DO_NOT_START_STAGE06A_R9_WITHOUT_OWNER_ACCEPTANCE: true
DO_NOT_START_STAGE06B_REVERSE_SYNC_WITHOUT_OWNER_ACCEPTANCE: true
```

Если 500 root cause не найден:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE06A_R8_R8_R3_IMPORT_500_BLOCKED
```

с конкретным blockers.

После отчёта ОСТАНОВИТЬСЯ.
