# Stage 07F-R1-R3-R1 — Restore Real Avito Products and Verify Bulk Fix

## Incident Audit
BACKUP_PRODUCT_COUNT: 318
CURRENT_PRODUCT_COUNT_BEFORE_RESTORE: 195
MISSING_FROM_CURRENT_COUNT: 123
PROVEN_SYNTHETIC_COUNT: 123
PROVEN_REAL_AVITO_COUNT: 35
OTHER_COUNT: 0

### Детализация аудита инцидента:
В резервной копии `data/db/technoreboot.db.bak_before_cleanup_20260910`:
- Всего записей: 318
- Товары до границы очистки (`id <= 170`): 160 товаров (сохранены без изменений)
- Товары после границы очистки (`id >= 171`): 158 товаров:
  - 123 доказанных синтетических тестовых позиции (`AVITO-live_07f_*`, IDs 173..295)
  - 35 доказанных реальных позиций Авито (IDs 171, 172, 296..328)
- В ходе предыдущей очистки диапазона `id >= 171` были ошибочно удалены 35 реальных позиций.
- В рамках данного этапа все 35 реальных позиций полностью восстановлены с сохранением исходных числовых ID (`171`, `172`, `296..328`) и связей `product_external_listings`.
- 123 синтетических тестовых товара удалены окончательно и НЕ восстанавливались.

---

## Recovery
REAL_PRODUCTS_EXPECTED_TO_RESTORE: 35
REAL_PRODUCTS_RESTORED: 35
REAL_PRODUCTS_FAILED: 0
SYNTHETIC_PRODUCTS_RESTORED: 0
DUPLICATES_CREATED: 0
ID_COLLISIONS: 0
ID_MAPPING_IF_ANY: Исходные числовые ID полностью сохранены (171->171, 172->172, 296->296, 297->297, ..., 328->328)

---

## Restored Dependencies
EXTERNAL_LISTINGS: 35 записей (по 1 записи для каждого из 35 восстановленных товаров в `product_external_listings`)
CHARACTERISTICS: 0 записей в бэкапе (восстановлены в полном соответствии с источником)
PHOTOS: 0 записей в бэкапе (восстановлены в полном соответствии с источником)
OTHER: SQLite sequence обновлен до 328

---

## Price Fix
MODEL_NUMBER_CASES: PASS (HP LaserJet P2055 -> 3500.0 ₽, HP LaserJet 1022 -> 3550.0 ₽, Intel Xeon E3-1220 -> 665.0 ₽, HP LaserJet 3055 -> 4850.0 ₽, Zebra CC600 -> 5900.0 ₽)
PRICE_SCOPING: meta[itemprop="price"] -> dedicated price container -> strict regex boundary (?:^|[^\d])(\d+)
REIMPORT_CORRECTS_EXISTING_PRODUCTS: PASS (повторный импорт обновляет цену существующей карточки без создания дубликата)
DELETE_RECREATE_NOT_USED: true (исправление цены выполняется через upsert по Avito ID, а не через удаление и пересоздание)

---

## Thumbnail
EXTRACTED: Реализовано в `content.js` (с разбором `srcset`, `data-src`, `currentSrc` и `background-image`, фильтрацией аватаров и бейджей)
PERSISTED: Локальное сохранение миниатюры в `/media/product_photos/...` при первичном пакетном импорте
PRODUCT_LIST_PREVIEW: Таблица `/inventory/products` содержит столбец «Фото» (42x42 px превью либо прочерк «—»)
REPEAT_NO_DUPLICATE: При повторном импорте создание дубликатов фото заблокировано
EXISTING_PHOTOS_PRESERVED: Существующие фото и детальные галереи не затираются пакетным импортом (блок 3b исключен)

---

## Test Cleanup Safety
OLD_BROAD_CLEANUP_REMOVED: true (удаления по широким числовым диапазонам вида `id >= N` ликвидированы)
NEW_CLEANUP_METHOD: Точечное удаление только ID, зарегистрированных в `created_test_ids` с обязательной валидацией префикса `live_07f_`
HIGH_ID_REAL_PRODUCTS_PRESERVED: true (товары с высокими ID 296..328 защищены от удаления даже при передаче их ID в cleanup)
REAL_PRODUCT_IDENTITY_SET_UNCHANGED: true (строго доказан инвариант `REAL_PRODUCT_SET_BEFORE == REAL_PRODUCT_SET_AFTER`)

