# TECHNOREBOOT — Stage06A-R5 Embedded Avito Browser Runtime / noVNC Proxy Fix

Репозиторий:
```powershell
C:\tbootit
```

Старт:
```text
Stage06A-R4
Commit: 6e85ce1
```

Это corrective stage. Stage06B НЕ начинать.

## Реальный blocker владельца

При:
```text
http://localhost:8011
→ Авито
→ Авторизоваться
```

получено:
```json
{"detail":"noVNC proxy error: All connection attempts failed"}
```

Это означает: owner routing уже дошёл до нужной страницы, но Admin Shell не может подключиться к noVNC runtime.

## Главный контракт

Owner НЕ должен запускать вручную:
```text
noVNC
Xvfb
x11vnc
Chromium
docker exec
playwright install
```

После обычного старта Technoreboot встроенный браузер должен быть готов автоматически.

## Сначала воспроизвести и найти точную причину

Зафиксировать:
```text
OWNER_URL
ADMIN_SHELL_PROXY_TARGET
TARGET_HOST
TARGET_PORT
TARGET_SOCKET_STATE
XVFB_STATE
X11VNC_STATE
WEBSOCKIFY_STATE
CHROMIUM_STATE
```

Проверить реальные причины, а не предполагать:
```text
- noVNC не запущен;
- websockify слушает не тот интерфейс;
- Admin Shell ходит на localhost вместо avito-module;
- неверный port/path;
- entrypoint запускает процессы неправильно;
- один процесс падает;
- health объявляет ready слишком рано.
```

## Предпочтительная runtime-архитектура

Внутри `avito-module`:

```text
FastAPI     :8020
Xvfb        DISPLAY=:99
x11vnc      :5900
websockify  :6080
Chromium    headed, DISPLAY=:99
```

Admin Shell должен ходить через Docker network:

```text
http://avito-module:6080
ws://avito-module:6080/websockify
```

Критически:
```text
localhost внутри admin-shell = admin-shell container,
а НЕ avito-module.
```

## Internal bind

noVNC/websockify внутри контейнера должен слушать:
```text
0.0.0.0:6080
```

Но наружу host port публиковать не нужно.

Owner ходит только через:
```text
http://localhost:8011
```

## Entrypoint

Автоматически стартуют:
```text
Xvfb
x11vnc
websockify/noVNC
uvicorn
```

Не просто запускать всё через `&` без контроля. Сделать минимальный supervision/startup check.

## Browser launch

При нажатии «Авторизоваться в Avito»:

```text
1. выбрать account profile;
2. persistent user-data-dir;
3. запустить headed Chromium на DISPLAY=:99;
4. открыть https://www.avito.ru/;
5. показать окно через noVNC;
6. повторное нажатие reuse existing session.
```

## Health

`/health/details` должен реально проверять:

```json
{
  "module": "ok",
  "browser_runtime": "ok",
  "xvfb": "ok",
  "vnc": "ok",
  "novnc": "ok",
  "chromium": "ok",
  "profile_storage": "ok"
}
```

Не hardcode `ok`.

На `/avito`:
```text
Браузер Avito: Готов
```
только если runtime действительно ready.

Если не ready:
```text
Браузер Avito: Не готов
```
и кнопка авторизации disabled.

Owner не должен видеть raw JSON proxy error.

## noVNC proxy

Проверить:
```text
/vnc.html
/app/
/core/
/vendor/
```

Все assets должны проходить через same-origin proxy.

WebSocket:
```text
browser
→ localhost:8011/avito/novnc/websockify
→ admin-shell
→ avito-module:6080/websockify
```

Обязателен успешный upgrade/connection.

## Runtime integration test

После final build/recreate доказать:

```text
avito-module running
Xvfb running
x11vnc running
websockify running
6080 listening
admin-shell can connect to avito-module:6080
proxied vnc.html = 200
assets = 200
WebSocket proxy = PASS
headed Chromium launch = PASS
framebuffer visible = PASS
```

После recreate всё снова должно подняться автоматически.

## Persistent profile

Профиль переживает recreate и тот же путь используется после перезапуска.

## Ограничения

Сохранить:
```text
manual login required;
same persistent browser profile;
no parsing before authorized;
one interactive profile at a time;
no stealth;
no fingerprint spoof;
no CAPTCHA bypass;
no proxy rotation.
```

## Tests

Добавить/обновить:
```text
avito-module/tests/test_runtime_processes.py
avito-module/tests/test_novnc_internal_bind.py
avito-module/tests/test_browser_runtime_health.py
avito-module/tests/test_interactive_chromium_display.py
avito-module/tests/test_browser_launch_idempotency.py

admin-shell/tests/test_novnc_proxy_runtime_target.py
admin-shell/tests/test_novnc_assets_proxy.py
admin-shell/tests/test_novnc_websocket_proxy.py
admin-shell/tests/test_avito_browser_ready_gate.py
admin-shell/tests/test_avito_browser_error_ui.py
```

## Regression

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
docker compose exec -T inventory-sales-module pytest
docker compose exec -T avito-module pytest
docker compose exec -T repairs-module pytest
pytest admin-shell/tests
```

## Safety

Проверить:
```text
public noVNC host port = 0
direct DB from avito-module = 0
tracked browser sessions = 0
stored credentials = 0
anti-bot evasion code = 0
```

## Документация

Создать:
```text
docs/stage06a_r5_embedded_avito_browser_runtime_fix.md
reports/stage06a_r5_embedded_avito_browser_runtime_fix_report.md
```

Обновить:
```text
README.md
logs/2026-08-11.md
```

## Git

Expected starting HEAD:
```text
6e85ce1
```

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
git commit -m "Fix embedded Avito browser runtime"
git push origin main
```

## Definition of Done

```text
owner works only via localhost:8011;
browser health really ready;
Xvfb auto-start;
x11vnc auto-start;
websockify auto-start;
Chromium present in image;
headed Chromium launches;
Admin Shell uses Docker hostname avito-module;
noVNC assets proxy works;
WebSocket proxy works;
framebuffer visible;
owner sees embedded Chromium;
no raw JSON proxy error;
recreate recovers automatically;
profile persists;
manual login remains required;
all test suites PASS;
push done;
git clean.
```

## Owner check after R5

Owner делает только:
```text
1. Открыть http://localhost:8011
2. Авито
3. Увидеть «Браузер Avito: Готов»
4. Нажать «Авторизоваться в Avito»
5. Увидеть встроенный Chromium
6. Убедиться, что открывается Avito
```

После этого STOP.

Не выполнять ещё login/import до owner confirmation, что встроенный browser работает.

## Final status

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE06A_R5_EMBEDDED_AVITO_BROWSER_READY_FOR_OWNER_CHECK

OWNER_MANUAL_BROWSER_CHECK_REQUIRED: true
OWNER_AVITO_LOGIN_NOT_YET_ACCEPTED: true
OWNER_ONE_ITEM_PROBE_NOT_YET_ACCEPTED: true
FULL_ACCOUNT_IMPORT_NOT_YET_AUTHORIZED: true
DO_NOT_START_STAGE06B_REVERSE_SYNC_WITHOUT_OWNER_ACCEPTANCE: true
```
