# Массовые (Batch) операции в каталоге товаров

## Описание функционала
В модуле складского учета Technoreboot (/inventory/products) реализована поддержка пакетных операций над товарами:
1. **Чекбокс в шапке таблицы (#select-all-products)**:
   - При клике переключает выбор всех товаров на текущей странице.
   - Поддерживает трехпозиционное состояние (indeterminate), если выбрана часть товаров.
2. **Чекбоксы в строках товаров (.product-select-cb)**:
   - Позволяют выбирать произвольный набор товаров.
   - Поддерживают выбор диапазона через клавишу Shift + Click.
3. **Плавающая панель массовых действий (#batch-actions-bar)**:
   - Автоматически отображается внизу экрана при выборе одного или нескольких товаров (>= 1).
   - Показывает счетчик выбранных позиций (Выбрано товаров: N).
   - Кнопка Снять выделение (#btn-batch-deselect).
4. **Массовая смена статуса**:
   - Выпадающий список со статусами: Черновик (draft), В наличии (in_stock), В резерве (reserved), Продан (sold), В архиве (archived), Списан (written_off).
   - Кнопка Применить. Отправляет запрос на POST /products/batch-action и вызывает POST /api/products/batch в Core API, выполняя транзакционное обновление, создание записей в product_events и аудит-логе.
5. **Массовая смена места хранения**:
   - Выпадающий список с локациями: Магазин (store), Мастерская (workshop), Архив (archive), Черновик (draft).
   - Кнопка Применить. Обновляет место хранения для всех выбранных позиций.
6. **Массовая печать ценников 58x40 мм**:
   - Кнопка Печать ценников (58x40).
   - Открывает страницу пакетного предпросмотра /inventory/products/price-tags/batch?ids=...
   - Рендерит ценники стандартного размера 58x40 мм с штрихкодами (SVG Code128), ценой в крупном читаемом формате, условиями гарантии и разделителями страниц (@media print { page-break-after: always; }) для термопринтера.
   - Автоматически вызывает системное окно печати браузера (window.print()).
7. **Массовая продажа (Добавить в чек)**:
   - Кнопка В чек (Массово).
   - Добавляет все выбранные товары со статусом in_stock / reserved и местом store в текущую корзину (request.session['cart']).
   - Перенаправляет пользователя в корзину кассы (/inventory/cart) для быстрого оформления продажи.

## Архитектура API
- **Core API**:
  - Endpoint: POST /api/products/batch
  - Schema: ProductBatchRequest (product_ids, status, storage_location, comment)
  - Response: ProductBatchResponse (updated_count, product_ids, status, storage_location)
- **Inventory Sales Module**:
  - Endpoint: POST /products/batch-action (JSON и FormData)
  - Endpoint: GET/POST /products/price-tags/batch (HTML-шаблон price_tag_batch.html)
  - Клиент: core_client.batch_update_products(...)
- **Маршрутизация**:
  - В products.py статические маршруты /products/batch-action и /products/price-tags/batch размещены перед параметризованным маршрутом /products/{product_id}, исключая затенение маршрутов фреймворком FastAPI / Starlette.
