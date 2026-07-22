# PROMPT — Техноребут / Stage 04E-R3 Sales Quantity Warranty Receipt & Product Print Actions UX Update

## Роль агента

Ты senior fullstack developer, UX/business-flow analyst, FastAPI/Jinja2 engineer и постановщик корректной торговой логики проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Твоя задача — выполнить Stage 04E-R3: доработать текущий `inventory-sales-module` по новым owner-требованиям к продаже, гарантии, товарному чеку и печати ценника как действию у товара.

Это repair/UX/business-flow update внутри Stage04E, а не отдельный Stage04F.

---

# 1. Причина этапа

Владелец уточнил требования:

```text
ценники - это не отдельный пункт, это просто кнопка на товаре в наличии,
при нажатии которого выскакивает форма отправки на печать принтера
в соответствии с формой, которую я позже вышлю,

при продаже нужно предусмотреть возможность указать цену ручками,
а так же количество товара.

так же при продаже должна кнопка товарный чек,
при нажатии на которую на печать отправляется форма гарантийного-товарного чека,
форму которого я скину чуть позже.

так же при продаже есть цифра гарантии в днях,
по умолчанию 30 дней, но можно изменить или убрать совсем через чек бокс
(тогда в гарантийном товаре появляется упоминание,
что товар продается без гарантии, в том состоянии в котором есть,
и покупатель внимательно осмотрел товар при покупке)
```

---

# 2. Главный статус

Текущий статус:

```text
STAGE04E_R2_READY_FOR_OWNER_RECHECK
```

Но появились новые owner-требования, поэтому Stage04E пока не финально принят.

Целевой статус этого этапа:

```text
TECHNOREBOOT_STAGE04E_R3_SALES_WARRANTY_RECEIPT_PRINT_ACTIONS_READY_FOR_OWNER_RECHECK
```

После выполнения нельзя переходить к следующему этапу без владельца.

Gate:

```text
OWNER_MANUAL_CHECK_REQUIRED: true
OWNER_ACCEPTANCE_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 3. Важное изменение Roadmap/UI

Раньше в UI был пункт:

```text
Ценники — скоро
```

Теперь это неправильно.

Новая логика:

```text
Ценники не являются отдельным разделом.
Печать ценника — это действие у конкретного товара в наличии.
```

Нужно убрать отдельный пункт меню/раздел:

```text
Ценники — скоро
```

И заменить на действия:

```text
в списке товаров: кнопка "Печать ценника" для товара в наличии
в карточке товара: кнопка "Печать ценника" для товара в наличии
```

Если товар нельзя продавать/нет в наличии:

```text
кнопка "Печать ценника" disabled или не показывается
```

---

# 4. Архитектурные правила

`inventory-sales-module` работает только через Core API.

Разрешено:

```text
inventory-sales-module → Core API → Core DB
```

Запрещено:

```text
inventory-sales-module → Core DB напрямую
```

Нельзя:

```text
добавлять собственную БД inventory-sales-module
читать sqlite напрямую
использовать SQLAlchemy в inventory-sales-module
```

---

# 5. Что НЕ делать сейчас

Не делать финальные формы документов, пока владелец не пришлет шаблоны.

Не делать:

```text
финальный дизайн ценника
финальный дизайн гарантийно-товарного чека
PDF engine
сложную очередь печати
интеграцию с конкретным драйвером принтера
автоматический silent print без действия пользователя
отдельный раздел "Ценники"
Stage04F как отдельный этап
```

Можно сделать:

```text
print-preview страницы
кнопка "Печать"
window.print()
CSS @media print
placeholder layout с явной пометкой "Шаблон будет заменён после утверждения формы"
```

---

# 6. Functional requirements — форма продажи

Доработать форму:

```text
GET /sales/new?product_id=<id>
```

Форма должна содержать:

```text
товар
артикул
статус
цена по карточке
ручная цена продажи
количество
способ оплаты
гарантия в днях
чекбокс "Без гарантии"
примечание
кнопка "Подтвердить продажу"
```

## 6.1 Цена вручную

Текущее поле цены сохранить/переименовать в понятное:

```text
Цена продажи
```

Оператор может изменить цену вручную.

Validation:

```text
цена > 0
пустая цена недопустима
ошибка на русском
```

## 6.2 Количество товара

Добавить поле:

```text
Количество
```

Default:

```text
1
```

Validation MVP:

```text
quantity >= 1
quantity integer
```

Важная бизнес-оговорка:

```text
Текущая модель товаров может быть преимущественно штучной.
Если Core пока не поддерживает складские остатки quantity для одного product_id,
то для Stage04E-R3 разрешено:
- добавить поле quantity в UI и отправлять его в Core sales item;
- сохранить ограничение quantity=1 для штучных товаров, если Core отклоняет quantity>1;
- явно описать это в report как ограничение MVP.
```

Если Core уже поддерживает quantity > 1 — использовать.

Нельзя ломать текущую продажу quantity=1.

## 6.3 Гарантия

Добавить поле:

```text
Гарантия, дней
```

Default:

```text
30
```

Добавить checkbox:

```text
Без гарантии
```

UI behavior:

```text
если "Без гарантии" не отмечено:
  warranty_days enabled
  default 30
  можно изменить вручную

