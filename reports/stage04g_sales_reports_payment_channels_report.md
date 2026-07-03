# Stage 04G Sales Reports and Payment Channels

## STATUS
READY_FOR_OWNER_CHECK

## OWNER_REQUIREMENT
Владелец запросил отдельный раздел "Отчёты по продажам" за день, неделю и год, с возможностью указания пользовательского периода. Отчёт должен показывать таблицу всех продаж, общую сумму, количество продаж и товаров, а также разбивку по способам поступления денег. Добавлен новый вариант поступления денег — "Счёт юрлица".

## IMPLEMENTED

### Payment channels
Добавлены новые методы `sbp` и `legal_entity_account`. Обновлены списки допустимых методов как в Core, так и в Inventory-модуле.

### Sales report Core API
Реализован эндпоинт `GET /api/reports/sales` для получения отчета за выбранный период (сегодня, неделя, месяц, год, произвольный) с агрегацией по методам оплаты.

### Sales report UI
В Inventory-модуле добавлен роутер `reports` и шаблон `reports_sales.html`, обеспечивающий отображение требуемой статистики и графики с разбиением по методам оплаты. Раздел добавлен в навигационное меню.

### Checkout payment method
Форма оплаты в корзине (Cart) обновлена для динамического вывода всех способов поступления денег из словаря, включая "Счёт юрлица". Чек (Receipt) также выводит выбранный способ поступления.

## API
- Core: `GET /api/reports/sales` (today, week, month, year, custom)
- Core: Добавлены `sbp` и `legal_entity_account` в валидацию `POST /api/sales`

## UI
- `GET /reports/sales`: Отдельная страница отчетов
- Форма корзины: добавлен выбор "Счёт юрлица"

## TESTS
- Core: Написан `test_sales_reports.py`, все остальные тесты пройдены.
- Inventory: Написаны `test_sales_payment_channels_ui.py` и `test_sales_reports_ui.py`, все тесты пройдены.
- Avito: Все тесты пройдены.

## MANUAL_SMOKE
- /reports/sales: 200 OK
- Core /api/reports/sales: Возвращает корректный JSON со сводкой и массивом продаж
- Checkout payment channel: Корзина выводит выпадающий список вариантов, в том числе Счёт юрлица.

## SAFETY_SCAN
Runtime tracked: Clean
Direct DB access: Clean
Destructive DB calls: Clean (только в тестах)
Secrets: Clean

## FILES_CHANGED
- core/app/models.py
- core/app/schemas.py
- core/app/main.py
- core/app/routers/reports.py
- core/app/routers/sales.py
- core/tests/test_sales_reports.py
- inventory-sales-module/app/core_client.py
- inventory-sales-module/app/routers/reports.py
- inventory-sales-module/app/routers/cart.py
- inventory-sales-module/app/routers/sales.py
- inventory-sales-module/app/templates/base.html
- inventory-sales-module/app/templates/reports_sales.html
- inventory-sales-module/app/templates/cart.html
- inventory-sales-module/app/templates/sales_list.html (uses dynamic payment methods)
- inventory-sales-module/app/templates/sale_receipt_preview.html
- inventory-sales-module/tests/test_sales_reports_ui.py
- inventory-sales-module/tests/test_sales_payment_channels_ui.py

## FINAL_STATUS
TECHNOREBOOT_STAGE04G_SALES_REPORTS_PAYMENT_CHANNELS_READY_FOR_OWNER_CHECK
OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
