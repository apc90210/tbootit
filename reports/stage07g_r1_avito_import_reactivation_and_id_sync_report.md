# Отчет по выполнению: Stage 07G-R1 — Avito Import Reactivation and ID Sync

**Дата:** 2026-09-11  
**Ветка:** `main`  
**Статус:** `TECHNOREBOOT_STAGE07G_R1_AVITO_IMPORT_REACTIVATION_READY_FOR_OWNER_CHECK`  

---

## 1. Бизнес-правило и архитектурные изменения

В соответствии с прямым указанием Владельца, скорректирована бизнес-логика интеграции с Авито:

1. **Осознанный импорт активного объявления = подтверждение наличия товара в магазине:**
   - Импорт активного объявления для уже существующего, но архивного/проданного товара (`sold/archive/0`) восстанавливает этот же товар: `status = "in_stock"`, `storage_location = "store"`, `quantity = 1`.
   - Регистрируется событие `avito_import_reactivated`.
   - Полное отсутствие дубликатов.
2. **Отмена автоматического списания по неактивным статусам Авито:**
   - Удалено ошибочное правило обратной синхронизации, при котором `closed/inactive/blocked/removed` переводили товар в `sold/archive/0`.
   - Внешние неактивные статусы Авито обновляют исключительно метаданные в `product_external_listings.remote_status`.
   - Физический товар с витрины списывается только через кассовую продажу магазина или явное ручное действие сотрудника.
3. **Защита от инфляции остатков:**
   - Многократный импорт активного объявления сохраняет текущий положительный остаток, не накручивая количество.
4. **Универсальная идентификация по Avito ID:**
   - Поиск по всей базе без фильтров статуса: первичный по `product_external_listings.external_item_id`, вторичный (fallback) по `products.sku == "AVITO-{external_item_id}"` с автоматическим залечиванием связи.
5. **Поддержка локальных товаров:**
   - Локальные товары без Avito ID полностью валидны, функционируют во всех складских и кассовых операциях и изолированы от процессов импорта Авито.

---

## 2. Результаты тестов и проверок

### Автоматизированные тесты в Docker:
- `core/tests/test_stage07g_r1_avito_import_reactivation.py`: 11 passed (100%) (Тесты A-Q)
- `core/tests/test_avito_import_upsert.py`: 1 passed (100%)
- `core/tests/test_avito_archive_reactivation_and_reverse_sync.py`: 2 passed (100%)
- `core/tests/test_avito_id_primary_lookup.py`: 3 passed (100%)
- `technoreboot-core` full suite: 255 passed (100%)
- `technoreboot-inventory-sales-module` full suite: 151 passed (100%)
- `admin-shell` full suite: 83 passed, 1 skipped (100%)

### Живая верификация через Gateway 8443 (mTLS):
- Скрипт: `scripts/verify_stage07g_r1_avito_import_reactivation_live.py`
  - Step 1: Active import creates product in stock (`in_stock`, `store`, `1`) [PASS]
  - Step 2: Inactive remote statuses (`closed`, `blocked`, `removed`, `archived`) do NOT zero physical stock [PASS]
  - Step 3: Repeated active imports do NOT inflate quantity (remains 1) [PASS]
  - Step 4: Local store sale moves product to `sold/archive/0` [PASS]
  - Step 5: Active Avito import reactivates the SAME product from archive to `in_stock/store/1`, logs `avito_import_reactivated`, 0 duplicates [PASS]
  - Step 6: Local-only product without Avito ID works normally [PASS]
  - Step 7: Gateway 8443 mTLS access with Owner certificate returns 200 OK [PASS]
  - Step 8: Clean teardown of test records [PASS]

---

## 3. Аудит базы данных

- В базе данных `data/db/technoreboot.db` проверено 50 активных товаров.
- Все 50 товаров имеют корректный статус `in_stock` и место хранения `store`.
- Записей с ошибочными событиями `avito_archived` не обнаружено.
- Удаление реальных товаров из базы: 0 (строгий запрет соблюден).
