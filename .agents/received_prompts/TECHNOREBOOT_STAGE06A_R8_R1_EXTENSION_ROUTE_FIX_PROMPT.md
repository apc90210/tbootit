# TECHNOREBOOT — Stage06A-R8-R1 Fix Missing /avito/extension Live Route

Репозиторий:

```powershell
C:\tbootit
```

Стартовая точка:

```text
Stage06A-R8
Commit: 1ed9775
```

Это corrective stage. Не начинать R9 и Stage06B.

## Реальный owner blocker

Владелец открыл:

```text
http://localhost:8011/avito/extension
```

и получил:

```json
{"detail":"Not Found"}
```

При этом Stage06A-R8 report утверждает, что route `/avito/extension` добавлен в Admin Shell.

Следовательно, R8 НЕ принят.

## Цель

Добиться, чтобы в реально запущенной системе:

```text
GET http://localhost:8011/avito/extension
```

возвращал:

```text
HTTP 200
HTML
«Расширение Chrome»
«Скачать расширение»
«Создать новый код подключения»
```

Без CLI со стороны владельца.

## Сначала воспроизвести на running Docker

До изменений зафиксировать:

```text
STATUS
BODY
ADMIN_SHELL_CONTAINER_ID
ADMIN_SHELL_IMAGE_ID
ADMIN_SHELL_START_TIME
CURRENT_GIT_HEAD
```

## Проверить route registration

Проверить `admin-shell/app/main.py` и фактический route:

```python
@app.get("/avito/extension", ...)
```

Проверить:
- route реально импортируется;
- нет условия, исключающего route;
- нет конфликтующего catch-all proxy;
- route не существует только в тестовой app.

## Проверить порядок route definitions

Особенно проверить generic route:

```text
/avito/{path:path}
```

Если generic proxy зарегистрирован так, что перехватывает `/avito/extension`, исправить порядок/архитектуру.

Контракт:

```text
/avito/extension
→ Admin Shell extension management page

/avito/...
→ proxy в avito-module только там, где это нужно
```

## Проверить live container code

Сравнить host:

```text
C:\tbootit\admin-shell\app\main.py
```

и running container:

```text
/app/app/main.py
```

Route `/avito/extension` должен реально присутствовать внутри контейнера.

Если нет — это build/volume/recreate issue.

## Проверить docker-compose mount

Убедиться, что Admin Shell использует актуальный код, например:

```text
./admin-shell/app:/app/app
```

или согласованный эквивалент.

Не допустить повторения запуска устаревшего image code.

## Rebuild/recreate

Агент сам выполняет необходимые rebuild/recreate сервисов. Owner не должен работать через CLI.

## Extension ZIP availability

Проверить:

```text
dist/technoreboot-avito-extension.zip
```

в live runtime.

Кнопка `Скачать расширение` должна реально отдавать ZIP:

```text
HTTP 200
attachment
size > 0
```

## Pairing endpoint live verification

Проверить через owner origin:

```text
POST /admin-api/avito-extension/pairing/generate
```

или фактический endpoint.

Ожидается 6-digit code + TTL.

## Runtime page verification

После final recreate:

```text
GET http://localhost:8011/avito/extension
```

Проверить:

```text
HTTP 200
contains «Расширение Chrome»
contains «Скачать расширение»
contains «Создать новый код подключения»
```

## Navigation link

На `/avito` должна быть явная ссылка:

```text
Расширение Chrome
```

ведущая на:

```text
/avito/extension
```

Проверить живой переход через `localhost:8011`.

## Tests

Добавить:

```text
admin-shell/tests/test_avito_extension_live_route.py
admin-shell/tests/test_avito_extension_not_shadowed_by_proxy.py
```

Первый тест:
```text
GET /avito/extension = 200
not 404
contains expected UI
```

Второй:
```text
/avito/extension
не попадает в /avito/{path:path} proxy handler
```

## Runtime Docker smoke

Не ограничиваться TestClient.

Проверить реально:

```text
http://localhost:8011/avito
http://localhost:8011/avito/extension
```

Оба должны возвращать 200.

## Не менять extension parser

R8-R1 не переписывает manifest/content.js/popup/pairing/parser/Core import, если это не нужно для route activation.

## Regression

Обязательно:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
docker compose exec -T inventory-sales-module pytest
docker compose exec -T avito-module pytest
docker compose exec -T repairs-module pytest
pytest admin-shell/tests
pytest chrome-extension/technoreboot-avito/tests
```

## Git

Expected HEAD:

```text
1ed9775
```

или фактический потомок.

Только targeted add.

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
```

Commit:

```powershell
git commit -m "Fix Avito extension admin route"
git push origin main
```

## Definition of Done

```text
GET /avito = 200;
GET /avito/extension = 200;
extension UI visible;
navigation link works;
route not shadowed by catch-all;
live container contains current code;
ZIP download works through 8011;
pairing generation works through 8011;
all regression suites PASS;
commit pushed;
git clean.
```

## Owner check

Owner делает только:

```text
1. Открыть http://localhost:8011/avito
2. Нажать «Расширение Chrome»
3. Убедиться, что страница открылась
4. Нажать «Скачать расширение»
5. Убедиться, что ZIP скачивается
```

После этого STOP.

## Final status

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE06A_R8_R1_EXTENSION_ROUTE_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
OWNER_EXTENSION_INSTALL_NOT_YET_ACCEPTED: true
OWNER_ONE_ITEM_EXTENSION_PROBE_NOT_YET_ACCEPTED: true
FULL_ACCOUNT_IMPORT_NOT_YET_AUTHORIZED: true
DO_NOT_START_STAGE06A_R9_WITHOUT_OWNER_ACCEPTANCE: true
DO_NOT_START_STAGE06B_REVERSE_SYNC_WITHOUT_OWNER_ACCEPTANCE: true
```
