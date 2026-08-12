# TECHNOREBOOT — Stage06A-R7 Manual Browser Login + Profile Registry Repair + Avito Access Diagnostics

Репозиторий:

```powershell
C:\tbootit
```

Стартовая точка:

```text
Stage06A-R6
Commit: 44c9807
```

Это corrective stage. Stage06B НЕ начинать.

## 1. Реальные замечания владельца

После R6:

```text
noVNC / embedded browser открылся;
Avito открылся;
при работе появился:
Profile not found

при ручном вводе корректного логина/пароля Avito в итоге показывает:
«Доступ закрыт».
```

Нужно разделить две независимые проблемы:

```text
A. TECHNOREBOOT PROFILE NOT FOUND
B. AVITO ACCESS DENIED DURING MANUAL LOGIN
```

Не смешивать их.

---

## 2. Profile not found — BLOCKER

Найти точный источник сообщения:

```text
Profile not found
```

Определить:

```text
кто его возвращает;
какой account_key/profile_id передаётся;
существует ли он в profile registry;
существует ли profile directory;
пережил ли registry container recreate;
пережил ли browser_data recreate;
не осталась ли stale ссылка в UI.
```

Report:

```text
PROFILE_NOT_FOUND_SOURCE
REQUESTED_PROFILE_KEY
REGISTRY_KEYS
PROFILE_DIRECTORY
ROOT_CAUSE
```

---

## 3. Profile registry — единый source of truth

Для каждого Avito account:

```text
account_key
display_name
browser_profile_path
auth_state
probe_verified
```

должны храниться persistent.

Registry НЕ должен исчезать при:

```text
container restart;
container recreate;
Docker restart;
Windows restart.
```

Profile metadata и browser_data должны иметь согласованную persistence model.

---

## 4. Никаких stale browser links

Owner-facing URL:

```text
/avito/accounts/{account_key}/browser
```

должен работать только для реально существующего account_key.

Если профиль удалён/потерян:

не показывать raw:

```text
Profile not found
```

Показывать:

```text
«Профиль Avito не найден. Вернитесь к списку аккаунтов.»
```

и кнопку:

```text
К аккаунтам Avito
```

---

## 5. Repair/migration existing registry

Не удалять автоматически owner browser profile.

Добавить safe reconciliation:

```text
registry entry exists + directory exists -> OK
registry entry exists + directory missing -> controlled broken profile
directory exists + registry entry missing -> do NOT delete;
                                      mark recoverable;
                                      offer safe recovery/migration
```

Не терять cookies/local storage существующего owner profile.

---

# ЧАСТЬ B — MANUAL LOGIN ENVIRONMENT

## 6. Главный architectural change

На этапе РУЧНОЙ авторизации Avito НЕ использовать Playwright-controlled browser.

То есть owner manual login flow:

```text
Technoreboot UI
→ launch ordinary GUI Chrome/Chromium OS process
→ DISPLAY=:99
→ persistent --user-data-dir
→ noVNC
→ owner manually logs in
```

Во время ручной авторизации:

```text
NO Playwright BrowserContext
NO CDP attach
NO remote-debugging-port
NO WebDriver
NO automation scripts
```

Это именно обычный браузер, которым управляет пользователь мышью/клавиатурой через noVNC.

---

## 7. Browser choice

Сначала аудировать текущий browser binary.

Зафиксировать:

```text
CURRENT_BROWSER_BINARY
CURRENT_BROWSER_VERSION
CURRENT_LAUNCH_METHOD
CURRENT_FLAGS
PLAYWRIGHT_CONTROLLED: true/false
```

Для manual login предпочесть обычный установленный stable browser:

```text
Google Chrome stable
или стандартный Chromium package
```

запущенный напрямую как process.

Не использовать Playwright bundled browser для manual-login mode, если именно Playwright его запускает/контролирует.

---

## 8. Никаких anti-bot workarounds

НЕ добавлять:

```text
stealth plugin
navigator.webdriver spoof
fingerprint spoofing
canvas spoofing
user-agent spoof ради обхода
proxy rotation
residential proxy tricks
CAPTCHA solver
SMS bypass
anti-detect browser
automation flag masking
```

Цель R7:

```text
сделать ручной логин действительно ручным,
а не замаскировать автоматизацию.
```

---

## 9. Manual browser process

Добавить отдельный runtime mode:

```text
MANUAL_BROWSER
```

Process example conceptually:

```text
chrome
--user-data-dir=/app/data/profiles/<account_key>/browser_data
--no-first-run
--start-maximized
https://www.avito.ru/
```

Использовать только технически необходимые container flags.

Не добавлять automation-specific flags без необходимости.

---

## 10. One browser profile

Manual login и дальнейшая работа должны использовать ОДИН persistent profile path.

Но нельзя одновременно держать:

```text
manual Chrome
и Playwright Chrome
```

на одном `user-data-dir`.

Добавить lifecycle lock:

```text
manual browser active
→ automated browser launch forbidden
```

