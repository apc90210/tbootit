# Pre-existing Core Test Failures Audit

- **Date:** 2026-09-30
- **Auditor:** AntiGravity
- **Audit Stage:** WEB-03A R3
- **Baseline Commit:** `fc6e63e` (`d0e6722^`)
- **Status:** PRE_EXISTING_FAILURES_CONFIRMED

---

## Executive Summary

В рамках аудита WEB-03A R3 выполнено верификационное сравнение результатов тестирования на текущем коммите `fd8d452` и на базовом коммите `fc6e63e` (до внедрения изоляции тестов базы данных WEB-03A R2).

- На baseline `fc6e63e`: **5 failed, 281 passed**
- На current `fd8d452`: **5 failed, 284 passed** (+3 новых теста изоляции в `test_database_persistence_config.py`, 100% pass)
- **Все 5 падений на 100% идентичны по nodeid, стектрейсам и причинам.** Ни одно из падений не вызвано коммитами R2 (`d0e6722`, `7952b6a`, `fd8d452`).
- Все падения вызваны легитимными изменениями бизнес-логики Core (введение обязательной авторизации владельца в Stage 11D и валидации суммы ремонта в Stage 05), под которые старые тесты не были обновлены.
- Влияние на web-проект `tboot-site`: **НУЛЕВОЕ**.

---

## Detailed Failure Matrix

### 1. `test_product_soft_delete_preserves_row_and_writes_off`

- **Nodeid:** `core/tests/test_product_safety_and_draft.py::test_product_soft_delete_preserves_row_and_writes_off`
- **Код падения:** `assert resp.status_code == 200` -> `assert 403 == 200`
- **Причина:** Тест вызывает `client.delete(f"/api/products/{pid}")` анонимно. В Stage 11D удаление товаров переведено на строгую модель безопасности с требованием прав владельца (`owner_required`), возвращающую `403 Forbidden` при отсутствии авторизации.
- **Baseline Result:** FAILED на `fc6e63e` с идентичным `403 == 200`.
- **Влияние на Web:** Отсутствует. Публичный сайт не удаляет товары и работает исключительно в read-only режиме каталога (`GET /api/products/`).
- **Будущая задача Core:** Передать заголовок авторизации владельца (`X-API-Token` / bearer token) в вызов фикстуры теста.

---

### 2. `test_seller_draft_workflow`

- **Nodeid:** `core/tests/test_product_safety_and_draft.py::test_seller_draft_workflow`
- **Код падения:** `assert r5.status_code == 200` -> `assert 403 == 200`
- **Причина:** В шаге 4 теста выполняется удаление черновика через `DELETE /api/products/{pid}` без прав владельца. Эндпоинт корректно возвращает `403 Forbidden`.
- **Baseline Result:** FAILED на `fc6e63e` с идентичным `403 == 200`.
- **Влияние на Web:** Отсутствует. Товары в статусе `draft` скрыты от сайта на уровне Core API (`is_published_site == 1 and status == 'in_stock'`).
- **Будущая задача Core:** Авторизовать вызов удаления в сценарии тестирования черновиков.

---

### 3. `test_no_destructive_delete_endpoints_for_business_entities`

- **Nodeid:** `core/tests/test_product_safety_and_draft.py::test_no_destructive_delete_endpoints_for_business_entities`
- **Код падения:** `assert client.delete("/api/sales/1").status_code in (404, 405)` -> `AssertionError: assert 200 in (404, 405)`
- **Причина:** В Stage 11D был добавлен официальный эндпоинт `DELETE /api/sales/{sale_id}` для контролируемого удаления продаж владельцем с аудитом. При прогоне полного сьюта продажа с ID 1 присутствует в БД от предыдущих тестов, поэтому роутер возвращает `200 OK`.
- **Baseline Result:** FAILED на `fc6e63e` в полном прогоне сьют-тестов Core с тем же ассертом.
- **Влияние на Web:** Отсутствует. Web-клиент не имеет доступа к продажам.
- **Будущая задача Core:** Обновить контрактную проверку: исключить `/api/sales/{id}` из списка эндпоинтов, не поддерживающих DELETE, либо проверять защищенность RBAC.

---

### 4. `test_all_valid_status_transitions_complete`

- **Nodeid:** `core/tests/test_repairs_status_matrix_complete.py::test_all_valid_status_transitions_complete`
- **Код падения:** `AssertionError: Allowed transition in_repair -> ready failed with status 400: {"detail":"Для перевода в статус «Готов» укажите стоимость ремонта. Можно указать 0 ₽."}`
- **Причина:** В Stage 05 добавлена валидация: переход в статус `ready` («Готов») требует указания поля `actual_repair_amount`. Тест отправляет тело `{"status": "ready"}`, что вызывает штатный HTTP 400.
- **Baseline Result:** FAILED на `fc6e63e` с идентичной ошибкой 400.
- **Влияние на Web:** Отсутствует. Web-сервис не изменяет статусы ремонтов.
- **Будущая задача Core:** Передавать `"actual_repair_amount": 0` при тестировании перехода в статус `ready`.

---

### 5. `test_forbidden_status_transitions_rejected`

- **Nodeid:** `core/tests/test_repairs_status_matrix_complete.py::test_forbidden_status_transitions_rejected`
- **Код падения:** `assert 400 == 409` (`Forbidden transition received -> ready expected 409, got 400`)
- **Причина:** Валидация наличия стоимости ремонта срабатывает до проверки допустимости статусного перехода в матрице, поэтому запрос получает HTTP 400 вместо HTTP 409 Conflict.
- **Baseline Result:** FAILED на `fc6e63e` с идентичным `400 == 409`.
- **Влияние на Web:** Отсутствует.
- **Будущая задача Core:** Передавать `actual_repair_amount` в payload для проверки матрицы переходов, либо расширить ассерт до `in (400, 409)`.
