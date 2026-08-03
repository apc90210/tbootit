# PROMPT — Техноребут / Stage04J-R1 Per-Product Cart Link

## Роль

Ты senior fullstack developer, FastAPI/Jinja2 engineer, UX-разработчик и release QA проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Нужно выполнить точечную UX-доработку уже реализованного Stage04J.

Новый функциональный этап не начинать.

---

# 1. Уточнение владельца

Текущая общая кнопка наверху:

```text
Перейти в корзину (N)
```

может остаться.

Дополнительно требуется:

```text
Рядом с каждым конкретным товаром,
который уже добавлен в корзину,
показывать кнопку «Перейти в корзину».
```

Для товара, которого нет в корзине:

```text
локальной кнопки «Перейти в корзину» быть не должно.
```

---

# 2. Целевой UX

На странице:

```text
http://localhost:8030/products
```

Для товара вне корзины:

```text
[В корзину]
```

После добавления этого товара:

```text
[В корзину] [Перейти в корзину]
```

Допустимый улучшенный вариант:

```text
[Добавить ещё] [Перейти в корзину]
В корзине: 1
```

Но нельзя ломать существующую бизнес-логику quantity.

Для уникального товара с максимальным количеством 1 допустимо:

```text
[Добавлено] [Перейти в корзину]
```

При этом кнопка «Добавлено» может быть disabled.

Главное требование:

```text
локальная кнопка «Перейти в корзину»
появляется только рядом с тем товаром,
который уже есть в session cart.
```

---

# 3. Общая верхняя кнопка

Сохранить текущую кнопку наверху:

```text
Перейти в корзину (N)
```

Правила прежние:

```text
показывается, если cart_items_count > 0;
скрыта, если корзина пуста;
показывает суммарное количество единиц.
```

---

# 4. Поведение после quick add

После успешного AJAX-добавления товара:

```text
страница не перезагружается;
URL не меняется;
scroll position сохраняется;
общий счётчик наверху обновляется;
рядом именно с добавленным товаром появляется
локальная кнопка «Перейти в корзину».
```

Локальная кнопка:

```text
href="/cart"
```

---

# 5. Поведение после reload

После обычной перезагрузки `/products`:

```text
сервер должен определить product IDs,
которые находятся в session cart;
для каждого такого товара
отрисовать локальную кнопку «Перейти в корзину».
```

Нельзя полагаться только на состояние JavaScript.

---

# 6. Состояние товара в корзине

В контекст шаблона передавать:

```text
cart_product_ids
```

или:

```text
cart_quantities_by_product_id
```

Предпочтительно:

```python
cart_quantities_by_product_id = {
    46: 1,
    47: 2
}
```

Это позволит показывать:

```text
В корзине: 1
В корзине: 2
```

---

# 7. Поведение при повторном добавлении

Если товар уже в корзине и допустимо увеличение quantity:

```text
quantity увеличивается;
локальный текст «В корзине: N» обновляется;
общий счётчик наверху обновляется;
локальная кнопка «Перейти в корзину» остаётся.
```

Если товар уникальный и больше добавить нельзя:

```text
не создавать дубликат;
показать русское сообщение;
локальная кнопка «Перейти в корзину» остаётся;
общий счётчик не меняется.
```

---

# 8. Поведение после очистки корзины

После успешного checkout:

```text
session cart очищается.
```

При возврате на `/products`:

```text
общая верхняя кнопка отсутствует;
локальные кнопки рядом с товарами отсутствуют;
надписи «В корзине: N» отсутствуют.
```

---

# 9. Product detail

На странице:

```text
/products/{id}
```

применить то же правило:

```text
если товар уже в корзине —
показывать рядом локальную кнопку «Перейти в корзину».
```

После quick add кнопка должна появиться без reload.

---

# 10. Архитектура

Сохранить:

```text
session-based cart;
Inventory без прямого доступа к Core DB;
Core остаётся источником истины о товаре;
quick add работает через HTTP endpoint;
общая верхняя кнопка остаётся.
```

---

# 11. Запреты

Запрещено:

```text
убирать верхнюю кнопку;
показывать локальную кнопку у всех товаров;
показывать локальную кнопку при пустой корзине;
ломать quick add;
ломать checkout;
ломать scanner;
использовать direct DB access;
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

---

# 12. Prompt discovery

Найти только:

```text
TECHNOREBOOT_STAGE04J_R1_PER_PRODUCT_CART_LINK_PROMPT.md
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
  C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE04J_R1_PER_PRODUCT_CART_LINK_PROMPT.md `
  C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE04J_R1_PER_PRODUCT_CART_LINK_PROMPT.md `
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

# 13. Preflight

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

Ожидаемый исходный HEAD:

```text
bbd3e90
```

---

# 14. Аудит текущей реализации

Проверить:

```text
inventory-sales-module/app/routers/products.py
inventory-sales-module/app/routers/cart.py
inventory-sales-module/app/templates/products.html
inventory-sales-module/app/templates/product_detail.html
inventory-sales-module/app/templates/base.html
inventory-sales-module/app/static/cart_quick_add.js
inventory-sales-module/tests/test_cart_quick_add.py
inventory-sales-module/tests/test_products_quick_cart_ui.py
```

Зафиксировать:

```text
как session cart передаётся в templates;
как обновляется верхний cart counter;
как определяется product_id после AJAX success.
```

---

# 15. Серверный template context

Для `/products` и `/products/{id}` добавить:

```text
cart_product_ids
cart_quantities_by_product_id
```

Пример:

```python
cart = request.session.get("cart", [])
cart_quantities_by_product_id = {
    int(item["product_id"]): int(item.get("quantity", 1))
    for item in cart
}
```

Учесть реальную структуру cart проекта.

Не допускать KeyError для старых session cart entries.

---

# 16. HTML-разметка товара

У каждого товара создать отдельный контейнер действий:

```html
<div class="product-cart-actions" data-product-id="{{ product.id }}">
    <form class="quick-add-form">...</form>

    <a
        class="product-go-to-cart"
        href="/cart"
        {% if product.id not in cart_product_ids %}hidden{% endif %}
    >
        Перейти в корзину
    </a>

    <span
        class="product-cart-quantity"
        {% if product.id not in cart_product_ids %}hidden{% endif %}
    >
        В корзине:
        <span class="product-cart-quantity-value">
            {{ cart_quantities_by_product_id.get(product.id, 0) }}
        </span>
    </span>
</div>
```

Допустима эквивалентная разметка.

---

# 17. JavaScript update

После успешного `POST /cart/add-quick` response должен содержать:

```json
{
  "product_id": 46,
  "product_quantity_in_cart": 1,
  "cart_items_count": 3
}
```

JavaScript должен:

```text
найти контейнер только этого product_id;
показать локальную кнопку;
обновить локальное quantity;
обновить верхний общий counter;
не трогать другие товары.
```

---

# 18. Несколько карточек одного product ID

Если один product ID по ошибке/дизайну присутствует в DOM несколько раз:

```text
обновить все контейнеры с data-product-id;
не падать;
не создавать duplicate IDs в HTML.
```

Использовать classes + data attributes.

---

# 19. Error behavior

При ошибке quick add:

```text
локальная кнопка не появляется;
quantity не меняется;
верхний counter не меняется;
показывается русская ошибка.
```

---

# 20. Accessibility

Локальная кнопка:

```text
доступна клавиатурой;
имеет понятный текст;
не использует только цвет как признак;
появление quantity можно поместить в aria-live.
```

---

# 21. Inventory tests — server rendering

Обновить/создать:

```text
inventory-sales-module/tests/test_product_cart_membership_ui.py
```

Покрыть:

```text
1. Пустая корзина — локальных кнопок нет.
2. Один товар в корзине — кнопка только у него.
3. Второй товар не в корзине — кнопки у него нет.
4. Quantity отображается правильно.
5. Верхняя общая кнопка остаётся.
6. Product detail показывает кнопку, если товар в корзине.
7. Product detail не показывает кнопку, если товара нет.
8. После checkout локальные кнопки отсутствуют.
```

---

# 22. Inventory tests — JavaScript

Покрыть:

```text
1. После success показывается кнопка только у product_id.
2. Локальный quantity обновляется.
3. Верхний counter обновляется.
4. Другие товары не изменяются.
5. При error кнопка не появляется.
6. При повторном add quantity меняется корректно.
7. Используются data-product-id, а не duplicate id.
```

