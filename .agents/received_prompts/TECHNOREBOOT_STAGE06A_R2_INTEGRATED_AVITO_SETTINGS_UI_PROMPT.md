# PROMPT — Техноребут / Stage06A-R2 Integrated Avito Settings UI and Zero-CLI Owner Workflow

## Роль

Ты senior solution architect, FastAPI/Jinja2 developer, Docker engineer, Playwright/noVNC runtime engineer, UX engineer и release QA проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Это продолжение:

```text
Stage06A — Avito Authenticated Catalog Bootstrap
Stage06A-R1 — Browser Runtime / Owner One-Item Probe Preparation
```

Нужно изменить пользовательский сценарий.

Владелец НЕ должен работать через PowerShell/командную строку для обычной работы с Avito.

Все действия должны выполняться из внутреннего веб-интерфейса Техноребут.

Stage06B reverse sync НЕ начинать.

---

# 1. Решение владельца

Avito integration должна выглядеть как обычный раздел информационной системы.

Пользовательский сценарий:

```text
открываю внутреннюю систему Техноребут
        ↓
перехожу в раздел «Авито»
        ↓
открываю «Настройки Авито»
        ↓
создаю профиль аккаунта
        ↓
нажимаю «Авторизоваться»
        ↓
в этой же системе открывается встроенный браузер
        ↓
вручную вхожу в Avito
        ↓
возвращаюсь в настройки
        ↓
система показывает «Авторизован»
        ↓
выбираю объявление
        ↓
запускаю пробный импорт
        ↓
сверяю результат
```

Для обычной работы пользователь НЕ выполняет:

```text
docker compose;
PowerShell;
python;
curl;
Invoke-WebRequest;
docker logs;
docker exec;
ручной запуск Chromium;
ручной запуск Xvfb;
ручной запуск noVNC.
```

---

# 2. Главный UX-принцип

Всё Avito-управление находится внутри существующей административной веб-системы.

Не заставлять владельца помнить:

```text
localhost:8020
localhost:8061
внутренние Docker-порты
VNC URL
API endpoints
```

Пользователь должен видеть нормальные разделы:

```text
Авито
 ├── Аккаунты
 ├── Импорт
 ├── История синхронизации
 └── Настройки
```

На Stage06A-R2 реально реализовать минимум:

```text
Авито
 ├── Аккаунты
 └── Пробный импорт
```

Остальные пункты можно оставить как будущую структуру, но без пустых/неработающих страниц.

---

# 3. Интеграция с существующим Admin Shell

В проекте уже есть внутренний Admin Shell.

Сначала провести аудит:

```text
admin-shell routes
navigation
reverse proxy
module links
base template
existing Russian UI conventions
```

Добавить в главное меню:

```text
Авито
```

Предпочтительный путь внутри общей системы:

```text
/avito
```

или:

```text
/admin/avito
```

Следовать существующему routing style.

Не заставлять владельца отдельно открывать:

```text
http://localhost:8020/accounts
```

---

# 4. Reverse proxy / module boundary

Avito-module остаётся отдельным Docker-модулем.

Архитектура:

```text
Browser пользователя
        ↓
Admin Shell
        ↓ proxy/internal HTTP
Avito Module
        ↓
Browser Worker / Playwright / noVNC
        ↓
Avito
```

Не сливать avito-module внутрь admin-shell.

Не давать admin-shell прямого доступа к:

```text
Core DB;
browser profile files;
cookies;
Chromium process internals.
```

---

# 5. Автоматический старт

После обычного запуска информационной системы все необходимые Avito-компоненты должны стартовать автоматически.

Минимум:

```text
core
admin-shell
avito-module
avito-browser runtime
Xvfb
x11vnc
noVNC/websockify
```

Не должно требоваться:

```text
playwright install chromium
docker compose exec ...
ручной запуск entrypoint.sh
```

Все runtime dependencies должны быть baked into Docker image.

После:

```text
docker compose up -d
```

система полностью готова.

Но это команда администратора/разработчика, НЕ повседневного пользователя.

---

# 6. Автозапуск всей системы на Windows

Добавить простой пользовательский launcher.

Предпочтительно создать:

```text
scripts/start_technoreboot.cmd
scripts/stop_technoreboot.cmd
```

или `.ps1` + `.cmd` wrapper.

`start_technoreboot.cmd`:

```text
1. Проверяет Docker Desktop availability.
2. Запускает docker compose up -d.
3. Ждёт health основных сервисов.
4. Открывает браузер на главной странице Admin Shell.
5. Не показывает пользователю технические команды при успехе.
```