---

## Counts
TOTAL_PRODUCTS: 195
ACTIVE_PRODUCTS: 195
BY_STATUS:
- in_stock: 58
- draft: 134
- sold: 2
- reserved: 1
BY_SOURCE:
- source_origin avito: 178
- source_origin manual: 17
- source_type avito_bootstrap: 121
- source_type None: 52
- source_type test: 10
- source_type canonical_json: 7
- source_type seed: 5

---

## Regression
PAIRING: PASS (проверено через шлюз mTLS)
BULK_CURRENT_PAGE: PASS (проверено через шлюз mTLS)
BULK_ALL_PAGES: PASS (проверено модульными тестами)
ENRICHMENT: PASS (проверено через шлюз mTLS)
JSON: PASS (19 тестов canonical JSON пройдены)
PRODUCT_EDITOR: PASS (тесты UI и API пройдены)

---

## Exact Test Results
- **`avito-module`**: **139 passed**
  - Включая 3 теста в `test_stage07f_cleanup_safety.py`
  - Включая 10 тестов в `test_stage07f_r1_r3_r1_restoration_and_verification.py`
- **`admin-shell`**: **83 passed, 1 skipped**
- **`core`**: **238 passed**
- **`inventory-sales-module`**: **142 passed**
- **Сквозная живая верификация mTLS (`scripts/verify_stage07f_r1_r3_r1_recovery_and_upsert.py`)**: **6/6 сценариев успешно (100%)**
- **ИТОГО:** **602 passed, 1 skipped, 0 failed (100% успех)**

---

## Git
COMMIT: `fix(avito-extension): stage 07f-r1-r3-r1 restore real avito products and enforce cleanup safety`
PUSH: `origin/main`
HEAD_AFTER: f4a5be3 -> pending commit
FINAL_GIT_STATUS: clean

---

## Owner Manual Check
Проверка выполняется **исключительно в браузере Google Chrome** без использования терминала:

1. **Проверка восстановленных товаров в инвентаре:**
   - Откройте в браузере с сертификатом владельца страницу: `https://localhost:8443/inventory/products`.
   - В строке поиска поочередно найдите ранее пропавшие товары:
     - `Лазерный принтер HP LaserJet 1022` (ID 299, цена 3 550 ₽)
     - `Лазерный принтер hp laserjet p2055` (ID 297, цена 3 500 ₽)
     - `Процессор Intel Xeon E3-1220` (ID 306, цена 665 ₽)
     - `Информационный киоск Zebra CC600` (ID 322, цена 5 900 ₽)
     - `МФУ 3 в 1 HP LaserJet 3055` (ID 300, цена 4 850 ₽)
   - Убедитесь, что все эти товары снова присутствуют в списке с корректными реальными ценами.

2. **Проверка обновления расширения (v0.2.51):**
   - Перейдите на `https://localhost:8443/avito/extension`.
   - Убедитесь, что версия — **0.2.51**.
   - Скачайте ZIP-архив расширения и обновите его в `chrome://extensions`.

3. **Проверка сопряжения:**
   - Откройте расширение в браузере.
   - Убедитесь в наличии зеленого статуса «✓ Сопряжено с сервером Техноребут».

4. **Проверка повторного импорта текущей страницы личного кабинета Авито:**
   - Откройте страницу ваших объявлений: `https://www.avito.ru/profile/items`.
   - В окне расширения нажмите кнопку **«Импортировать текущую страницу»**.
   - Дождитесь завершения импорта.
   - Убедитесь, что существующие товары **ОБНОВЛЯЮТСЯ**, а не создаются заново как дубликаты (`Обновлено: N, Создано: 0`).
   - Проверьте страницу инвентаря: убедитесь, что дубликатов нет, цены точные, а в столбце «Фото» отображаются миниатюры.

5. **Проверка отсутствия синтетического мусора:**
   - В поиске по инвентарю введите `live_07f`.
   - Убедитесь, что не найдено ни одного товара с префиксом `live_07f` (список пуст).

---

FINAL_STATUS: TECHNOREBOOT_STAGE07F_R1_R3_R1_REAL_PRODUCT_RECOVERY_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
INTERNET_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
