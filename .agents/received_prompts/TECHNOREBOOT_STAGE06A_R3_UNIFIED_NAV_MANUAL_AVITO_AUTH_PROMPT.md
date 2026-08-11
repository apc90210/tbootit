# PROMPT — Техноребут / Stage06A-R3 Unified Admin Navigation + Mandatory Manual Avito Login + Browser-Session Parsing

## Роль

Ты senior solution architect, FastAPI/Jinja2 developer, reverse-proxy engineer, Playwright engineer, Docker engineer, UX engineer и release QA проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Это corrective stage после:

```text
Stage06A-R2
Commit: fcca2bd
```

НЕ начинать Stage06B reverse sync.

---

# 1. Причина R3 — реальные замечания владельца

Владелец вручную проверил UI и обнаружил:

```text
1. Верхнее меню содержит перекрёстные ссылки,
   которые уводят на другие localhost-порты.

2. После перехода на другой модуль общий верхний интерфейс пропадает,
   в том числе исчезает пункт «Авито».

3. Непонятно, где именно авторизоваться в Avito.

4. Требуется обязательная ручная авторизация
   во встроенном браузере внутри информационной системы.

5. Только ПОСЛЕ ручной авторизации система может использовать
   этот же persistent browser profile для работы с «Моими объявлениями».
```

Эти замечания — BLOCKER для Stage06A.

---

# 2. Главный UX-контракт всей системы

Пользователь работает только с одним базовым адресом:

```text
http://localhost:8011
```

Все пользовательские разделы должны открываться внутри единой оболочки:

```text
Главная
Товары / Остатки
Продажи
Ремонты
Авито
...
```

Запрещено owner-facing переходить напрямую на:

```text
http://localhost:8020
http://localhost:8030
http://localhost:8040
http://localhost:8061
```

или любой другой module port.

Эти порты могут существовать внутри Docker/для разработчика,
но не должны быть частью обычного пользовательского сценария.

---

# 3. Единое верхнее меню

Верхнее меню должно оставаться видимым на ВСЕХ owner-facing страницах.

После перехода:

```text
Товары
Продажи
Ремонты
Авито
```

пользователь остаётся в общей оболочке.

Не должно происходить:

```text
переход на raw module port;
потеря Admin Shell navigation;
появление другого независимого header;
исчезновение пункта «Авито».
```

---

# 4. Аудит всех ссылок меню

Найти ВСЕ owner-facing ссылки:

```text
href="http://localhost:..."
href="http://127.0.0.1:..."
window.location = ...
redirect(... localhost ...)
hardcoded module port
```

Проверить:

```text
admin-shell templates
inventory-sales templates
repairs templates
avito templates
README owner links
```

Составить таблицу:

```text
LABEL
OLD_URL
NEW_SAME_ORIGIN_URL
```

---

# 5. Same-origin routes

Использовать единые пути, например:

```text
/                    Главная
/inventory           Товары / Остатки
/sales               Продажи
/repairs             Ремонты
/avito               Авито
```

Точные пути подстроить под текущую архитектуру.

Важно:

```text
в адресной строке owner остаётся на localhost:8011.
```

---

# 6. Reverse proxy strategy

Не переписывать все модули внутрь admin-shell.

Предпочтительно:

```text
Admin Shell
    ↓
same-origin HTTP reverse proxy
    ↓
отдельные Docker modules
```

При необходимости обеспечить:

```text
path prefix rewrite;
relative redirects;
Location header rewrite;
query parameters;
POST forms;
cookies if они используются;
WebSocket для noVNC.
```

---

# 7. Internal links from proxied modules

Критически важно.

Если внутри Repairs/Inventory/Avito есть ссылки:

```text
/
../
http://localhost:8040/...
```

они не должны выбрасывать пользователя из shell.

Использовать:

```text
X-Forwarded-Prefix
root_path
proxy-aware URL generation
или server-side rewrite
```

Выбрать устойчивое решение.

---

# 8. One shell, one navigation