При ошибке выводит понятное русское сообщение.

Дополнительно подготовить инструкцию, как создать ярлык:

```text
Техноребут
```

на рабочем столе Windows.

Не создавать сложный Windows service на этом этапе.

---

# 7. Главная страница Avito

В общей системе:

```text
/avito
```

Показывать:

```text
Статус модуля Avito
Статус браузерного сервиса
Количество настроенных аккаунтов
Авторизованные аккаунты
Последний пробный импорт
```

Основные кнопки:

```text
Аккаунты Avito
Добавить аккаунт
Пробный импорт
```

---

# 8. Страница «Аккаунты Avito»

Путь:

```text
/avito/accounts
```

или эквивалент через proxy.

Показывать карточки профилей.

Для каждого:

```text
Название профиля
Статус авторизации
Последняя проверка
Последняя успешная авторизация
Статус браузера
Последний импорт
```

Кнопки:

```text
Авторизоваться / Открыть Avito
Проверить авторизацию
Пробный импорт
Переименовать
Удалить
```

Не показывать:

```text
UUID без необходимости;
filesystem path;
cookie count;
internal VNC port;
Docker container name.
```

---

# 9. Создание профиля

Форма:

```text
Название аккаунта
```

Пример:

```text
Основной аккаунт
```

После создания:

```text
UUID создаётся автоматически;
persistent profile directory создаётся автоматически;
профиль появляется в списке.
```

Максимум:

```text
3 профиля
```

Если достигнут лимит:

```text
«Можно настроить не более 3 аккаунтов Avito.»
```

---

# 10. Встроенный браузер внутри системы

Кнопка:

```text
Авторизоваться
```

не должна отправлять пользователя вручную на `localhost:8061`.

Открывать встроенный browser view внутри интерфейса Техноребут.

Предпочтительно:

```text
/avito/accounts/{profile_id}/browser
```

Страница содержит:

```text
Заголовок: Авторизация Avito — <имя профиля>
Встроенный noVNC canvas / iframe
Кнопка «Закрыть браузер»
Кнопка «Я вошёл — проверить авторизацию»
```

Browser view должен быть встроен через внутренний reverse proxy.

---

# 11. noVNC через same-origin proxy

Не показывать пользователю raw:

```text
http://127.0.0.1:8061
```

Admin Shell или Avito module должен proxy:

```text
/avito/browser-ui/...
```

к noVNC service.

Нужно поддержать:

```text
HTTP assets;
WebSocket connection;
same-origin browser access.
```

Обязательно проверить WebSocket proxy.

---

# 12. Security browser UI

Browser/noVNC service:

```text
НЕ публиковать наружу.
```

Допустимы варианты:

```text
expose only inside Docker network;
или bind 127.0.0.1 без прямой ссылки для owner.
```

Предпочтительно:

```text
no host public port вообще;
Admin Shell proxy -> internal Docker service.
```

Это лучше, чем отдельный `8061`.

Если временно host-port остаётся для диагностики:

```text
только 127.0.0.1;
не показывать в UI;
зафиксировать как developer-only.
```

---

# 13. Browser worker — автоматическое управление

Пользователь не запускает Chromium вручную.

При открытии встроенного браузера:

```text
1. Avito module получает profile_id.
2. Проверяет browser runtime.
3. Запускает Chromium с нужным persistent user-data-dir.
4. Открывает Avito.
5. Подключает noVNC.
```

При закрытии страницы:

```text
можно оставить Chromium запущенным ограниченное время;
или завершить graceful.
```

Не терять persistent profile.

---

# 14. Один активный интерактивный профиль

На Stage06A-R2 допускается:

```text
один интерактивный Chromium одновременно.
```

Если пользователь пытается открыть второй аккаунт:

```text
«Сейчас открыт браузер аккаунта <имя>. Закройте его или переключитесь.»
```

Это проще и надёжнее.

Импорт позже может работать последовательно по профилям.

---

# 15. Статус браузера в UI

Показывать:

```text
Не запущен
Запускается
Открыт
Ошибка
```

Не показывать raw process errors владельцу.

Для деталей можно иметь:

```text
«Техническая информация»
```

с раскрывающимся блоком.

---

# 16. Авторизация

Встроенный Chromium открывает:

```text
https://www.avito.ru/
```

Owner вручную проходит:

```text
логин;
пароль;
SMS;
2FA;
CAPTCHA;
security challenge.
```

Никаких credential полей в Техноребут.

---

# 17. После авторизации

На странице встроенного браузера кнопка:

```text
Я вошёл — проверить авторизацию
```

должна:

```text
1. сохранить/зафиксировать browser profile state;
2. выполнить фактическую auth check;
3. вернуть владельца на страницу аккаунта;
4. показать результат.
```

Результаты:

```text
Авторизован
Не авторизован
Требуется подтверждение
Не удалось определить
```

---

# 18. Persistent profile

После:

```text
container recreate;
system restart;
Windows restart;
Docker restart
```

вход должен сохраняться настолько, насколько Avito сохраняет browser session.

Пользователь не должен повторно логиниться каждый раз.

Если Avito инвалидировал session:

```text
UI показывает «Требуется повторная авторизация».
```

---

# 19. Пробный импорт — только через UI

После `Авторизован` появляется:

```text
Пробный импорт
```

Пользователь НЕ использует командную строку.

Workflow:

```text
Выбрать аккаунт
        ↓
Загрузить мои объявления
        ↓
Выбрать одно объявление
        ↓
Предпросмотр
        ↓
Импортировать
        ↓
Результат
```

---

# 20. «Мои объявления»

Кнопка:

```text
Загрузить мои объявления
```

Система:

```text
использует persistent profile;
открывает own listings;
извлекает список;
возвращает в UI.
```

Показывать:

```text
Avito ID
Название
Цена
Статус
Миниатюра
Ссылка «Открыть на Avito»
```

---

# 21. Выбор объявления

У каждого item:

```text
Выбрать для пробного импорта
```

После выбора показать preview:

```text
Название
Цена
Категория
Описание — первые строки
Характеристики
Количество фото
Remote status
Avito ID
URL
```

---

# 22. Пробный импорт

Кнопка:

```text
Импортировать в Техноребут
```

После:

```text
Product ID
Created / Updated / Unchanged
Количество фото
External ID
```

Кнопки:

```text
Открыть товар
Повторить импорт
Назад к объявлениям
```

---

# 23. Проверка идемпотентности через UI

После первого импорта UI должен позволить:

```text
Повторить импорт
```

И показать:

```text
Товар не продублирован
Product ID: тот же
Фото: без дублей
```

Не заставлять owner считать Product count вручную.

---

# 24. Автоматическая owner-check диагностика

После второго импорта система сама проверяет:

```text
same product_id;
same external listing id;
product count delta = 0;
photo duplicate delta = 0.
```

Показывать результат:

```text
Проверка дублей: пройдена
```

или:

```text
Обнаружена проблема дедупликации
```

---

# 25. Full import gate

До успешного пробного импорта:

```text
Полный импорт аккаунта
```

неактивен.

После:

```text
первый импорт PASS;
повторный импорт PASS;
owner нажал «Пробный импорт проверен»
```

можно разблокировать full import.

Но Stage06A-R2 НЕ запускает full import автоматически.

---

# 26. Owner acceptance button

Добавить локальное подтверждение в UI:

```text
Пробный импорт проверен
```

Это НЕ заменяет процесс owner acceptance в разработке, но хранит operational state.

После нажатия:

```text
profile.probe_verified = true
```

или аналог в avito-module operational storage.

Не писать этот operational flag напрямую в Core DB, если в этом нет необходимости.

---

# 27. Авто health checks

Страница `/avito` должна сама показывать:

```text
Core: работает
Avito module: работает
Browser runtime: работает
Chromium: доступен
Profile storage: доступен
```

Без PowerShell.

Кнопка:

```text
Проверить систему
```

запускает safe diagnostics.

---

# 28. Safe self-diagnostics endpoint

Добавить read-only endpoint:

```text
GET /health/details
```

или:

```text
GET /avito/health
```

Возвращает:

```json
{
  "module": "ok",
  "core": "ok",
  "browser_runtime": "ok",
  "chromium": "ok",
  "profile_storage": "ok"
}
```

Не возвращать:

```text
cookies;
filesystem secrets;
tokens;
credentials.
```

---

# 29. Ошибки для владельца

Все ошибки в UI — на русском.

Примеры:

```text
«Не удалось запустить браузер Avito.»
«Сессия Avito истекла. Авторизуйтесь повторно.»
«Avito запросил дополнительное подтверждение.»
«Не удалось загрузить список объявлений.»
«Объявление не импортировано. Подробности сохранены в журнале.»
```