---

## 11. Manual login state

UI:

```text
Авито
→ Аккаунт
→ Авторизоваться вручную
```

После запуска:

```text
Ручной браузер открыт
```

Owner входит самостоятельно.

Кнопки:

```text
Я вошёл — закрыть браузер и проверить
Закрыть без проверки
```

---

## 12. Graceful browser shutdown

После:

```text
Я вошёл — закрыть браузер и проверить
```

обычный Chrome должен завершаться корректно:

```text
graceful terminate;
wait profile flush;
не kill -9;
не удалять cookies;
не удалять Preferences;
не очищать Local Storage.
```

Только stale `Singleton*` после подтверждённого аварийного процесса можно чистить безопасно.

---

## 13. Сохранность cookies/local storage

Добавить persistence proof без вывода cookie values.

До/после restart проверить только metadata:

```text
cookie database exists;
profile Preferences exists;
local storage directory exists;
mtime/size persisted.
```

НЕ выводить secret cookie content в logs/report/API.

---

## 14. Контрольный owner test вне системы

В owner guide добавить диагностический контроль:

```text
A. Обычный Chrome/Yandex/Edge на том же ПК и той же сети.
B. Войти в тот же Avito account вручную.
```

Результаты трактовать:

```text
Обычный desktop browser тоже получает «Доступ закрыт»
→ проблема не доказана как Technoreboot browser problem;
  возможна account/session/network security restriction;
  STOP и owner решает вопрос обычным путём/поддержкой.

Обычный desktop browser входит нормально,
embedded MANUAL_BROWSER получает «Доступ закрыт»
→ проблема конкретно в embedded browser environment;
  продолжить technical comparison.
```

Не пытаться обходить блокировку.

---

## 15. Embedded environment comparison

Если ordinary desktop browser works but embedded manual browser fails, собрать НЕсекретную диагностику:

```text
browser name/version
OS platform
timezone
locale
screen size
cookie enabled
local storage enabled
JavaScript enabled
date/time
TLS certificate errors
network egress IP comparison (only owner-readable status, not bypass)
```

Не собирать fingerprint для spoofing.

Цель — понять несовместимость.

---

## 16. Cookie settings

Убедиться, что browser НЕ запускается с:

```text
--disable-cookies
incognito
temporary profile
ephemeral user-data-dir
clear-on-exit
```

Cookies и local storage должны работать стандартно.

---

## 17. Browser profile permissions

Проверить:

```text
browser_data writable by browser user;
Cookie DB writable;
Local Storage writable;
Preferences writable.
```

После входа browser должен иметь возможность записать session state.

---

## 18. Container clock / timezone

Проверить системно:

```text
container time correct;
timezone sane;
certificates valid.
```

Не менять время для маскировки.

---

## 19. Access denied classification

В UI добавить controlled operational state:

```text
AVITO_ACCESS_DENIED
```

Owner message:

```text
«Avito закрыл доступ в этом браузере. Автоматический обход блокировки не выполняется.»
```

Действия:

```text
Повторить обычный ручной вход
Проверить вход в обычном браузере
Открыть справочную информацию
```

---

# ЧАСТЬ C — AFTER MANUAL AUTH

## 20. Только после успешного ручного логина

Когда owner подтверждает:

```text
обычный embedded browser вошёл;
личный кабинет доступен;
```

только тогда разрешается следующий test:

```text
AUTOMATED_SESSION_COMPATIBILITY_CHECK
```

---

## 21. Automated compatibility check

После graceful закрытия manual browser:

```text
launch current supported automation using same persistent profile;
open own account page;
perform READ-ONLY check only;
no changes;
no import yet.
```

Если access remains valid:

```text
AUTOMATION_COMPATIBLE
```

Если Avito immediately returns access denied/challenge:

```text
AUTOMATION_NOT_COMPATIBLE
```

STOP.

Не применять evasion.

---

## 22. If automation is not compatible

Не пытаться скрыть Playwright.

Report owner decision options:

```text
A. Official Avito API where available
B. Manual browser workflow
C. Another documented/allowed integration mechanism
```

Do not start Stage06B automatically.

---

## 23. Browser automation behaviour if compatible

Сохранить ограничения:

```text
only owner's own account;
only own listings;
low concurrency;
sequential navigation;
no stealth;
no proxy rotation;
challenge -> USER_ACTION_REQUIRED.
```

---

## 24. Tests — profile registry

Добавить:

```text
avito-module/tests/test_profile_registry_persistence.py
avito-module/tests/test_profile_directory_registry_consistency.py
avito-module/tests/test_missing_profile_owner_ui.py
avito-module/tests/test_stale_profile_recovery.py
```

---

## 25. Tests — manual browser

Добавить:

```text
avito-module/tests/test_manual_browser_not_playwright_controlled.py
avito-module/tests/test_manual_browser_persistent_user_data_dir.py
avito-module/tests/test_manual_browser_profile_write_permissions.py
avito-module/tests/test_manual_browser_graceful_shutdown.py
avito-module/tests/test_manual_browser_single_profile_lock.py
```

