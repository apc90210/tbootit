# PROMPT — Техноребут / Stage 04E-R4 Sales Cart, Receipt, Price Tag Requirements & R3 Recovery

## Роль агента

Ты senior fullstack architect, recovery engineer, FastAPI/Jinja2 developer, print-template engineer и бизнес-аналитик торгового процесса проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Твоя задача — НЕ начинать Stage04F, а выполнить recovery/alignment после проблемного Stage04E-R3 и заложить правильную бизнес-схему продажи:

```text
корзина товаров → оформление продажи → гарантийно-товарный чек → таблица продаж
```

Также нужно учесть ценник 58×40 мм на термопринтере и будущие штрихкоды.

---

# 1. Почему этот этап нужен

После Stage04E-R3 агент сообщил:

```text
FINAL_STATUS: SUCCESS
worktree clean: false
committed files: none
next step: Proceed to Stage 04F
```

Это неприемлемо.

Также в ходе Stage04E-R3 были опасные действия с runtime DB:

```text
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
```

и попытка ручного ALTER в локальный db-файл.

Следовательно:

```text
Stage04E-R3 нельзя считать owner-accepted.
Stage04F начинать нельзя.
Нужно сначала восстановить/зафиксировать состояние и привести требования к правильной схеме.
```

---

# 2. Новые owner-требования

Владелец уточнил:

```text
1. Ценник:
   - размер 58×40 мм;
   - печатается на термопринтере;
   - ценник не является отдельным разделом;
   - это кнопка у товара в наличии;
   - сейчас можно без штрихкода;
   - штрихкод будет добавлен позднее, но систему нужно проектировать с учетом будущих штрихкодов.

2. Товарно-гарантийный чек:
   - должен быть как в предоставленном примере, максимально один в один;
   - в накладной/чеке должны быть реквизиты и название организации;
   - нужна форма настройки/заполнения реквизитов организации;
   - по умолчанию реквизиты взять из предоставленного чека.

3. Продажа:
   - сначала накидываем товары в корзину;
   - потом оформляем гарантийник и продажу;
   - при продаже можно указать цену вручную;
   - при продаже можно указать количество товара;
   - гарантия по умолчанию 30 дней;
   - гарантию можно изменить;
   - гарантию можно убрать чекбоксом "Без гарантии";
   - если без гарантии, в чеке должен быть текст:
     "Товар продаётся без гарантии, в том состоянии, в котором есть.
      Покупатель внимательно осмотрел товар при покупке."

4. Продажи:
   - все продажи должны фиксироваться в таблице продаж;
   - владелец должен потом смотреть продажи отдельно.
```

---

# 3. Приложенные материалы owner

Владелец предоставил:

```text
1. Фото ценника.
2. RTF-файл товарного чека:
   Tovarnyy_chek_rasshirennyy8888888.rtf
```

Если файл есть в Downloads, найти его:

```powershell
Get-ChildItem -Path C:\Users\Apc\Downloads -Recurse -File |
  Where-Object { $_.Name -like "*Tovarnyy*chek*" -or $_.Name -like "*.rtf" } |
  Select-Object FullName, LastWriteTime, Length
```

Скопировать reference copy в проект, например:

```text
docs/reference_templates/tovarnyy_chek_rasshirennyy8888888.rtf
```

Если файла нет — использовать требования из этого prompt.

## 3.1 Default organization data from receipt example

Использовать как дефолтные реквизиты:

```text
Название: ИП Атанов Павел Сергеевич
ИНН: 667009336901
Адрес: Свердловская обл. г. Екатеринбург, ул. Кузнецова, дом 10
Телефон: +7 343 344 88 95
```

## 3.2 Receipt structure from example

Гарантийно-товарный чек должен включать:

```text
Название организации
ИНН
Адрес
Телефон

Товарный чек № <номер> от <дата время>

Таблица:
№
Наименование
Код
Ед. изм.
Кол-во
Цена
Сумма

Итого
Предоплата
К оплате
Всего наименований
Сумма прописью

Отпустил:
Покупатель:
Частное лицо

Гарантийные условия
Подпись покупателя:
С условиями ознакомился и согласен: _______________________________
```