---

# 23. Regression tests

Не сломать:

```text
quick add без reload;
верхнюю кнопку;
products filters;
pagination;
scroll preservation;
product detail;
cart page;
checkout;
scanner;
cancel;
reissue;
reports;
receipts.
```

---

# 24. Docker rebuild

```powershell
docker compose up --build -d --force-recreate inventory-sales-module
docker compose up -d core avito-module
docker compose ps
```

---

# 25. Полные тесты

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
docker compose exec -T inventory-sales-module pytest
docker compose exec -T avito-module pytest
```

Проверить, что live DB не изменилась от tests.

---

# 26. Runtime owner flow

## Сценарий A — пустая корзина

Открыть `/products`.

Ожидаемо:

```text
верхней кнопки нет;
локальных кнопок нет.
```

## Сценарий B — первый товар

Нажать «В корзину» у товара A.

Ожидаемо:

```text
страница остаётся;
верхняя кнопка появляется;
рядом с товаром A появляется «Перейти в корзину»;
рядом с другими товарами кнопки нет;
показывается «В корзине: 1».
```

## Сценарий C — второй товар

Добавить товар B.

Ожидаемо:

```text
у A кнопка остаётся;
у B появляется кнопка;
верхний счётчик увеличивается;
оба локальных quantity корректны.
```

## Сценарий D — reload

Перезагрузить `/products`.

Ожидаемо:

```text
локальные кнопки у A и B сохраняются;
верхняя кнопка сохраняется;
quantity сохраняются.
```

## Сценарий E — checkout

Перейти в `/cart`, оформить продажу, вернуться в `/products`.

Ожидаемо:

```text
верхней кнопки нет;
локальных кнопок нет;
quantity labels нет.
```

---

# 27. Safety scans

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

# 28. Документация

Создать:

```text
docs/stage04j_r1_per_product_cart_link.md
reports/stage04j_r1_per_product_cart_link_report.md
```

Обновить:

```text
logs/2026-08-03.md
```

Report:

```text
# Stage04J-R1 Per-Product Cart Link Report

## STATUS
## OWNER_CLARIFICATION
## PREVIOUS_BEHAVIOR
## NEW_BEHAVIOR
## TEMPLATE_CONTEXT
## LOCAL_CART_BUTTON
## JAVASCRIPT_UPDATE
## QUANTITY_DISPLAY
## ERROR_HANDLING
## TESTS
## LIVE_DB_PRESERVATION
## RUNTIME_EMPTY_CART
## RUNTIME_FIRST_ADD
## RUNTIME_SECOND_ADD
## RUNTIME_RELOAD
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

# 29. Git

Только targeted add.

Возможные файлы:

```powershell
git add inventory-sales-module/app/routers/products.py
git add inventory-sales-module/app/templates/products.html
git add inventory-sales-module/app/templates/product_detail.html
git add inventory-sales-module/app/static/cart_quick_add.js
git add inventory-sales-module/tests/test_product_cart_membership_ui.py
git add inventory-sales-module/tests/test_products_quick_cart_ui.py

git add docs/stage04j_r1_per_product_cart_link.md
git add reports/stage04j_r1_per_product_cart_link_report.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04J_R1_PER_PRODUCT_CART_LINK_PROMPT.md
git add -f logs/2026-08-03.md
```

Коммит:

```powershell
git commit -m "Show cart link beside added products"
git push origin main
```

После:

```powershell
git status --short --untracked-files=all
git rev-parse HEAD
git log --oneline -5
```

---

# 30. Definition of Done

```text
верхняя общая кнопка сохранена;
локальная кнопка показывается только у товаров в корзине;
после AJAX add локальная кнопка появляется сразу;
после reload локальная кнопка сохраняется;
quantity отображается корректно;
другие товары не меняются;
при ошибке кнопка не появляется;
после checkout все локальные кнопки исчезают;
product detail поддержан;
quick add без reload работает;
filters/scroll сохраняются;
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

# 31. Финальный статус

Успех:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04J_R1_PER_PRODUCT_CART_LINK_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

Проблема:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04J_R1_PER_PRODUCT_CART_LINK_FAIL

BLOCKERS:
...
```