если "Без гарантии" отмечено:
  warranty_days disabled или ignored
  sale warranty mode = no_warranty
```

Validation:

```text
если warranty enabled: warranty_days >= 1
если no warranty: warranty_days null/0 допустимо
```

---

# 7. Core data/API requirements

Проверить текущую Core sales model.

Если Sales API уже поддерживает notes/items quantity/price — использовать.

Нужно добавить или подготовить поля для продажи:

```text
warranty_days
no_warranty / warranty_enabled
```

Варианты реализации:

## Preferred

В Core Sale добавить поля:

```text
warranty_days: Optional[int]
warranty_enabled: bool
```

или:

```text
warranty_days: Optional[int]
warranty_type: "warranty" | "no_warranty"
```

Для MVP можно использовать:

```text
warranty_days = 30 по умолчанию
warranty_days = null если без гарантии
```

Но лучше явно иметь boolean:

```text
warranty_enabled: true/false
```

## SaleCreate payload example

```json
{
  "customer_id": null,
  "payment_method": "cash",
  "notes": "....",
  "warranty_days": 30,
  "warranty_enabled": true,
  "items": [
    {
      "product_id": 1,
      "quantity": 1,
      "price": 25000
    }
  ]
}
```

No warranty:

```json
{
  "customer_id": null,
  "payment_method": "cash",
  "notes": "....",
  "warranty_days": null,
  "warranty_enabled": false,
  "items": [
    {
      "product_id": 1,
      "quantity": 1,
      "price": 25000
    }
  ]
}
```

Если Core требует migration/ad-hoc migration, сделать аккуратно по существующему стилю проекта.

---

# 8. Product price tag print action

Добавить action у товара:

```text
Печать ценника
```

Где:

```text
/products table row
/products/{id} detail page
```

Условие:

```text
только товар в наличии / reserved, если owner logic считает reserved допустимым
лучше MVP: только in_stock
```

Routes:

```text
GET /products/{product_id}/price-tag
POST /products/{product_id}/price-tag/print
```

или только preview:

```text
GET /products/{product_id}/price-tag
```

Для MVP достаточно print-preview page:

```text
товар
артикул
цена
производитель
модель
краткое описание
кнопка "Печать"
```

Template:

```text
inventory-sales-module/app/templates/price_tag_preview.html
```

Важно:

```text
форма ценника будет заменена после того, как владелец пришлет шаблон
```

На странице должна быть пометка:

```text
Предварительная форма ценника. Финальный шаблон будет подключен после утверждения.
```

Печать:

```html
<button onclick="window.print()">Печать</button>
```

CSS:

```text
@media print
```

---

# 9. Warranty/product receipt print action

После успешной продажи на странице:

```text
GET /sales/{sale_id}
```

Добавить кнопку:

```text
Товарный чек
```

Она ведет на:

```text
GET /sales/{sale_id}/receipt
```

Template:

```text
inventory-sales-module/app/templates/sale_receipt_preview.html
```

На странице:

```text
Гарантийно-товарный чек
номер продажи
дата
товар
количество
цена
сумма
способ оплаты
гарантия
кнопка "Печать"
```

Если гарантия включена:

```text
Гарантия: 30 дней
```

или выбранное число.

Если гарантия выключена:

```text
Товар продаётся без гарантии, в том состоянии, в котором есть.
Покупатель внимательно осмотрел товар при покупке.
```

Важно:

```text
финальная форма гарантийно-товарного чека будет заменена после того, как владелец пришлет шаблон
```

Показать пометку:

```text
Предварительная форма товарного чека. Финальный шаблон будет подключен после утверждения.
```

Печать:

```html
<button onclick="window.print()">Печать</button>
```

---

# 10. UI navigation cleanup

Убрать из главного меню:

```text
Ценники — скоро
```

Меню должно быть примерно:

```text
Главная
Товары
Продажи
```

Печать ценника доступна только из товара.

---

# 11. CoreClient changes

В `inventory-sales-module/app/core_client.py` добавить/проверить:

```text
create_sale(product_id, price, quantity, payment_method, notes, warranty_days, warranty_enabled)
get_sale(sale_id)
get_product(product_id)
get_product_details(product_id)
```

Если receipt needs sale detail but Core sale detail doesn't include product data, можно:

```text
получить sale
получить product по product_id из sale item
собрать view model на стороне inventory-sales-module
```

Но без прямой БД.

---

# 12. Schemas

Обновить:

```text
inventory-sales-module/app/schemas.py
core/app/schemas.py
```

Добавить:

```text
quantity
warranty_days
warranty_enabled
```

Где уместно.

---

# 13. Tests

Добавить/обновить tests.

Core tests:

```text
core/tests/test_sales_warranty.py
```

Покрыть:

```text
create sale default warranty_days=30 / warranty_enabled true
create sale with warranty_days custom
create sale no warranty
sale detail returns warranty fields
quantity is accepted in sale item if supported
```

Inventory tests:

```text
inventory-sales-module/tests/test_sales_warranty_ui.py
inventory-sales-module/tests/test_price_tag_print_action.py
inventory-sales-module/tests/test_receipt_print_action.py
inventory-sales-module/tests/test_navigation_no_price_tags_section.py
```

Покрыть:

```text
/sales/new shows quantity field
/sales/new shows warranty days default 30
/sales/new shows "Без гарантии" checkbox
POST /sales/create sends quantity
POST /sales/create sends warranty_days and warranty_enabled
/sales/{id} shows "Товарный чек"
/sales/{id}/receipt renders warranty text
/sales/{id}/receipt renders no warranty disclaimer
/products shows "Печать ценника" for in_stock product
/products/{id}/price-tag renders preview
main nav does not include "Ценники — скоро"
UI labels are Russian
```

Запустить:

```powershell
docker compose exec core pytest
docker compose exec inventory-sales-module pytest
docker compose exec avito-module pytest
```

---

# 14. Manual smoke

После реализации:

```powershell
docker compose up --build -d
docker compose ps
```

Проверить:

```powershell
Invoke-WebRequest http://127.0.0.1:8030/products | Select-Object StatusCode
```

Owner flow:

```text
1. Открыть /products.
2. Проверить, что в верхнем меню нет "Ценники — скоро".
3. Найти товар in_stock.
4. Убедиться, что у товара есть кнопка "Печать ценника".
5. Нажать "Печать ценника".
6. Открывается preview ценника с кнопкой "Печать".
7. Вернуться к товару.
8. Нажать "Продать".
9. На форме есть:
   - Цена продажи
   - Количество
   - Гарантия, дней = 30
   - Без гарантии