Если гарантия включена:

```text
На все Б/У товары предоставляется гарантия <N> дней.
```

Если гарантия выключена:

```text
Товар продаётся без гарантии, в том состоянии, в котором есть.
Покупатель внимательно осмотрел товар при покупке.
```

---

# 4. Главный статус

Текущий статус:

```text
STAGE04E_R3_REPORTED_SUCCESS_BUT_UNCOMMITTED_AND_OWNER_REQUIREMENTS_CHANGED
```

Целевой статус:

```text
TECHNOREBOOT_STAGE04E_R4_SALES_CART_RECEIPT_PRICE_TAG_REQUIREMENTS_READY_FOR_OWNER_RECHECK
```

Gate:

```text
OWNER_MANUAL_CHECK_REQUIRED: true
OWNER_ACCEPTANCE_REQUIRED: true
DO_NOT_START_STAGE04F_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 5. Что запрещено

Строго запрещено:

```text
начинать Stage04F как отдельный этап
делать отдельный раздел "Ценники"
делать silent print без подтверждения пользователя
делать прямой DB access из inventory-sales-module
создавать отдельную DB inventory-sales-module
коммитить runtime DB
делать git add .
делать git add -u
делать git commit --amend
делать git reset / git clean / rebase / force push
делать Base.metadata.drop_all/create_all на runtime DB
удалять runtime данные
```

Если надо дописать лог после commit — сделать отдельный normal commit.

---

# 6. Обязательное правило поиска prompt-файлов

Перед работой найти prompt:

```text
TECHNOREBOOT_STAGE04E_R4_SALES_CART_RECEIPT_PRICE_TAG_REQUIREMENTS_PROMPT.md
```

Искать:

```text
C:\tbootit
C:\tbootit\.agents
C:\tbootit\docs
C:\tbootit\docs\obsidian
C:\tbootit\prompts
C:\tbootit\logs\prompts
C:\Users\Apc\Downloads
```

Если найден в Downloads — скопировать в:

```text
C:\tbootit\.agents\received_prompts\
```

В отчете указать:

```text
PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:
```

---

# 7. Phase A — R3 recovery audit first

Перед любой новой разработкой выполнить:

```powershell
Set-Location C:\tbootit