---

## 26. Tests — storage persistence

Добавить safe tests:

```text
profile directory survives recreate;
cookie DB fixture persists;
local-storage fixture persists;
registry survives recreate.
```

Fixtures only.

No real owner cookie values.

---

## 27. Admin Shell tests

Добавить:

```text
admin-shell/tests/test_profile_not_found_friendly_ui.py
admin-shell/tests/test_manual_avito_login_mode.py
admin-shell/tests/test_avito_access_denied_ui.py
admin-shell/tests/test_automation_compatibility_gate.py
```

---

## 28. Runtime test

После final rebuild/recreate:

```text
1. Create temporary fixture profile.
2. Launch MANUAL_BROWSER.
3. Verify process is ordinary Chrome/Chromium, not Playwright context.
4. Verify noVNC shows browser.
5. Write harmless profile fixture/state.
6. Gracefully close browser.
7. Recreate container.
8. Verify registry + browser_data persisted.
9. Reopen same profile.
```

Не использовать real Avito credentials in automated test.

---

## 29. Regression

Обязательно:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
docker compose exec -T inventory-sales-module pytest
docker compose exec -T avito-module pytest
docker compose exec -T repairs-module pytest
pytest admin-shell/tests
```

---

## 30. Safety

Проверить:

```text
credentials stored = 0
cookie values printed = 0
tracked browser profile = 0
direct DB from avito-module = 0
stealth/evasion code = 0
raw browser ports = 0
```

---

## 31. Documentation

Создать:

```text
docs/stage06a_r7_manual_browser_profile_access.md
reports/stage06a_r7_manual_browser_profile_access_report.md
```

Обновить:

```text
README.md
logs/2026-08-12.md
```

---

## 32. Report

```text
STATUS
OWNER_FINDINGS
PROFILE_NOT_FOUND_ROOT_CAUSE
PROFILE_REGISTRY
PROFILE_PERSISTENCE
CURRENT_BROWSER_AUDIT
MANUAL_BROWSER_ARCHITECTURE
PLAYWRIGHT_REMOVED_FROM_MANUAL_LOGIN
BROWSER_BINARY
PROFILE_PERMISSIONS
COOKIE_STORAGE_PERSISTENCE
LOCAL_STORAGE_PERSISTENCE
GRACEFUL_SHUTDOWN
AVITO_ACCESS_DENIED_CLASSIFICATION
DESKTOP_BROWSER_CONTROL_TEST_GUIDE
AUTOMATION_COMPATIBILITY_GATE
NO_EVASION_CONFIRMATION
TESTS
RUNTIME
REGRESSION
FILES_CHANGED
COMMIT
PUSH
FINAL_GIT_STATUS
OWNER_BROWSER_ONLY_GUIDE
FINAL_STATUS
```

---

## 33. Git

Expected HEAD:

```text
44c9807
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
git commit -m "Use persistent manual browser for Avito login"
git push origin main
```

---

## 34. Definition of Done

R7 готов только если:

```text
Profile not found root cause fixed;
profile registry persistent;
browser profile persistent;
no stale owner link;
missing profile has friendly UI;
manual login browser is not Playwright-controlled;
manual login uses persistent browser_data;
cookies/local storage writable;
browser closes gracefully;
profile survives recreate;
no credentials/cookies exposed;
AVITO_ACCESS_DENIED handled safely;
desktop-browser control test documented;
automation compatibility is separately gated;
no anti-bot evasion;
all regression tests PASS;
push complete;
git clean.
```

---

## 35. Owner check after R7

Owner sequence:

```text
1. Проверить тот же Avito account в обычном desktop browser.
2. Записать: входит / доступ закрыт.

3. Открыть http://localhost:8011
4. Авито
5. Открыть существующий профиль или создать новый.
6. Авторизоваться вручную.
7. Убедиться, что Profile not found больше нет.
8. Встроенный обычный Chrome открылся.
9. Войти в Avito вручную.
10. Записать: вошёл / доступ закрыт.
```

Если embedded manual browser вошёл:

```text
STOP.
OWNER_MANUAL_LOGIN_SUCCESS_REQUIRED: true
```

Автоматический parser пока не запускать.

---

## 36. Final status

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE06A_R7_MANUAL_BROWSER_READY_FOR_OWNER_LOGIN_CHECK

OWNER_DESKTOP_CONTROL_TEST_REQUIRED: true
OWNER_EMBEDDED_MANUAL_LOGIN_REQUIRED: true
AUTOMATION_COMPATIBILITY_NOT_YET_ACCEPTED: true
OWNER_ONE_ITEM_PROBE_NOT_YET_ACCEPTED: true
FULL_ACCOUNT_IMPORT_NOT_YET_AUTHORIZED: true
DO_NOT_START_STAGE06B_REVERSE_SYNC_WITHOUT_OWNER_ACCEPTANCE: true
```