Не показывать traceback.

---

# 30. Developer logs

Подробные traceback остаются в:

```text
docker logs
application logs
```

но не являются частью owner workflow.

UI может иметь:

```text
Код ошибки: AVITO_BROWSER_START_FAILED
```

для поддержки.

---

# 31. Admin Shell navigation

Добавить `Авито` в основное русское меню рядом с существующими модулями.

Не открывать модуль в новой вкладке без необходимости.

Пользователь должен ощущать единую систему.

---

# 32. Визуальная консистентность

Использовать текущий стиль Admin Shell:

```text
шрифты;
кнопки;
таблицы;
cards;
messages;
navigation.
```

Не делать отдельный «чужой» интерфейс.

---

# 33. Existing direct Avito port

Существующий developer URL:

```text
http://localhost:8020
```

можно сохранить для разработки.

Но owner documentation должна использовать только общий интерфейс:

```text
Admin Shell -> Авито
```

---

# 34. Docker compose

Проверить и довести:

```text
restart: unless-stopped
healthcheck
depends_on
persistent volumes
internal network
```

для:

```text
avito-module
browser/noVNC runtime
```

При старте системы всё поднимается автоматически.

---

# 35. Entrypoint

Entry point должен автоматически:

```text
проверить display;
запустить Xvfb;
запустить x11vnc;
запустить websockify/noVNC;
запустить API;
```

или эквивалент для выбранной архитектуры.

Не требовать пост-install команд.

---

# 36. Browser runtime proof

После build/recreate автоматическими тестами доказать:

```text
Chromium executable exists;
Chromium launches;
Xvfb alive;
x11vnc alive;
websockify alive;
noVNC HTTP asset available;
WebSocket proxy works.
```

---

# 37. No command-line owner acceptance

Definition of Done включает UX-тест:

```text
новый пользователь может пройти:
создание профиля
-> авторизация
-> auth check
-> discovery
-> preview
-> one-item import
-> repeat import

не выполняя ни одной shell-команды.
```

---

# 38. Tests — Admin Shell

Создать/обновить:

```text
admin-shell/tests/test_avito_navigation.py
admin-shell/tests/test_avito_proxy.py
admin-shell/tests/test_avito_browser_proxy.py
```

Проверить:

```text
есть меню Авито;
страницы доступны через общий shell;
HTTP proxy работает;
WebSocket/noVNC proxy contract присутствует;
raw internal ports не показываются owner UI.
```

---

# 39. Tests — Avito Module

Создать/обновить:

```text
avito-module/tests/test_integrated_accounts_ui.py
avito-module/tests/test_browser_auto_start.py
avito-module/tests/test_browser_session_switch.py
avito-module/tests/test_owner_probe_ui.py
avito-module/tests/test_probe_dedup_ui.py
avito-module/tests/test_health_details.py
```

Проверить:

```text
browser auto start;
profile launch;
auth check;
discovery;
preview;
one item import;
repeat import;
dedup result;
full import disabled before verification.
```

---

# 40. Regression

Обязательно:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
docker compose exec -T inventory-sales-module pytest
docker compose exec -T avito-module pytest
docker compose exec -T repairs-module pytest
```

Плюс Admin Shell tests согласно существующему способу запуска.

---

# 41. Runtime automated browser test

После final image recreate:

```text
1. Open Admin Shell.
2. Navigate to Avito.
3. Create temporary test profile.
4. Open embedded browser.
5. Browser loads example.com or Avito landing page.
6. noVNC content visible.
7. Close.
8. Recreate avito services.
9. Profile still exists.
```

Не логиниться реальным аккаунтом автоматически.

---

# 42. Owner runtime workflow after R2

После автоматической реализации агент останавливается.

Владелец делает ТОЛЬКО в браузере:

```text
1. Открывает Техноребут.
2. Авито.
3. Аккаунты.
4. Добавить аккаунт.
5. Авторизоваться.
6. Встроенный браузер Avito.
7. Входит.
8. «Я вошёл — проверить».
9. «Загрузить мои объявления».
10. Выбирает одно.
11. Preview.
12. «Импортировать».
13. «Открыть товар».
14. Сверяет.
15. «Повторить импорт».
16. Видит «Проверка дублей: пройдена».
17. Нажимает «Пробный импорт проверен».
```

Ни одной shell-команды.

---

# 43. Full import still gated

После Stage06A-R2:

```text
FULL_ACCOUNT_IMPORT_NOT_AUTOMATIC: true
```

Разрешить owner вручную начать full import только после успешного probe.

Не запускать автоматически при авторизации.

---

# 44. Existing source_origin fix

Сохранить требования R1:

```text
Product default source_origin != avito;
Avito import explicitly source_origin=avito.
```

Обязательно доказать тестами.

---

# 45. Profile naming

Сохранить требования R1:

```text
нет Main/Laptops/Office hardcode;
имя вводит пользователь;
до 3 профилей.
```

---

# 46. Secrets

Не хранить:

```text
пароли;
SMS;
2FA code;
CAPTCHA answers.
```

Session profile:

```text
persistent runtime storage;
gitignored;
не попадает в API response.
```

---

# 47. Safety scans

Проверить:

```text
direct DB access из avito-module = 0;
tracked browser sessions = 0;
raw password/token hardcode = 0;
public noVNC port = 0 или localhost-only.
```

---

# 48. Documentation

Создать:

```text
docs/stage06a_r2_integrated_avito_settings_ui.md
reports/stage06a_r2_integrated_avito_settings_ui_report.md
```

Обновить:

```text
README.md
logs/2026-08-11.md
```

---

# 49. Report

```text
# Stage06A-R2 Integrated Avito Settings UI Report