Рекомендуемый UX:

```text
+-----------------------------------------------------------+
| Техноребут | Товары | Продажи | Ремонты | Авито | ...    |
+-----------------------------------------------------------+
|                                                           |
|                 текущий модуль                            |
|                                                           |
+-----------------------------------------------------------+
```

Не использовать внешний iframe для обычных модулей,
если нормальный reverse proxy решается корректно.

Для noVNC iframe/canvas допустим.

---

# 9. Авито — явный вход в настройки

Раздел:

```text
Авито
```

должен открывать понятную стартовую страницу.

На ней крупно:

```text
Настройки Avito
```

и блок:

```text
Аккаунты Avito
```

Основной CTA:

```text
+ Добавить аккаунт
```

Если аккаунт уже создан:

```text
Авторизоваться в Avito
```

Должно быть очевидно, где начинается авторизация.

---

# 10. Убрать неоднозначность

Не заставлять пользователя угадывать между:

```text
Аккаунты
Проверить
Browser
Probe
Settings
```

Главный сценарий одного аккаунта:

```text
1. Добавить аккаунт
2. Авторизоваться
3. Проверить авторизацию
4. Загрузить мои объявления
5. Пробный импорт
```

Показывать это как пошаговый wizard/stepper.

---

# 11. Stepper состояния аккаунта

Для каждого профиля:

```text
Шаг 1. Профиль создан
Шаг 2. Авторизация
Шаг 3. Авторизация подтверждена
Шаг 4. Объявления доступны
Шаг 5. Пробный импорт
```

Текущий шаг выделен.

Недоступные шаги disabled.

---

# 12. Обязательная ручная авторизация

Никакой автоматической авторизации.

При нажатии:

```text
Авторизоваться в Avito
```

открывается:

```text
/avito/accounts/{account_key}/browser
```

внутри общего интерфейса Техноребут.

На странице:

```text
Заголовок: Авторизация Avito
Подзаголовок: Войдите в свой аккаунт вручную
```

---

# 13. Встроенный браузер

В страницу встроен обычный интерактивный Chromium через noVNC.

Пользователь вручную:

```text
вводит логин;
вводит пароль;
получает SMS;
вводит 2FA;
проходит CAPTCHA;
подтверждает устройство;
```

Все это происходит непосредственно на сайте Avito внутри Chromium.

Техноребут НЕ содержит собственных полей:

```text
Логин Avito
Пароль Avito
SMS-код
```

---

# 14. Browser profile

Для аккаунта используется отдельный persistent Chromium user-data-dir.

Связь:

```text
AvitoAccountProfile
    ↓
browser_profile_uuid
    ↓
persistent Chromium profile
```

После успешного ручного входа тот же профиль используется для:

```text
auth check;
просмотра «Моих объявлений»;
открытия карточек;
извлечения данных;
будущей синхронизации.
```

---

# 15. Никакого отдельного headless login profile

Не создавать:

```text
один profile для manual login;
другой profile для parser.
```

Должен использоваться один и тот же browser profile.

Иначе ручная авторизация теряет смысл.

---

# 16. Проверка после ручного входа

На странице браузера разместить заметную кнопку:

```text
Я вошёл в Avito — продолжить
```

После нажатия система:

```text
не закрывает/не теряет profile;
проверяет фактическую авторизацию;
переходит обратно в аккаунт;
показывает статус.
```

Результат:

```text
✓ Авторизован
```

или:

```text
Требуется дополнительное подтверждение
```

---

# 17. Нельзя перейти к parsing до auth

Endpoints/UI для:

```text
Загрузить мои объявления
Пробный импорт
Полный импорт
```

должны проверять:

```text
auth_state == authorized
```

Иначе:

```text
HTTP 409 / controlled response
«Сначала авторизуйтесь в Avito.»
```

---

# 18. Как работать после авторизации

После ручной авторизации система использует обычный браузерный контекст.

Технический workflow:

```text
persistent Chromium context
        ↓
страница «Мои объявления»
        ↓
последовательная навигация
        ↓
карточка собственного объявления
        ↓
извлечение данных
        ↓
Core API
```

---

# 19. Browser-first extraction

Приоритет:

```text
авторизованный браузерный DOM;
structured data страницы;
стабильные data attributes;
JSON-LD;
видимый текст.
```

Не использовать отдельный anonymous HTTP scraper как основной runtime path
для собственных объявлений.

---

# 20. Важное ограничение — без anti-bot evasion

Владелец хочет, чтобы работа шла максимально похоже на обычную работу пользователя через браузер.

Реализовать безопасно:

```text
обычный Chromium;
реальный persistent profile;
один аккаунт;
последовательная навигация;
разумные интервалы;
низкая concurrency;
обычные page interactions.
```

НЕ реализовывать:

```text
stealth plugin;
navigator.webdriver spoof;
fingerprint spoof;
canvas spoof;
proxy rotation;
IP rotation;
CAPTCHA bypass;
SMS bypass;
anti-bot bypass;
маскировку automation flags;
обход rate limits.
```

Если Avito требует challenge:

```text
остановить автоматическую работу;
показать owner:
«Avito запросил подтверждение. Откройте браузер.»
```

---

# 21. Sequential / human-scale operation

Для собственных объявлений:

```text
1 active page
или максимум 1–2 controlled pages.
```

Не использовать десятки parallel tabs.

Добавить небольшие технические паузы только для стабильности UI:

```text
wait for DOM;
wait for network idle where suitable;
explicit element readiness.
```

Не делать random delay engine для сокрытия automation.

---

# 22. Состояние «Требуется участие пользователя»

Добавить operational state:

```text
USER_ACTION_REQUIRED
```

Причины:

```text
authorization expired;
CAPTCHA;
SMS;
2FA;
Avito security challenge;
unexpected login page.
```

UI:

```text
Требуется действие
[Открыть браузер]
```

---

# 23. После успешной авторизации

Страница аккаунта:

```text
Основной Avito
Статус: ✓ Авторизован
```

Показывать:

```text
[Открыть Avito]
[Загрузить мои объявления]
[Пробный импорт]
```

---

# 24. «Загрузить мои объявления»

При нажатии система:

```text
открывает persistent context;
переходит в «Мои объявления»;
убеждается, что аккаунт авторизован;
получает список только собственных объявлений.
```

Если вместо кабинета открылась login page:

```text
auth_state = unauthorized
вернуть в UI:
«Сессия истекла. Авторизуйтесь повторно.»
```

---

# 25. Не парсить публичный аккаунт по seller page

Источник списка:

```text
внутренний раздел собственных объявлений
```

а не внешний публичный профиль продавца,
если personal cabinet даёт необходимые данные.

---

# 26. Listing ownership safety

Каждый listing импортируется только если найден через:

```text
My Listings / собственный кабинет
```

или официальное API собственного аккаунта.

Не принимать произвольный URL в production import flow как доказательство ownership.

---

# 27. Пробный импорт

После discovery:

```text
список собственных объявлений
```

Owner выбирает одно.

Показывается:

```text
Avito ID
Название
Цена
Статус
Фото
URL
```

Кнопка:

```text
Открыть предпросмотр
```

---

# 28. Preview

Preview извлекается тем же browser context.

Показывать:

```text
название;
цена;
описание;
категория;
бренд;
модель;
характеристики;
фотографии;
статус;
Avito ID;
URL.
```

---

# 29. Import

Кнопка:

```text
Импортировать в Техноребут
```

посылает normalised data в существующий Core integration endpoint.

Не создавать новую параллельную import architecture.

---

# 30. Repeat import

В UI:

```text
Повторить импорт
```

После:

```text
Product ID same
ExternalListing same
Photos deduplicated
```

Показать:

```text
✓ Дубликатов не обнаружено
```

---

# 31. Navigation после открытия товара

Кнопка:

```text
Открыть товар
```

