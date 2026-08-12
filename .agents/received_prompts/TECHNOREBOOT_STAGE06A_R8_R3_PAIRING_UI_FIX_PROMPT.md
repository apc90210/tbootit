# TECHNOREBOOT — Stage06A-R8-R3 Fix Extension Pairing UI / Missing Code Input

Репозиторий:

```powershell
C:\tbootit
```

Стартовая точка:

```text
Stage06A-R8-R2
Commit: 42ea7ed
```

Это corrective stage. Не начинать R9 и Stage06B.

---

## 1. Реальный owner blocker

Расширение Chrome успешно установлено и работает на реальном Avito.

Owner видит:

```text
Техноребут Avito
Подключен

✓ Подключено к локальному серверу Техноребут.

Карточка объявления
...
[Передать объявление в Техноребут]

Расширение не привязано к Техноребут.
Введите код подключения.
```

Но при этом в popup:

```text
НЕТ поля для ввода 6-значного кода;
НЕТ кнопки «Подключить».
```

Следовательно:

```text
server availability работает;
page parser работает;
pairing UI state broken.
```

R8-R2 НЕ принят как рабочий pairing flow.

---

## 2. Главная причина для аудита

Не предполагать, а проверить код.

Вероятная архитектурная ошибка:

```text
server_reachable
```

и

```text
extension_paired
```

обрабатываются как одно состояние.

Нужно разделить минимум:

```text
server_reachable: bool
paired: bool
token_valid: bool
page_detected: bool
```

---

## 3. Правильная state machine

### STATE A — сервер недоступен

```text
server_reachable = false
```

UI:

```text
Сервер Техноребут недоступен
Проверьте, что система запущена
```

Pairing form disabled/hidden.

---

### STATE B — сервер доступен, расширение НЕ привязано

```text
server_reachable = true
paired = false
```

Это текущий owner case.

UI ОБЯЗАТЕЛЬНО:

```text
✓ Сервер Техноребут доступен

Подключение расширения
Введите 6-значный код из Техноребут

[______]
[Подключить]
```

И дополнительно:

```text
Передать объявление в Техноребут
```

должна быть disabled.

---

### STATE C — token сохранён, но недействителен

Например:

```text
401
403
expired/revoked token
```

UI:

```text
Привязка устарела.
Подключите расширение заново.

[______]
[Подключить]
```

Старый token удалить/очистить безопасно.

---

### STATE D — расширение успешно привязано

```text
server_reachable = true
paired = true
token_valid = true
```

UI:

```text
✓ Сервер доступен
✓ Расширение привязано
```

Pairing form скрыта.

Кнопка:

```text
Передать объявление в Техноребут
```

enabled только если page/listing detected.

---

## 4. Исправить тексты статусов

Текущий верхний статус:

```text
Подключен
```

сбивает owner с толку, потому что фактически означает только доступность localhost.

Заменить на:

```text
Сервер доступен
```

или:

```text
Техноребут доступен
```

После pairing отдельно:

```text
Расширение привязано
```

Не использовать одно слово `Подключен` для двух разных состояний.

---

## 5. Popup UX

При unpaired state popup должен выглядеть примерно:

```text
Техноребут Avito

✓ Сервер Техноребут доступен

Подключение расширения

Введите 6-значный код,
который показан в Техноребут:

[  _ _ _ _ _ _  ]

[ Подключить ]

Карточка объявления:
...
Передача станет доступна после подключения.
```

---

## 6. Code input

Поле:

```html
<input
  type="text"
  inputmode="numeric"
  maxlength="6"
  pattern="[0-9]{6}"
  autocomplete="one-time-code"
>
```

Validation:

```text
ровно 6 цифр;
не принимать буквы;
trim spaces;
понятная русская ошибка.
```

---

## 7. Pair button

При submit:

```text
POST /admin-api/avito-extension/pairing/pair
```

или фактический endpoint.

Payload:

```json
{
  "pair_code": "123456"
}
```

После success:

```text
token сохранить в chrome.storage.local;
сразу heartbeat/token validation;
перерисовать popup;
показать «Расширение привязано».
```

---

## 8. Pairing error UX

### Неверный код

```text
«Код подключения неверный.»
```

### Истёк

```text
«Срок действия кода истёк. Создайте новый код в Техноребут.»
```

### Server unavailable

```text
«Не удалось подключиться к Техноребут.»
```

### Unknown server error

```text
«Не удалось привязать расширение.»
```

Не показывать raw JSON/traceback.

---

## 9. Token state on popup open

При каждом открытии popup:

```text
1. GET/status — server reachable?
2. chrome.storage.local — token exists?
3. if token exists:
   heartbeat/token check
4. derive paired/token_valid
5. render one consistent state
```

Не рендерить UI раньше окончания state resolution, если из-за этого возникает мигание неправильного состояния.

---

## 10. Green transfer button

Сейчас кнопка визуально активна даже при сообщении:

```text
«Расширение не привязано»
```

Это неверно.

Контракт:

```text
paired = false
→ transfer button disabled
```

После pairing:

```text
paired = true
AND page_detected = true
→ enabled
```

---

## 11. Content parser не менять

По owner screenshot parser уже распознаёт:

```text
title
Avito ID
price
```

