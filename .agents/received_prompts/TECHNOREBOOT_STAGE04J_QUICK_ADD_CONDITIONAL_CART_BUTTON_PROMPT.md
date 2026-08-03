# PROMPT — Техноребут / Stage04J Quick Add to Cart Without Redirect

## Роль

Ты senior fullstack developer, FastAPI/Jinja2 engineer, UX-разработчик, специалист по корзине и тестированию проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Нужно изменить UX добавления товаров в корзину.

---

# 1. Решение владельца

Stage04I принят владельцем:

```text
TECHNOREBOOT_STAGE04I_OWNER_ACCEPTED
```

Новая задача:

```text
При нажатии «В корзину» товар добавляется,
но страница списка товаров не открывает корзину.

Пользователь остаётся на текущем месте списка,
может быстро добавить несколько товаров подряд.

Когда корзина не пуста, рядом со списком товаров
появляется кнопка «Перейти в корзину».

Когда корзина пуста, этой кнопки нет.
```

---

# 2. Название этапа

```text
TECHNOREBOOT_STAGE04J_QUICK_ADD_CONDITIONAL_CART_BUTTON
```

Целевой статус:

```text
TECHNOREBOOT_STAGE04J_QUICK_ADD_CONDITIONAL_CART_BUTTON_READY_FOR_OWNER_CHECK
```

Gate:

```text
OWNER_MANUAL_CHECK_REQUIRED: true
OWNER_ACCEPTANCE_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 3. Основной пользовательский сценарий

На странице:

```text
http://localhost:8030/products
```

Пользователь нажимает:

```text
В корзину
```

Ожидаемо:

```text
товар добавляется в session cart;
страница не переходит на /cart;
фильтры не сбрасываются;
поисковый запрос не сбрасывается;
страница пагинации не сбрасывается;
позиция прокрутки сохраняется;
рядом со списком появляется кнопка «Перейти в корзину»;
кнопка показывает количество товаров в корзине;
можно добавить следующий товар.
```

---

# 4. Поведение условной кнопки

Кнопка:

```text
Перейти в корзину
```

Отображается только при условии:

```text
cart_items_count > 0
```

Когда корзина пуста:

```text
кнопка отсутствует в HTML или скрыта;
пустой badge не показывается;
«0 товаров» не показывается.
```

Когда в корзине есть товары:

```text
Перейти в корзину · 1
Перейти в корзину · 2
Перейти в корзину · 3
```

Допустимый русский вариант:

```text
Перейти в корзину (3)
```

Разместить кнопку рядом с заголовком/панелью списка товаров так, чтобы она была заметна и не перекрывала фильтры.

Предпочтительно:

```text
справа от заголовка «Товары»;
либо в верхней панели над списком;
на мобильной ширине — отдельной строкой.
```

---

# 5. UX добавления

После успешного добавления:

```text
не выполнять redirect на /cart;
не выполнять полную перезагрузку страницы;
не менять URL;
не сбрасывать scroll position.
```

На самой кнопке товара кратко показать подтверждение:

```text
Добавлено
```

Через короткое время вернуть текст:

```text
В корзину
```

Дополнительно разрешён небольшой русский toast:

```text
Товар добавлен в корзину
```

Но toast не должен мешать добавлять следующие товары.

---

# 6. Ошибки

При ошибке:

```text
reserved;
sold;
draft;
quantity=0;
wrong storage_location;
Core unavailable;
unknown product;
network error.
```

Ожидаемо:

```text
пользователь остаётся на странице товаров;
корзина не открывается;
показывается понятное русское сообщение;
cart counter не увеличивается;
кнопка не показывает ложное «Добавлено».
```

Не показывать пользователю необработанный JSON/Pydantic response.

---

# 7. Архитектура

Сохранить модульность:

```text
inventory-sales-module не обращается напрямую к Core DB;
все сведения о товаре получает через Core HTTP API;
корзина остаётся session-based;
Core остаётся источником истины о товаре, статусе, цене и остатке.
```

---

# 8. Запреты

Запрещено:

```text
начинать следующий этап;
ломать обычную страницу /cart;
ломать barcode scanner;
дублировать товар неконтролируемо;
хранить корзину в Core DB;
использовать direct DB access из Inventory;
использовать drop_all;
использовать DROP TABLE;
использовать DELETE FROM;
запускать небезопасный core pytest;
git add .;
git add -A;
git add -u;
git reset;
git clean;
git rebase;
git commit --amend;
force push;
коммитить DB/temp/cache.
```

Core tests запускать только:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
```