10. Продать с гарантией 30 дней.
11. На странице продажи есть кнопка "Товарный чек".
12. Открыть "Товарный чек".
13. Проверить текст "Гарантия: 30 дней".
14. Создать/выбрать другой товар.
15. Продать с чекбоксом "Без гарантии".
16. Открыть "Товарный чек".
17. Проверить текст:
    "Товар продаётся без гарантии, в том состоянии, в котором есть.
     Покупатель внимательно осмотрел товар при покупке."
```

---

# 15. Safety scans

Direct DB access:

```powershell
git grep -n -I "create_engine\|SessionLocal\|sqlite\|technoreboot.db\|data/db\|sqlalchemy\|SELECT .* FROM\|INSERT INTO" -- inventory-sales-module
```

Browser automation:

```powershell
git grep -n -I "selenium\|playwright\|webdriver\|undetected\|pyppeteer\|captcha solver\|captcha-solver\|bypass captcha\|обход капчи\|автологин\|auto login\|chromium" -- core admin-shell avito-module inventory-sales-module
```

Runtime data:

```powershell
git status --ignored --short --untracked-files=all -- data/db
git status --ignored --short --untracked-files=all -- data/avito-module
```

---

# 16. Documentation

Создать/обновить:

```text
docs/stage04e_r3_sales_warranty_receipt_print_actions.md
docs/inventory_sales_module_ui_map.md
docs/inventory_sales_module_core_api_contract.md
reports/stage04e_r3_sales_warranty_receipt_print_actions_report.md
logs/2026-07-02.md
```

Report structure:

```text
# Stage 04E-R3 Sales Warranty Receipt Print Actions Report