git status --short --untracked-files=all
git branch --show-current
git log --oneline -20
git diff --name-status
git diff --stat
docker compose ps
```

Найти, какие R3-файлы не закоммичены.

Особо проверить:

```text
core/app/models.py
core/app/schemas.py
core/app/routers/sales.py
core/app/main.py
inventory-sales-module/**/*
reports/*
docs/*
logs/2026-07-02.md
TECHNOREBOOT_STAGE04E_R3_REPORT.md
task.md
implementation_plan.md
debug.py
```

Если R3 changes valid — включить их в нормальный targeted commit.

Если есть мусорные/временные debug файлы — не коммитить, но не удалять без явного анализа. В report указать.

Создать recovery note:

```text
reports/stage04e_r4_r3_recovery_note.md
```

Структура:

```text
R3 worktree before:
Uncommitted files:
Valid files:
Unexpected/temp files:
Action:
```

---

# 8. Phase B — settings for organization requisites

Нужна форма настройки реквизитов организации.

Для MVP можно хранить настройки в Core DB.

Добавить Core model/table, если нет:

```text
organization_settings
```

Поля:

```text
id
organization_name
inn
address
phone
default_cashier_name nullable
default_customer_label default "Частное лицо"
created_at
updated_at
```

Default seed/ad-hoc migration:

```text
organization_name = "ИП Атанов Павел Сергеевич"
inn = "667009336901"
address = "Свердловская обл. г. Екатеринбург, ул. Кузнецова, дом 10"
phone = "+7 343 344 88 95"
default_customer_label = "Частное лицо"
```

Core endpoints:

```text
GET /api/settings/organization
PUT /api/settings/organization
```

Inventory UI page:

```text
GET /settings/organization
POST /settings/organization
```

Navigation may include:

```text
Настройки
```

Допустимо добавить пункт меню "Настройки", но не "Ценники".

---

# 9. Phase C — sale cart flow

Текущий flow "продать один товар сразу" нужно заменить/расширить на корзину.

Главное бизнес-поведение:

```text
1. В списке товаров у товара in_stock есть "В корзину".
2. В корзине можно менять:
   - количество
   - цену вручную
3. На checkout задается:
   - способ оплаты
   - гарантия дней default 30
   - "Без гарантии"
4. Нажимаем "Оформить продажу".
5. Core создает sale и sale_items.
6. Продажа видна в /sales.
7. Открывается страница продажи.
8. Оттуда печатается товарно-гарантийный чек.
```

MVP cart storage options:

```text
Preferred: Core sale draft endpoints.
Acceptable MVP: signed cookie/session cart in inventory-sales-module without separate DB.
```

Если chosen MVP = cookie/session cart, обязательно описать tradeoff в report.

---

# 10. Phase D — sales table/list

Все продажи должны фиксироваться и быть доступными отдельно.

Проверить `/sales`:

```text
дата
номер продажи
количество товаров
сумма
способ оплаты
гарантия
статус
кнопки:
  Открыть
  Товарный чек
```

Core sales table/list API должен поддерживать:

```text
GET /api/sales
GET /api/sales/{id}
```

Если sale_items не возвращаются в detail — добавить.

---

# 11. Phase E — warranty and receipt

Core Sale должен хранить:

```text
warranty_enabled
warranty_days
```

Receipt preview:

```text
GET /sales/{sale_id}/receipt
```

Template:

```text
inventory-sales-module/app/templates/sale_receipt_preview.html
```

Должен использовать:

```text
organization settings from Core
sale number/id
sale datetime
sale items
product code/sku/internal code
quantity
manual price
line total
total
prepayment = 0,00 ₽ for MVP
customer label = "Частное лицо" default
warranty text
signature line
```

Обязательно добавить кнопку:

```text
Печать
```

Через:

```html
window.print()
```

---

# 12. Phase F — price tag 58×40 mm

Ценник — action у товара.

Routes:

```text
GET /products/{product_id}/price-tag
```

Template:

```text
inventory-sales-module/app/templates/price_tag_preview.html
```

Page size:

```css
@page {
  size: 58mm 40mm;
  margin: 0;
}
```

Layout по примеру owner:

```text
Магазин Техноребут
Тип / категория
Наименование товара
[место под штрихкод позднее]
Цена крупно
Код: <код товара>
```

Сейчас можно без штрихкода, но оставить placeholder/future-ready место в коде и docs.

---

# 13. Phase G — barcode future foundation

Сейчас штрихкод можно не печатать, но нужно заложить:

```text
product.barcode nullable
search/add-to-cart by barcode later
```

Если в Core Product уже есть code/sku — не ломать.

Если добавлять barcode рискованно — не реализовывать DB поле сейчас, но зафиксировать в docs:

```text
Barcode foundation planned:
- product.barcode
- barcode scan search
- add to cart by barcode
- barcode on price tag
```

---

# 14. Tests

Добавить/обновить tests.

Core:

```text
core/tests/test_organization_settings.py
core/tests/test_sales_cart_or_multi_item_sale.py
core/tests/test_sales_warranty.py
core/tests/test_sales_detail_items.py
```

Inventory:

```text
inventory-sales-module/tests/test_organization_settings_ui.py
inventory-sales-module/tests/test_cart_flow.py
inventory-sales-module/tests/test_price_tag_58x40.py
inventory-sales-module/tests/test_receipt_template.py
inventory-sales-module/tests/test_sales_list_table.py
inventory-sales-module/tests/test_no_price_tags_nav.py
```

Покрыть:

```text
organization defaults returned
organization settings update works
cart page opens
add product to cart
change quantity
manual price
checkout with warranty 30
checkout no warranty
sale created with items
sales list shows sale
receipt uses organization requisites
receipt warranty text
receipt no-warranty disclaimer
price tag page uses 58mm x 40mm CSS
nav has no "Ценники — скоро"
direct DB access absent
```

Run:

```powershell
docker compose exec core pytest
docker compose exec inventory-sales-module pytest
docker compose exec avito-module pytest
```

---

# 15. Manual smoke

Smoke steps:

```text
1. Open /products.
2. Verify no separate "Ценники — скоро" menu.
3. For in_stock product click "Печать ценника".
4. Verify 58×40 preview.
5. Return to /products.
6. Add one or more products to cart.
7. Open /cart.
8. Set manual price.
9. Set quantity.
10. Checkout with warranty 30 days.
11. Sale appears in /sales.
12. Open sale.
13. Open "Товарный чек".
14. Receipt shows org requisites and warranty 30 days.
15. Create another sale with no warranty.
16. Receipt shows no-warranty disclaimer.
```

---

# 16. Safety scans

Direct DB access in inventory-sales-module:

```powershell
git grep -n -I "create_engine\|SessionLocal\|sqlite\|technoreboot.db\|data/db\|sqlalchemy\|SELECT .* FROM\|INSERT INTO" -- inventory-sales-module
```

Runtime data:

```powershell
git status --ignored --short --untracked-files=all -- data/db
git status --ignored --short --untracked-files=all -- data/avito-module
```

No browser/captcha automation:

```powershell
git grep -n -I "selenium\|playwright\|webdriver\|undetected\|pyppeteer\|captcha solver\|captcha-solver\|bypass captcha\|обход капчи\|автологин\|auto login\|chromium" -- core admin-shell avito-module inventory-sales-module
```

---

# 17. Documentation/report

Create/update:

```text
docs/stage04e_r4_sales_cart_receipt_price_tag_requirements.md
docs/inventory_sales_module_ui_map.md
docs/inventory_sales_module_core_api_contract.md
docs/receipt_and_price_tag_templates_requirements.md
reports/stage04e_r4_sales_cart_receipt_price_tag_requirements_report.md
reports/stage04e_r4_r3_recovery_note.md
logs/2026-07-02.md
```

Report structure:

```text
# Stage 04E-R4 Sales Cart Receipt Price Tag Requirements Report

## STATUS

READY_FOR_OWNER_RECHECK / FAIL

## R3_RECOVERY

## OWNER_REQUIREMENTS_CAPTURED

## ORGANIZATION_SETTINGS

## SALES_CART_FLOW

## SALES_TABLE

## WARRANTY_LOGIC

## RECEIPT_TEMPLATE

## PRICE_TAG_58X40

## BARCODE_FUTURE_FOUNDATION

## TESTS

## MANUAL_SMOKE

## SAFETY_SCAN

## FILES_CHANGED

## OWNER_RECHECK_GUIDE

## FINAL_STATUS

TECHNOREBOOT_STAGE04E_R4_SALES_CART_RECEIPT_PRICE_TAG_REQUIREMENTS_READY_FOR_OWNER_RECHECK
```

---

# 18. Git

Use targeted add only.

Forbidden:

```text
git add .
git add -u
git commit --amend
```

If log changes after commit:

```text
make separate normal commit
```

Possible targeted add set depends on actual changes. Do not stage temp files like `debug.py`, root `task.md`, or root `implementation_plan.md` unless project rules explicitly require them.

Commit message:

```powershell
git commit -m "Align sales cart receipt and price tag requirements"
```

---

# 19. Definition of Done

Готово, если:

```text
R3 dirty state audited and resolved
no destructive DB reset/drop used
organization settings exist with default receipt requisites
organization settings UI exists
no separate "Ценники — скоро" nav
price tag action exists on product
price tag preview is 58×40 mm
cart flow exists or documented MVP alternative exists
manual price supported
quantity supported
warranty default 30 supported
no-warranty supported
sale receipt preview uses organization settings
sale receipt resembles provided receipt structure
sales list table shows all sales
barcode future foundation documented
tests pass: core, inventory-sales-module, avito-module
no direct DB access in inventory-sales-module
no amend used
READY_FOR_OWNER_RECHECK
```

---

# 20. Final response required from agent

Final answer must include:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04E_R4_SALES_CART_RECEIPT_PRICE_TAG_REQUIREMENTS_READY_FOR_OWNER_RECHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_STAGE04F_WITHOUT_OWNER_ACCEPTANCE: true
```

Не писать "можно переходить к Stage04F", пока владелец не проверит.
