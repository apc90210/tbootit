# Stage 07C-R1-R2 — JSON Import Zero-Result Fix

## Reproduction
OWNER_REQUEST_PATH: POST /admin-api/products/json/import
CORE_REQUEST_PATH: POST http://core:8000/api/products/json/import
CORE_RESPONSE_BEFORE: {"success":true,"created_count":2,"updated_count":0,"skipped_count":0,"errors":[],"imported_product_ids":[154,155]}
FRONTEND_RESULT_BEFORE: "✓ Импорт успешно завершён! Создано: 0, обновлено: 0, ошибок: 0." (таблица результатов пуста)
PROVEN_ROOT_CAUSE: Несоответствие контракта ключей между бэкендом и фронтендом. Core API возвращал плоскую структуру (created_count, updated_count, skipped_count, errors), тогда как UI-скрипт в products_json.html считывал вложенный объект data.summary (summary.created, summary.updated, summary.skipped) и массив data.results. Из-за отсутствия этих полей frontend брал нули по умолчанию ({created: 0, updated: 0, skipped: 0}) и, поскольку skipped == 0, выводил зелёное сообщение об успехе со всеми нулями.

## Fix
BACKEND_CHANGED: В core/app/services/product_json_service.py метод import_canonical_products расширен: теперь возвращает как структурированный объект summary (total_in_payload, total, created, updated, skipped, errors), так и детальный массив results с поэлементными статусами и ошибками каждого товара.
ADMIN_SHELL_CHANGED: В admin-shell/tests/test_products_json_ui.py добавлены проверки сквозной передачи данных и наличия всех 4 классов исходов в UI.
FRONTEND_CHANGED: В admin-shell/app/templates/products_json.html добавлены карточки статистики для всех 4 классов исходов (Создано, Обновлено, Пропущено, Ошибок), реализовано отказоустойчивое чтение summary с поддержкой fallback-ключей бэкенда, отрисовка таблицы results с бейджами, и запрет показа зелёного баннера успеха при нулевых счетчиках для непустого пакета.
ACCOUNTING_INVARIANT_ENFORCED: created + updated + skipped + errors == total_in_payload. Ни один товар из переданного пакета не может потеряться из учета. Для непустого пакета с 0 обработанных товаров возвращается ошибка (success=False).

## Owner Fixture
INPUT_PRODUCTS: 2
CREATED: 2
UPDATED: 0
SKIPPED: 0
ERRORS: 0

## Field Verification
DELL_MONITOR: Название 'Монитор Dell P2419H 24" Full HD', категория 'Мониторы', бренд 'Dell', модель 'P2419H', цена продажи 8500.0, закупочная цена 5000.0, состояние 'Б/у', количество 1, склад 'Витрина', описание сохранено без искажений.
HP_LAPTOP: Название 'Ноутбук HP ProBook 450 G6 15.6"', категория 'Ноутбуки', бренд 'HP', модель 'ProBook 450 G6', цена продажи 24500.0, закупочная цена 15500.0, состояние 'Б/у', количество 1, склад 'Склад 1', описание сохранено без искажений.
CHARACTERISTICS_PRESERVED: Все характеристики категорий сохранены в avito_params_json и типизированные атрибуты (Монитор: Диагональ, Разрешение, Тип матрицы, Частота обновления, Разъемы; Ноутбук: Процессор, Оперативная память, Объем накопителя, Тип накопителя, Видеокарта, Диагональ экрана, Разрешение экрана, Операционная система).

## Import Paths
TEXTAREA: Успешно (HTTP 200, summary.created=2, summary.errors=0)
FILE_UPLOAD: Успешно (HTTP 200, summary.created=2, summary.errors=0)
SAME_CANONICAL_LOGIC: Оба пути вызывают один и тот же канонический сервис Core API и гарантируют идентичную обработку.

## Regression
SELECTED_EXPORT: Успешно (выгрузка выбранных товаров ?ids=154,155 возвращает канонический JSON с ровно 2 товарами)
FULL_EXPORT: Успешно (выгрузка всех товаров возвращает полный каталог со всеми 145 товарами)
ROUND_TRIP: Успешно (повторный импорт выгруженного JSON с существующими ID обновляет товары: updated=2, created=0, errors=0)
AVITO: Успешно (95 тестов модуля Авито пройдены)
OWNER_MTLS: Успешно (Gateway mTLS блокирует запросы без сертификата с кодом 403 и пропускает запросы с сертификатом Владельца с кодом 200)

## Exact Test Results
- Core test suite: 228 passed, 0 failed
- Admin Shell test suite: 80 passed, 1 skipped, 0 failed
- Avito Module test suite: 95 passed, 0 failed
- Total: 403 passed, 1 skipped, 0 failed

## Git
COMMIT: (to be recorded upon commit)
PUSH: origin/main
HEAD_AFTER: (to be recorded upon commit)
FINAL_GIT_STATUS: clean

## Owner Manual Check
1. Откройте в веб-браузере с установленным сертификатом Владельца адрес `https://127.0.0.1:8443/products/json`.
2. В Секции Б («Импорт товаров из JSON») вставьте эталонный JSON из двух товаров в поле «Или вставьте скопированный JSON в поле ниже».
3. Нажмите кнопку «🚀 Загрузить и импортировать товары».
4. Убедитесь, что отображается сводка:
   - Создано: 2
   - Обновлено: 0
   - Пропущено: 0
   - Ошибок: 0
   и в таблице ниже отображаются 2 строки с зелеными бейджами «СОЗДАН», присвоенными ID и уникальными артикулами PRD-XXXXXXXX.
5. Перейдите в Секцию В («Экспорт товаров в JSON») или раздел «Товары», чтобы убедиться, что Монитор Dell и Ноутбук HP присутствуют в каталоге со всеми характеристиками.
6. При желании повторите проверку, сохранив этот JSON в файл `.json` и загрузив его через область перетаскивания файлов.

FINAL_STATUS:
TECHNOREBOOT_STAGE07C_R1_R2_JSON_IMPORT_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
INTERNET_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