## STATUS

READY_FOR_OWNER_RECHECK / FAIL

## OWNER_REQUEST

## IMPLEMENTED

## UI_CHANGES

## CORE_API_CHANGES

## WARRANTY_LOGIC

## QUANTITY_LOGIC

## PRICE_TAG_ACTION

## RECEIPT_PRINT_ACTION

## TEMPLATES_PLACEHOLDER_NOTE

## TESTS

## MANUAL_SMOKE

## SAFETY_SCAN

## FILES_CHANGED

## OWNER_RECHECK_GUIDE

## FINAL_STATUS

TECHNOREBOOT_STAGE04E_R3_SALES_WARRANTY_RECEIPT_PRINT_ACTIONS_READY_FOR_OWNER_RECHECK
```

---

# 17. Git

Use targeted add only.

Possible files:

```powershell
git add core/app/models.py
git add core/app/schemas.py
git add core/app/routers/sales.py
git add core/tests/test_sales_warranty.py
git add inventory-sales-module/app/core_client.py
git add inventory-sales-module/app/schemas.py
git add inventory-sales-module/app/routers/products.py
git add inventory-sales-module/app/routers/sales.py
git add inventory-sales-module/app/main.py
git add inventory-sales-module/app/templates/base.html
git add inventory-sales-module/app/templates/products.html
git add inventory-sales-module/app/templates/product_detail.html
git add inventory-sales-module/app/templates/sales_new.html
git add inventory-sales-module/app/templates/sales_detail.html
git add inventory-sales-module/app/templates/price_tag_preview.html
git add inventory-sales-module/app/templates/sale_receipt_preview.html
git add inventory-sales-module/app/static/app.css
git add inventory-sales-module/tests/test_sales_warranty_ui.py
git add inventory-sales-module/tests/test_price_tag_print_action.py
git add inventory-sales-module/tests/test_receipt_print_action.py
git add inventory-sales-module/tests/test_navigation_no_price_tags_section.py
git add docs/stage04e_r3_sales_warranty_receipt_print_actions.md
git add docs/inventory_sales_module_ui_map.md
git add docs/inventory_sales_module_core_api_contract.md
git add reports/stage04e_r3_sales_warranty_receipt_print_actions_report.md
git add logs/2026-07-02.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04E_R3_SALES_WARRANTY_RECEIPT_PRINT_ACTIONS_PROMPT.md

git commit -m "Add sales warranty receipt and product print actions"
git status --short --untracked-files=all
```

Strictly forbidden:

```text
git add .
git add -u
git commit --amend
```

If log needs update after commit:

```text
create a separate normal commit
```

---

# 18. Definition of Done

Готово, если:

```text
отдельный пункт "Ценники — скоро" убран из меню
у товара in_stock есть кнопка "Печать ценника"
price tag preview открывается
форма продажи содержит ручную цену
форма продажи содержит количество
форма продажи содержит гарантию дней default 30
форма продажи содержит чекбокс "Без гарантии"
sale create сохраняет warranty fields
sale detail показывает кнопку "Товарный чек"
receipt preview открывается
receipt показывает гарантию в днях
receipt показывает no warranty disclaimer при "Без гарантии"
финальные формы не выдуманы, есть placeholder note
tests pass: core, inventory-sales-module, avito-module
direct DB access отсутствует
commit без amend
READY_FOR_OWNER_RECHECK
```

---

# 19. Главное правило

После Stage04E-R3 не переходить дальше.

Финальный статус:

```text
TECHNOREBOOT_STAGE04E_R3_SALES_WARRANTY_RECEIPT_PRINT_ACTIONS_READY_FOR_OWNER_RECHECK
OWNER_MANUAL_CHECK_REQUIRED: true
NEXT_STEP: владелец проверяет UI
```