R8-R3 НЕ переписывает `content.js` parser без необходимости.

Фокус:

```text
pairing UI
pairing state
token validation
button enable/disable
```

---

## 12. Existing listing owner test fixture

Использовать sanitised fixture/realistic state:

```text
title: Лазерный цветной принтер hp m252n на запчасти
external_item_id: 8313765236
price: 7099
```

Только как тестовые данные, без owner secrets.

---

## 13. Extension tests

Добавить/обновить:

```text
chrome-extension/technoreboot-avito/tests/test_popup_pairing_states.py
chrome-extension/technoreboot-avito/tests/test_popup_unpaired_shows_code_input.py
chrome-extension/technoreboot-avito/tests/test_popup_paired_hides_code_input.py
chrome-extension/technoreboot-avito/tests/test_transfer_disabled_until_paired.py
chrome-extension/technoreboot-avito/tests/test_invalid_token_returns_to_pairing.py
```

---

## 14. Explicit regression test for owner bug

Обязательный тест:

```text
server_reachable = true
token = absent
```

Expected DOM:

```text
pair code input visible
Подключить button visible
transfer button disabled
text «Сервер доступен»
text НЕ утверждает «Расширение привязано»
```

Назвать:

```text
test_server_reachable_unpaired_still_shows_pairing_form
```

---

## 15. Pairing integration test

Через mocked/local bridge:

```text
generate code
→ popup enters code
→ pair endpoint success
→ token stored
→ heartbeat success
→ popup shows paired
→ transfer enabled when listing detected
```

---

## 16. Version bump

Поднять extension patch version:

```text
0.1.1 → 0.1.2
```

Обновить:

```text
manifest.json
popup footer
service worker version constant
bridge supported extension version
download filename
Admin Shell version label
```

---

## 17. Build/package

После изменений:

```text
build extension ZIP
validate manifest/resources
live download validation
```

Новая версия:

```text
technoreboot-avito-extension-0.1.2.zip
```

---

## 18. Cache

Сохранить:

```text
Cache-Control: no-store
```

Owner должен получить именно 0.1.2.

---

## 19. Live package smoke

Проверить:

```text
GET /avito/extension = 200
download 0.1.2 = 200
manifest version = 0.1.2
popup contains pairing form elements
```

---

## 20. Не заставлять owner переустанавливать без инструкции

После R8-R3 owner guide:

```text
1. Скачать 0.1.2.
2. Распаковать в новую папку.
3. chrome://extensions.
4. Удалить старую 0.1.1
   ИЛИ загрузить новую папку как обновлённую dev build.
5. Проверить Version 0.1.2.
```

Для надёжности на owner probe предпочтительно удалить старую dev extension и загрузить новую папку.

---

## 21. Regression suites

Обязательно:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
docker compose exec -T inventory-sales-module pytest
docker compose exec -T avito-module pytest
docker compose exec -T repairs-module pytest
pytest admin-shell/tests
pytest chrome-extension/technoreboot-avito/tests
```

---

## 22. Security

Сохранить:

```text
cookies permission = absent
debugger permission = absent
proxy permission = absent
Avito cookies never transferred
passwords never transferred
extension token never logged
```

---

## 23. Documentation

Обновить:

```text
chrome-extension/technoreboot-avito/README.md
docs/stage06a_r8_chrome_extension_avito_bridge.md
reports/stage06a_r8_chrome_extension_avito_bridge_report.md
logs/2026-08-12.md
```

---

## 24. Git

Expected HEAD:

```text
42ea7ed
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
git commit -m "Fix Avito extension pairing UI"
git push origin main
```

---

## 25. Definition of Done

Готово только если:

```text
server reachable state separated from paired state;
unpaired popup always shows 6-digit input;
unpaired popup shows Подключить button;
transfer button disabled until paired;
invalid/expired token returns to pairing form;
pair success stores token;
heartbeat validates token;
paired state visible;
version 0.1.2 packaged;
live ZIP valid;
all regression tests PASS;
commit pushed;
git clean.
```

---

## 26. Owner check after R8-R3

Owner делает:

```text
1. Скачать extension 0.1.2.
2. Установить новую version.
3. Открыть любое своё объявление Avito.
4. Открыть popup.
5. Убедиться:
   «Сервер Техноребут доступен».
6. Убедиться, что видно поле 6-значного кода.
7. В Technoreboot создать code.
8. Ввести code в popup.
9. Нажать «Подключить».
10. Убедиться:
    «Расширение привязано».
11. Убедиться, что кнопка
    «Передать объявление в Техноребут»
    стала активной.
```

После этого STOP.

Не нажимать передачу объявления до owner confirmation pairing.

---

## 27. Final status

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE06A_R8_R3_PAIRING_UI_READY_FOR_OWNER_CHECK

OWNER_PAIRING_CHECK_REQUIRED: true
OWNER_ONE_ITEM_EXTENSION_PROBE_NOT_YET_ACCEPTED: true
FULL_ACCOUNT_IMPORT_NOT_YET_AUTHORIZED: true
DO_NOT_START_STAGE06A_R9_WITHOUT_OWNER_ACCEPTANCE: true
DO_NOT_START_STAGE06B_REVERSE_SYNC_WITHOUT_OWNER_ACCEPTANCE: true
```