должна вести через SAME-ORIGIN Admin Shell route.

НЕ:

```text
http://localhost:8030/...
```

А:

```text
http://localhost:8011/<proxied-product-path>
```

После открытия товара верхнее меню остаётся.

---

# 32. Repair links / Sales links / Product links

Провести отдельный аудит cross-module links.

Примеры проблем:

```text
Sale -> Product
Repair -> Sale
Sale -> Repair
Avito -> Product
```

Все owner-facing cross-module links должны использовать same-origin Admin Shell paths.

---

# 33. Canonical URL builder

Создать единый helper/config:

```text
admin_url(...)
```

или:

```text
PUBLIC_BASE_URL
```

Не разбрасывать по templates:

```text
localhost:8030
localhost:8040
localhost:8020
```

---

# 34. Developer raw URLs

Raw module URLs можно оставить:

```text
developer-only;
tests;
internal health;
Docker network.
```

Но в owner-facing HTML:

```text
0 hardcoded raw module ports.
```

Добавить test на это.

---

# 35. Browser UI same-origin

noVNC должен продолжать работать:

```text
localhost:8011/avito/...
```

WebSocket также same-origin.

Проверить:

```text
HTTP assets;
JS;
WebSocket handshake;
keyboard input;
mouse input;
clipboard optional.
```

---

# 36. Автоматический browser runtime

Сохранить R2:

```text
Xvfb automatically starts;
x11vnc automatically starts;
noVNC automatically starts;
Chromium automatically launched on owner request;
profile automatically selected.
```

User CLI = 0.

---

# 37. UI health

На странице Avito показывать только понятное:

```text
Система Avito: работает
Браузер: готов
```

Если проблема:

```text
«Браузер Avito недоступен.»
```

Не показывать raw ports/process names как основной текст.

---

# 38. Tests — unified navigation

Создать:

```text
admin-shell/tests/test_unified_navigation.py
admin-shell/tests/test_no_owner_raw_module_ports.py
admin-shell/tests/test_cross_module_links_same_origin.py
```

Проверить:

```text
верхнее меню есть на proxied views;
inventory link stays :8011;
sales link stays :8011;
repairs link stays :8011;
avito link stays :8011;
Avito -> Product stays :8011;
нет href localhost:8020/8030/8040/8061 в owner HTML.
```

---

# 39. Tests — mandatory manual auth

Создать/обновить:

```text
avito-module/tests/test_manual_auth_required.py
avito-module/tests/test_same_profile_for_manual_and_parse.py
avito-module/tests/test_parse_blocked_without_auth.py
avito-module/tests/test_user_action_required.py
avito-module/tests/test_my_listings_requires_auth.py
```

Проверить:

```text
new profile unauthorized;
discovery blocked;
probe blocked;
manual browser launch works;
after mocked auth same profile path reused;
expired auth -> USER_ACTION_REQUIRED.
```

---

# 40. Tests — no evasion

Добавить source scan test:

```text
stealth
fingerprint spoof
navigator.webdriver override
proxy rotation
captcha solver
```

должны отсутствовать в production code.

---

# 41. Runtime owner test — browser only

После agent implementation owner делает ТОЛЬКО:

```text
1. Открыть http://localhost:8011
2. Проверить меню.
3. Перейти Товары.
4. Перейти Продажи.
5. Перейти Ремонты.
6. Перейти Авито.
7. Убедиться, что header не исчезает.
8. Авито -> Добавить аккаунт.
9. Авторизоваться.
10. Встроенный Chromium.
11. Вручную войти.
12. «Я вошёл — продолжить».
13. Увидеть «Авторизован».
14. «Загрузить мои объявления».
15. Выбрать одно.
16. Preview.
17. Import.
18. Открыть товар.
19. Убедиться, что меню осталось.
20. Repeat import.
21. Убедиться, что дублей нет.
```

Никаких shell-команд.

---

# 42. Full import остаётся gated

После R3:

```text
FULL_ACCOUNT_IMPORT_NOT_YET_AUTHORIZED: true
```

До успешной owner проверки одного реального объявления.

---

# 43. Regression

Обязательно:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
docker compose exec -T inventory-sales-module pytest
docker compose exec -T avito-module pytest
docker compose exec -T repairs-module pytest
```

Admin Shell:

```powershell
pytest admin-shell/tests
```

---

# 44. Safety

Проверить:

```text
direct DB from avito-module = 0;
credentials stored = 0;
browser session files tracked = 0;
owner-facing raw module URLs = 0;
public noVNC exposure = 0;
anti-bot evasion code = 0.
```

---

# 45. Documentation

Создать:

```text
docs/stage06a_r3_unified_navigation_manual_avito_auth.md
reports/stage06a_r3_unified_navigation_manual_avito_auth_report.md
```

Обновить:

```text
README.md
logs/2026-08-11.md
```

---

# 46. Report

```text
# Stage06A-R3 Unified Navigation + Manual Avito Auth Report

## STATUS
## OWNER_FINDINGS
## ROOT_CAUSE_CROSS_PORT_NAVIGATION
## OWNER_URL_CONTRACT
## ADMIN_SHELL_PROXY_ARCHITECTURE
## MENU_BEFORE
## MENU_AFTER
## CROSS_MODULE_LINK_AUDIT
## RAW_PORT_SCAN
## AVITO_ENTRY_UX
## AVITO_ACCOUNT_STEPPER
## MANUAL_AUTH_FLOW
## EMBEDDED_BROWSER
## SAME_PROFILE_PROOF
## AUTH_GATE
## USER_ACTION_REQUIRED
## MY_LISTINGS_BROWSER_FLOW
## BROWSER_FIRST_EXTRACTION
## NO_ANTIBOT_EVASION
## PREVIEW
## ONE_ITEM_IMPORT
## REPEAT_IMPORT
## DEDUP_CHECK
## TESTS
## RUNTIME
## SECURITY
## FILES_CHANGED
## COMMIT
## PUSH
## FINAL_GIT_STATUS
## OWNER_BROWSER_ONLY_GUIDE
## FINAL_STATUS
```

---

# 47. Git

Expected starting point:

```text
fcca2bd
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
git commit -m "Unify navigation and require manual Avito login"
git push origin main
```

---

# 48. Definition of Done

R3 готов только если:

```text
единый owner URL localhost:8011;
верхнее меню остаётся на всех разделах;
Товары не уводят на raw port;
Продажи не уводят на raw port;
Ремонты не уводят на raw port;
Авито не уводит на raw port;
Avito -> Product same-origin;
0 owner-facing raw module URLs;
в Avito очевидна кнопка «Авторизоваться»;
manual login обязателен;
login происходит во встроенном Chromium;
тот же persistent profile используется parser-ом;
без auth parsing blocked;
«Мои объявления» читаются через авторизованный browser context;
challenge -> USER_ACTION_REQUIRED;
никаких stealth/fingerprint/CAPTCHA bypass механизмов;
one-item preview/import работает;
repeat import не создаёт дублей;
full import gated;
Core PASS;
Inventory PASS;
Avito PASS;
Repairs PASS;
Admin Shell PASS;
targeted commit;
push;
clean Git.
```

---

# 49. Final status

После автоматизированной реализации:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE06A_R3_UNIFIED_NAV_MANUAL_AVITO_AUTH_READY_FOR_OWNER_BROWSER_PROBE

OWNER_BROWSER_ONLY_PROBE_REQUIRED: true
FULL_ACCOUNT_IMPORT_NOT_YET_AUTHORIZED: true
DO_NOT_START_STAGE06B_REVERSE_SYNC_WITHOUT_OWNER_ACCEPTANCE: true
```

Если same-origin proxy для какого-либо модуля не удаётся реализовать без поломки:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE06A_R3_BLOCKED

BLOCKERS:
...
OWNER_DECISION_REQUIRED: true
```