---

# 9. Prompt discovery

Найти только:

```text
TECHNOREBOOT_STAGE04J_QUICK_ADD_CONDITIONAL_CART_BUTTON_PROMPT.md
```

Искать:

```text
C:\Users\Apc\Downloads
C:\tbootit\.agents\received_prompts
C:\tbootit
```

Если найден в Downloads:

```powershell
Copy-Item `
  C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE04J_QUICK_ADD_CONDITIONAL_CART_BUTTON_PROMPT.md `
  C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE04J_QUICK_ADD_CONDITIONAL_CART_BUTTON_PROMPT.md `
  -Force
```

В отчёте:

```text
PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:
PROMPT_SHA256:
```

---

# 10. Preflight

```powershell
Set-Location C:\tbootit

git status --short --untracked-files=all
git branch --show-current
git rev-parse HEAD
git log --oneline -15
git diff --name-status
git diff --stat
docker compose ps
```

Ожидаемый исходный HEAD:

```text
39d0ce8
```

Если фактический HEAD другой — указать.

---

# 11. Аудит текущего cart add flow

Проверить:

```text
inventory-sales-module/app/routers/cart.py
inventory-sales-module/app/templates/products.html
inventory-sales-module/app/templates/product_detail.html
inventory-sales-module/app/templates/base.html
inventory-sales-module/app/static/*
inventory-sales-module/tests/*
```

Зафиксировать текущий flow:

```text
HTML form action;
method;
response;
redirect target;
session cart structure;
cart count calculation.
```

---

# 12. Новый HTTP-контракт quick add

Предпочтительно использовать отдельный JSON endpoint:

```text
POST /cart/add-quick
```

или сохранить:

```text
POST /cart/add
```

с определением AJAX-запроса.

Рекомендуемый ответ:

```json
{
  "ok": true,
  "message": "Товар добавлен в корзину",
  "cart_items_count": 3,
  "cart_lines_count": 2,
  "product_id": 46,
  "product_quantity_in_cart": 1
}
```

При ошибке:

```json
{
  "ok": false,
  "message": "Товар недоступен для продажи",
  "cart_items_count": 2
}
```

Статусы:

```text
200 — успешно;
400 — некорректный запрос;
404 — товар не найден;
409 — товар нельзя добавить;
502/503 — Core недоступен.
```

Не отдавать HTML redirect для AJAX success.

---

# 13. Progressive enhancement

Обычная форма должна оставаться работоспособной без JavaScript.

Без JS допустимо:

```text
POST /cart/add;
redirect обратно на исходную products URL;
не переходить в /cart.
```

Для этого передавать:

```text
return_url
```

или использовать безопасный referer только после валидации локального пути.

Запрещён open redirect.

Разрешённые return_url:

```text
/products
/products?...filters...
/products/{id}
```

---

# 14. Сохранение состояния списка

При quick add должны сохраняться:

```text
search query;
category filter;
brand/model filters;
status filter;
location filter;
pagination;
sort;
scroll position.
```

При JS flow это достигается отсутствием navigation.

При fallback flow redirect должен возвращать на исходный локальный URL.

---

# 15. Подсчёт корзины

Определить два значения:

```text
cart_lines_count — число разных строк;
cart_items_count — суммарное количество единиц.
```

В кнопке использовать:

```text
cart_items_count
```

Пример:

```text
2 строки:
товар A quantity=2
товар B quantity=1

Кнопка:
Перейти в корзину (3)
```

Если проект считает уникальные б/у товары только по одной единице, значение всё равно должно вычисляться из session cart.

---

# 16. Уникальные и количественные товары

Сохранить существующую бизнес-логику:

```text
уникальный товар нельзя добавить сверх доступного количества;
повторное добавление не создаёт неконтролируемые дубликаты;
для количественного товара quantity увеличивается до доступного остатка;
при превышении остатка показывается русская ошибка.
```

После повторного добавления counter должен обновиться корректно.

---

# 17. Кнопка «Перейти в корзину»

В шаблоне списка товаров предусмотреть контейнер:

```html
<a id="go-to-cart-button" href="/cart">Перейти в корзину (<span>3</span>)</a>
```

Поведение:

```text
если cart_items_count == 0 — hidden/не отрисовывать;
после первого quick add — показать;
после следующих add — обновлять count;
если корзина очищена в другой вкладке, после reload состояние корректно;
на /products после checkout кнопка отсутствует.
```

---

# 18. Доступность

Кнопки должны:

```text
работать с клавиатуры;
иметь type="submit";
не блокировать Enter/Space;
иметь aria-live для сообщения и счётчика;
во время запроса быть временно disabled;
не отправлять один запрос дважды при двойном клике.
```

---

# 19. Защита от двойного клика

При нажатии:

```text
сразу disabled;
показывать «Добавляем...»;
после ответа вернуть рабочее состояние.
```

Один физический клик не должен создавать два cart increment.

Добавить тест на двойную отправку или UI-lock.

---

# 20. Scanner flow

Не менять основную логику barcode scanner.

Проверить:

```text
/cart/scan по-прежнему добавляет товар;
reserved/sold/draft/zero/wrong-location блокируются;
scanner autofocus сохраняется;
checkout работает.
```

Scanner может оставаться на странице `/cart`.

---

# 21. Product detail

На странице товара:

```text
/products/{id}
```

желательно применить такое же поведение:

```text
«В корзину» добавляет без перехода;
появляется «Перейти в корзину».
```

Если это значительно расширяет scope, минимум не сломать текущий detail flow и явно указать, что quick add реализован только в списке.

Предпочтительно сделать одинаково в списке и карточке.

---

# 22. Inventory tests — endpoint

Создать:

```text
inventory-sales-module/tests/test_cart_quick_add.py
```

Покрыть:

```text
1. Успешный quick add возвращает JSON.
2. Нет redirect на /cart.
3. cart_items_count корректен.
4. cart_lines_count корректен.
5. Цена берётся из Core.
6. Название берётся из Core.
7. Первый товар создаёт корзину.
8. Повторное добавление обновляет quantity согласно правилам.
9. Превышение остатка блокируется.
10. reserved блокируется.
11. sold блокируется.
12. draft блокируется.
13. quantity=0 блокируется.
14. wrong location блокируется.
15. unknown product возвращает русскую ошибку.
16. Core unavailable возвращает понятную ошибку.
17. session cart не меняется при ошибке.
```

---

# 23. Inventory tests — products UI

Создать:

```text
inventory-sales-module/tests/test_products_quick_cart_ui.py
```

Покрыть:

```text
1. При пустой корзине кнопки «Перейти в корзину» нет.
2. При непустой корзине кнопка есть.
3. В кнопке правильный count.
4. Product form имеет quick-add hook.
5. JavaScript перехватывает submit.
6. JS не меняет window.location.
7. После успеха показывает кнопку.
8. После следующего add обновляет count.
9. При ошибке count не меняется.
10. Кнопка товара временно disabled.
11. Есть aria-live.
12. Фильтры и query string остаются на месте.
13. Есть безопасный fallback без JS.
```

---

# 24. Regression tests

Не сломать:

```text
cart page;
checkout;
SBP;
warranty;
no warranty;
cancel;
reissue;
reports;
barcode scanner;
price tags;
sales filters;
receipts.
```

---

# 25. Docker rebuild

```powershell
docker compose up --build -d --force-recreate inventory-sales-module
docker compose up -d core avito-module
docker compose ps
```

---

# 26. Полные тесты

Core safe:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
```

Inventory:

```powershell
docker compose exec -T inventory-sales-module pytest
```

Avito:

```powershell
docker compose exec -T avito-module pytest
```

Проверить, что safe tests не изменяют live DB.

---

# 27. Runtime owner flow

Открыть:

```text
http://localhost:8030/products
```

## Сценарий A — пустая корзина

Зафиксировать:

```text
корзина пуста;
кнопки «Перейти в корзину» нет.
```

Нажать «В корзину» на товаре A.

Ожидаемо:

```text
URL не изменился;
страница не перезагрузилась;
scroll position сохранилась;
товар A добавлен;
кнопка «Перейти в корзину (1)» появилась.
```

## Сценарий B — второй товар

Нажать «В корзину» на товаре B.

Ожидаемо:

```text
URL не изменился;
кнопка стала «Перейти в корзину (2)»;
товары A и B присутствуют в cart.
```

## Сценарий C — фильтры

Применить фильтр/поиск, перейти ниже по списку, добавить товар.

Ожидаемо:

```text
фильтр не сброшен;
query string не изменён;
scroll position не сброшена;
cart count обновлён.
```

## Сценарий D — ошибка

Попытаться добавить недоступный товар.

Ожидаемо:

```text
страница остаётся;
русская ошибка;
cart count не меняется.
```

## Сценарий E — переход

Нажать:

```text
Перейти в корзину
```

Ожидаемо:

```text
открывается /cart;
в корзине все добавленные товары;
цены корректны.
```

---

# 28. Runtime checkout regression

После набора товаров:

```text
оформить продажу;
убедиться, что cart очищена;
вернуться на /products;
кнопки «Перейти в корзину» нет.
```

---

# 29. Safety scans

```powershell
git grep -n -I "drop_all\|DROP TABLE\|DELETE FROM" -- core/app core/tests inventory-sales-module/app inventory-sales-module/tests
```

```powershell
git ls-files | Select-String -Pattern "tbootit\.db|technoreboot\.db|\.sqlite|\.sqlite3|data/db|__pycache__|\.pytest_cache"
```

```powershell
git grep -n -I "create_engine\|SessionLocal\|sqlite\|technoreboot.db\|data/db\|sqlalchemy\|SELECT .* FROM\|INSERT INTO" -- inventory-sales-module
```

```powershell
git ls-files | Select-String -Pattern "\.env$|id_rsa|id_ed25519|private_key|\.pem|\.p12|\.pfx"
```

---

# 30. Документация

Создать:

```text
docs/stage04j_quick_add_conditional_cart_button.md
reports/stage04j_quick_add_conditional_cart_button_report.md
```

Обновить:

```text
logs/2026-08-03.md
```

Report:

```text
# Stage04J Quick Add and Conditional Cart Button Report

## STATUS
## OWNER_REQUIREMENT
## PREVIOUS_FLOW
## NEW_FLOW
## QUICK_ADD_ENDPOINT
## SESSION_CART_COUNTS
## CONDITIONAL_CART_BUTTON
## ERROR_HANDLING
## ACCESSIBILITY
## FALLBACK_WITHOUT_JS
## TESTS
## LIVE_DB_PRESERVATION
## RUNTIME_EMPTY_CART
## RUNTIME_FIRST_ADD
## RUNTIME_SECOND_ADD
## RUNTIME_FILTER_PRESERVATION
## RUNTIME_ERROR
## RUNTIME_CHECKOUT
## SAFETY_SCAN
## FILES_CHANGED
## COMMIT
## PUSH
## FINAL_GIT_STATUS
## OWNER_CHECK_GUIDE
## FINAL_STATUS
```

---

# 31. Git

Только targeted add.

Возможные файлы:

```powershell
git add inventory-sales-module/app/routers/cart.py
git add inventory-sales-module/app/routers/products.py
git add inventory-sales-module/app/templates/products.html
git add inventory-sales-module/app/templates/product_detail.html
git add inventory-sales-module/app/static/cart_quick_add.js
git add inventory-sales-module/app/static/styles.css
git add inventory-sales-module/tests/test_cart_quick_add.py
git add inventory-sales-module/tests/test_products_quick_cart_ui.py

git add docs/stage04j_quick_add_conditional_cart_button.md
git add reports/stage04j_quick_add_conditional_cart_button_report.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04J_QUICK_ADD_CONDITIONAL_CART_BUTTON_PROMPT.md
git add -f logs/2026-08-03.md
```

Не добавлять несуществующие файлы.

Коммит:

```powershell
git commit -m "Add quick cart actions to product list"
git push origin main
```

После:

```powershell
git status --short --untracked-files=all
git rev-parse HEAD
git log --oneline -5
```

---

# 32. Definition of Done

```text
нажатие «В корзину» не открывает корзину;
страница products не перезагружается;
URL и фильтры сохраняются;
scroll position сохраняется;
товар реально появляется в session cart;
после первого добавления появляется «Перейти в корзину»;
кнопка показывает суммарное количество;
при пустой корзине кнопки нет;
после checkout кнопка исчезает;
несколько товаров добавляются подряд;
ошибки показываются по-русски;
count не меняется при ошибке;
двойной клик защищён;
fallback без JavaScript безопасен;
cart page работает;
scanner работает;
checkout работает;
cancel/reissue/reports не сломаны;
Core safe tests PASS;
Inventory tests PASS;
Avito tests PASS;
live DB не меняется от tests;
safety scans clean;
targeted commit;
push;
clean Git;
owner manual check required.
```

---

# 33. Финальный статус

Успех:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04J_QUICK_ADD_CONDITIONAL_CART_BUTTON_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

Проблема:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04J_QUICK_ADD_CONDITIONAL_CART_BUTTON_FAIL

BLOCKERS:
...
```
