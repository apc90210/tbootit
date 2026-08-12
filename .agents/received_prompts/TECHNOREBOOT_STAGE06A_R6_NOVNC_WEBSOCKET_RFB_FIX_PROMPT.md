# TECHNOREBOOT — Stage06A-R6 Fix noVNC WebSocket/RFB Connection

Репозиторий:
```powershell
C:\tbootit
```

Старт:
```text
Stage06A-R5
Commit: c748cf9
```

Это corrective stage. Stage06B НЕ начинать.

## Реальный owner blocker

Во встроенной авторизации Avito:

```text
noVNC UI загружается;
видна кнопка Connect;
после подключения:
Failed to connect to server
```

Следовательно:

```text
HTTP noVNC assets работают;
WebSocket/RFB transport НЕ работает.
```

R5 НЕ принят.

## Сначала воспроизвести

Зафиксировать:

```text
IFRAME_URL
NOVNC_PAGE_URL
NOVNC_WEBSOCKET_PATH
BROWSER_WEBSOCKET_URL
ADMIN_SHELL_WS_HANDLER
ADMIN_SHELL_WS_TARGET
WEBSOCKIFY_LISTEN
WEBSOCKIFY_TARGET
X11VNC_LISTEN
RFB_HANDSHAKE_RESULT
```

## WebSocket path

Browser-visible URL должен быть same-origin:

```text
ws://localhost:8011/avito/novnc/websockify
```

Он должен проксироваться:

```text
Admin Shell
→ ws://avito-module:6080/websockify
```

Запрещено browser-visible:

```text
ws://localhost:6080
ws://localhost:8061
ws://avito-module:6080
```

## Проверить iframe/noVNC config

Проверить `avito_browser.html`.

noVNC должен запускаться с корректным websocket path, например:

```text
/avito/novnc/vnc.html?autoconnect=1&resize=remote&path=avito/novnc/websockify
```

или корректным эквивалентом для установленной версии noVNC.

Не полагаться на default `websockify`, если proxy prefix отличается.

## Автоподключение

Owner не должен нажимать техническую кнопку `Connect`.

При открытии страницы:

```text
Подключение к браузеру Avito…
→ автоматический WebSocket connect
→ Chromium
```

## Admin Shell WebSocket proxy

Обязательный binary bridge:

```text
browser binary → upstream binary
upstream binary → browser binary
```

WebSocket handler должен:

```text
accept client;
connect upstream;
forward binary frames bidirectionally;
forward close/disconnect;
не превращать bytes в str;
не завершать bridge после первого frame.
```

## websockify/x11vnc proof

В `avito-module` доказать:

```text
5900 accepts TCP;
RFB banner received;
6080 accepts WebSocket;
websockify forwards RFB bytes from 5900.
```

Ожидаемый RFB banner вида:

```text
RFB 003.008
```

или совместимый.

## Admin Shell end-to-end proof

Подключиться через:

```text
ws://localhost:8011/avito/novnc/websockify
```

и доказать:

```text
WebSocket upgrade PASS;
RFB bytes получены через Admin Shell.
```

## Browser-level proof

Автоматизированно открыть owner page:

```text
http://localhost:8011/avito/accounts/<profile>/browser
```

Проверить:

```text
noVNC loads;
autoconnect starts;
нет Failed to connect to server;
canvas/framebuffer появился;
Chromium виден;
mouse/keyboard event проходит.
```

## Correct runtime ordering

```text
Xvfb ready
→ x11vnc ready
→ websockify ready
→ Chromium headed on DISPLAY=:99
→ embedded noVNC
→ autoconnect
→ framebuffer
```

## Health

`browser_runtime=ok` только если:

```text
Xvfb alive;
5900 gives RFB;
6080 websocket works;
Admin Shell websocket bridge works.
```

Не hardcode `ok`.

## Owner UI

Не показывать raw noVNC error как основной UX.

В shell:

```text
Не удалось подключиться к встроенному браузеру Avito.
[Повторить подключение]
```

## Tests

Добавить/обновить:

```text
avito-module/tests/test_x11vnc_rfb_banner.py
avito-module/tests/test_websockify_rfb_bridge.py
avito-module/tests/test_novnc_autoconnect_config.py

admin-shell/tests/test_novnc_ws_binary_bridge.py
admin-shell/tests/test_novnc_ws_rfb_banner_through_proxy.py
admin-shell/tests/test_embedded_novnc_autoconnect.py
admin-shell/tests/test_embedded_browser_framebuffer.py
admin-shell/tests/test_embedded_browser_no_failed_connection.py
```

## Mandatory runtime integration test

После final rebuild:

```text
Xvfb READY
x11vnc TCP 5900 READY
RFB banner READY
websockify websocket READY
RFB via websockify READY
Admin Shell websocket READY
RFB via Admin Shell READY
noVNC autoconnect READY
framebuffer READY
Chromium visible READY
```

После `force-recreate` повторить эти проверки без ручных post-start команд.

## Ограничения

Сохранить:

```text
manual login required;
same persistent browser profile;
no parsing before authorized;
one interactive profile;
no stealth;
no fingerprint spoof;
no CAPTCHA bypass;
no proxy rotation.
```

## Regression

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
docker compose exec -T inventory-sales-module pytest
docker compose exec -T avito-module pytest
docker compose exec -T repairs-module pytest
pytest admin-shell/tests
```

## Документация

Создать:

```text
docs/stage06a_r6_novnc_websocket_rfb_fix.md
reports/stage06a_r6_novnc_websocket_rfb_fix_report.md
```

Обновить:

```text
README.md
logs/2026-08-12.md
```

## Git

Expected HEAD:

```text
c748cf9
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
git commit -m "Fix noVNC WebSocket connection"
git push origin main
```

## Definition of Done

```text
noVNC page loads;
autoconnect works;
same-origin websocket path;
binary websocket bridge works;
websockify reaches x11vnc;
RFB banner verified;
RFB works through Admin Shell;
framebuffer visible;
Chromium visible;
mouse works;
keyboard works;
no Failed to connect to server;
recreate recovers automatically;
profile persists;
all suites PASS;
push complete;
git clean.
```

## Owner check after R6

Owner делает только:

```text
1. http://localhost:8011
2. Авито
3. Авторизоваться в Avito
4. Ничего не нажимать в noVNC
5. Дождаться autoconnect
6. Увидеть Chromium
7. Увидеть Avito
8. Проверить мышь
9. Проверить клавиатуру
```

После этого STOP.

## Final status

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE06A_R6_NOVNC_RFB_READY_FOR_OWNER_CHECK

OWNER_MANUAL_BROWSER_CHECK_REQUIRED: true
OWNER_AVITO_LOGIN_NOT_YET_ACCEPTED: true
OWNER_ONE_ITEM_PROBE_NOT_YET_ACCEPTED: true
FULL_ACCOUNT_IMPORT_NOT_YET_AUTHORIZED: true
DO_NOT_START_STAGE06B_REVERSE_SYNC_WITHOUT_OWNER_ACCEPTANCE: true
```