## STATUS
## OWNER_REQUIREMENT
## PREFLIGHT
## ADMIN_SHELL_AUDIT
## AVITO_MODULE_AUDIT
## DOCKER_AUTO_START
## WINDOWS_LAUNCHER
## ADMIN_NAVIGATION
## AVITO_HOME
## ACCOUNT_UI
## PROFILE_CREATE
## PROFILE_PERSISTENCE
## EMBEDDED_BROWSER
## NOVNC_PROXY
## WEBSOCKET_PROXY
## BROWSER_AUTO_START
## AUTH_FLOW
## AUTH_STATE
## HEALTH_UI
## OWN_LISTINGS_DISCOVERY
## PREVIEW
## ONE_ITEM_IMPORT
## REPEAT_IMPORT
## DEDUP_AUTOCHECK
## FULL_IMPORT_GATE
## SOURCE_ORIGIN_FIX
## PROFILE_NAME_FIX
## SECURITY
## TESTS
## RUNTIME
## FILES_CHANGED
## COMMIT
## PUSH
## FINAL_GIT_STATUS
## OWNER_BROWSER_ONLY_GUIDE
## FINAL_STATUS
```

---

# 50. Git safety

Только targeted add.

Не использовать:

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

Expected starting HEAD:

```text
фактический HEAD после Stage06A-R1 work
```

Коммит:

```powershell
git commit -m "Integrate Avito settings into admin UI"
git push origin main
```

---

# 51. Definition of Done

Готово только если:

```text
Avito доступен из главного меню Техноребут;
owner не использует отдельный 8020 URL;
owner не использует 8061 URL;
owner не запускает Docker вручную для Avito;
browser runtime автоматически стартует;
Chromium установлен в image;
noVNC автоматически стартует;
browser UI встроен в Техноребут;
WebSocket proxy работает;
профиль создаётся из UI;
имя профиля owner-defined;
до 3 профилей;
профиль persistent;
login выполняется внутри встроенного браузера;
auth check выполняется кнопкой;
discovery выполняется кнопкой;
preview выполняется в UI;
one-item import выполняется в UI;
repeat import выполняется в UI;
dedup проверяется автоматически;
full import gated;
source_origin default исправлен;
Avito import явно ставит avito;
нет прямого DB access;
нет credential storage;
нет session files в Git;
Core tests PASS;
Inventory tests PASS;
Avito tests PASS;
Repairs tests PASS;
Admin Shell tests PASS;
targeted commit;
push;
clean Git.
```

---

# 52. Final status

После автоматизированной реализации:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE06A_R2_INTEGRATED_AVITO_UI_READY_FOR_OWNER_BROWSER_ONLY_PROBE

OWNER_BROWSER_ONLY_PROBE_REQUIRED: true
FULL_ACCOUNT_IMPORT_NOT_YET_AUTHORIZED: true
DO_NOT_START_STAGE06B_REVERSE_SYNC_WITHOUT_OWNER_ACCEPTANCE: true
```

Если embedded browser / WebSocket proxy не удаётся стабильно реализовать:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE06A_R2_INTEGRATED_AVITO_UI_BLOCKED

BLOCKERS:
...
OWNER_DECISION_REQUIRED: true
```
