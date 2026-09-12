# Отчет о выполнении STAGE 08D-R1R6: Owner Fast Rollback & Release Checkpoints

**Дата выполнения:** 2026-09-12  
**Стадия:** STAGE 08D-R1R6  
**Статус:** ВЫПОЛНЕНО (ГОТОВО К ПРИЕМКЕ)  

---

## 1. Исходное состояние и Preflight Baseline

Перед началом работ зафиксированы контрольные параметры системы:
- **LOCAL HEAD:** `5fadf332f364cf57f28ba595ef69dbebf116d9a4`
- **ORIGIN/MAIN HEAD:** `5fadf332f364cf57f28ba595ef69dbebf116d9a4`
- **VDS HEAD:** `e2805f1f942afcfcab4447909ca2c2c07356da97`
- **Состояние стека VDS:** ЗДОРОВ (все 6 сервисов `healthy`)
- **Свободное место на VDS:** 9097 MB (требуется >= 500 MB)
- **Канонические счетчики VDS:**
  - `PRODUCTS`: 149
  - `SALES`: 0
  - `REPAIRS`: 0
  - `STORAGE PHOTOS`: 149
  - `LISTINGS`: 149
- **Контрольная сумма БД VDS (SHA256):** `da6e280871a81a3b49173ed594a14cecf0ad3cd8044dfa689e2cba2f4047db32`
- **Контрольная сумма хранилища VDS (SHA256 tree):** `9bfe2827417e5dc8658afcdc8369aef83717f1a305279156b1507ecfc5a3ff1d`
- **Контрольная сумма mTLS CA (SHA256):** `a9b4d288cddf74f6337848a833240efdfba412e3e55f37953a5a72533d009d8d`

---

## 2. Архитектурные инварианты и правила безопасности

1. **Нормальный откат — СТРОГО ТОЛЬКО КОД (Code-Only Rollback):**
   - Нормальный быстрый откат переключает версию кодовой базы (Git commit) и перезапускает сервисные контейнеры Docker.
   - **НИ ПРИ КАКИХ ОБСТОЯТЕЛЬСТВАХ** нормальный откат не заменяет и не перезаписывает рабочую базу данных SQLite (`technoreboot.db`) и не откатывает пользовательские медиафайлы (`data/storage/`).
   - Все продажи, заказы на ремонт, созданные товары и загруженные фотографии, созданные после обновления, остаются в полной сохранности (0 data loss).
2. **Диагностика VDS Preflight & Запрет снимка мертвого сервера:**
   - Перед каждым обновлением или созданием точки восстановления выполняется проверка жизнеспособности VDS: SSH, порт HTTPS 443, Docker демон, 6 контейнеров в статусе healthy, чтение SQLite (`PRAGMA quick_check = ok`), свободное место на диске >= 500 MB.
   - Если сервер в состоянии `DEGRADED` или `UNREACHABLE`, обновление **БЛОКИРУЕТСЯ**. Снимок мертвого или поврежденного сервера **НИКОГДА НЕ СОЗДАЕТСЯ**.
3. **Защита схемы БД при откате (Rollback Schema Guard):**
   - Перед откатом живая схема БД на VDS сравнивается со схемой целевого релиза (`previous_schema_sha256`).
   - Если схемы различаются, откат **ЖЕСТКО БЛОКИРУЕТСЯ** (`ROLLBACK BLOCKED`). Для несовместимых схем требуется ручной миграционный пайплайн.
4. **Контрольные точки релиза (Release Checkpoint Model):**
   - Создаются автоматически перед каждым обновлением: бэкап VDS переносится в локальное хранилище `.local-recovery/vds-releases/<checkpoint_id>/`, сверяется SHA-256 хэш, тэгируются Docker-образы всех 6 сервисов, записывается `checkpoint.json`.
   - Политика удержания сохраняет не менее 3 последних точек восстановления и гарантированно не удаляет `last_known_good_vds_release.json`.
5. **Изоляция и RBAC:**
   - Откат доступен только Владельцу (`is_owner=True`) и только из локальной DEV-среды (`403 Forbidden` для роли USER и при вызове непосредственно на VDS).

---

## 3. Выполненные работы

### 3.1. Бэкенд и логика исполнителя (`scripts/local_ops_runner.py`)
- Добавлена функция `check_vds_health_preflight(ssh_key, vds_host)`:
  - Пакетная удаленная диагностика через SSH `python3 -` с таймаутами.
  - Проверка локального и удаленного диска, Docker, статусов 6 сервисов, SQLite quick_check, HTTPS 443.
  - Возвращает `HEALTHY`, `DEGRADED` или `UNREACHABLE` с детальной структурой зондов.
- Добавлена функция `create_vds_release_checkpoint(...)`:
  - Создание снимка на VDS, загрузка по SCP в `.local-recovery/vds-releases/<checkpoint_id>/business-backup.zip`.
  - Верификация контрольной суммы SHA-256 (сбой при несовпадении).
  - Тэгирование работающих контейнеров (`technoreboot-rollback/<checkpoint_id>/<service>`).
  - Запись манифеста `checkpoint.json` локально, в `data/dev-ops/checkpoints/` и на VDS.
- Добавлена функция `enforce_checkpoint_retention(keep_count=3)`:
  - Удержание >= 3 точек, безусловное сохранение `last_known_good_vds_release.json`.
- Добавлена операция `execute_rollback_vds_code_only(...)`:
  - Проверка доступности VDS.
  - Проверка Rollback Schema Guard (сравнение SHA-256 контракта живой схемы VDS и целевого релиза).
  - Создание предварительного аварийного бэкапа (Disaster Safety Backup) текущего состояния VDS.
  - Переключение Git на коммит целевого чекпоинта и перезапуск контейнеров без изменения БД.
  - Ожидание перехода всех 6 сервисов в `healthy`.
  - Верификация неизменности бизнес-данных и фиксация в журнале аудита.
- Интеграция автоматического отката в `execute_update_vds_code_only(...)`:
  - Если развертывание или проверка здоровья на VDS завершились ошибкой, автоматически вызывается откат кода к предыдущему коммиту и регистрируется статус `UPDATE_FAILED_ROLLBACK_SUCCESS`.
- Добавлены CLI-флаги `--preflight` и `--inventory`.

### 3.2. API эндпоинты в `admin-shell/app/main.py`
- Добавлена вспомогательная функция `_get_vds_checkpoints(devops_dir)` для сканирования и сортировки доступных точек восстановления.
- Расширен эндпоинт `GET /admin-api/system/operations/status`:
  - Возвращает `vds_health` (результат префлайта).
  - Возвращает `checkpoints_list` (список сохраненных точек восстановления).
  - Возвращает `latest_checkpoint`, `last_known_good`, `rollback_available`, `rollback_reason`.
- Добавлен эндпоинт `POST /admin-api/system/operations/rollback`:
  - Авторизация: только `OWNER` (403 для `USER`).
  - Защита окружения: только `LOCAL DEV` (403 для `VDS`).
  - Валидация: проверка наличия чекпоинтов (400 при отсутствии) и флага `rollback_allowed` (400 при несовместимости схемы).
  - Постановка задачи отката в очередь бегуна (`rollback_vds_code_only`).

### 3.3. Пользовательский интерфейс в `admin-shell/app/templates/operations.html`
- Добавлен бейдж здоровья VDS (`#vds-health-badge`) в заголовок страницы.
- Добавлена Карточка 3: **«Быстрый откат VDS»** (`#btn-rollback`) с отображением коммита, точки восстановления и статуса доступности.
- Добавлена таблица **«Последние точки восстановления VDS»** (`#checkpoints-card`) с колонками:
  - ID точки, Время создания, Коммиты (До -> Целевой), Локальный бэкап (статус и SHA), Данные VDS, Статус отката.
- Добавлено модальное окно подтверждения отката (`#modal-rollback`):
  - Детали отката (целевой коммит, ID чекпоинта).
  - Подтверждение совместимости схемы базы данных.
  - Важное уведомление: *«Откат затронет только код и контейнеры. Все данные пользователей останутся без изменений»*.
  - Обязательный чекбокс подтверждения перед разблокировкой кнопки запуска.
- Реализована функция JavaScript `executeRollback()` и интеграция с поллингом статуса.

### 3.4. Автоматизированные тесты
Разработаны и интегрированы 4 новых тестовых набора (20 тестов):
1. `tests/test_owner_operations_preflight.py` (6 тестов):
   - `test_preflight_ssh_unreachable`: SSH недоступен -> статус `UNREACHABLE`, блокировка.
   - `test_preflight_dead_https_alive_ssh_is_degraded`: порт 443 не отвечает -> `DEGRADED`.
   - `test_preflight_unhealthy_service_is_degraded`: нездоровый контейнер -> `DEGRADED`.
   - `test_preflight_unreadable_db_is_degraded`: сбой целостности SQLite -> `DEGRADED`.
   - `test_preflight_low_vds_disk_is_degraded`: мало места на VDS (< 500 MB) -> `DEGRADED`.
   - `test_preflight_low_local_disk_is_degraded`: мало места локально (< 500 MB) -> `DEGRADED`.
2. `tests/test_owner_operations_checkpoint.py` (4 теста):
   - `test_create_vds_release_checkpoint_success`: создание чекпоинта, скачивание бэкапа, сверка SHA-256, тэгирование образов, проверка манифеста.
   - `test_create_checkpoint_sha_mismatch_fails`: сбой при несовпадении SHA-256.
   - `test_enforce_checkpoint_retention_keeps_3`: удержание 3 последних точек, удаление устаревших.
   - `test_enforce_retention_preserves_last_known_good`: безусловное сохранение last known good точки.
3. `tests/test_owner_operations_rollback.py` (8 тестов):
   - `test_rollback_user_forbidden`: 403 для роли USER.
   - `test_rollback_anonymous_forbidden`: 403 для анонимных запросов.
   - `test_rollback_environment_guard_blocks_on_vds`: 403 при выполнении на VDS.
   - `test_rollback_no_checkpoints_returns_400`: 400 при отсутствии чекпоинтов.
   - `test_rollback_blocked_by_checkpoint_flag`: 400 при несовместимости схемы.
   - `test_rollback_owner_allowed_and_queued`: 200 и постановка в очередь для OWNER.
   - `test_execute_rollback_vds_code_only_success`: выполнение отката кода, аварийный бэкап, сохранение БД.
   - `test_auto_rollback_on_update_failure`: автоматический откат при сбое обновления (`UPDATE_FAILED_ROLLBACK_SUCCESS`).
4. `tests/test_owner_operations_rollback_schema_guard.py` (2 теста):
   - `test_rollback_schema_guard_matching_allows_rollback`: совпадение схем разрешает откат.
   - `test_rollback_schema_guard_mismatch_blocks_rollback`: различие схем жестко блокирует откат без изменения БД.

---

## 4. Результаты запусков тестовых наборов

Единый целевой раннер `scripts/run_targeted_tests.py`:
- **Core module tests:** 18 passed
- **Admin-shell module tests:** 28 passed
- **Root & Operations suites:** 74 passed
- **ИТОГО:** **120 PASSED, 0 FAILED**

---

## 5. Документация и отчетность

Созданы и актуализированы следующие документы:
1. `docs/vds_fast_rollback.md` — архитектура и регламент быстрого отката.
2. `docs/owner_operations_sync_update_rollback.md` — руководство по панели `/system/operations`.
3. `docs/production_deployment_model.md` — дополнен Разделом 9 (Preflight, Checkpoints & Fast Rollback).
4. `docs/production_status.md` — дополнен Разделом 6 (статус подсистемы отката и контрольных точек).
5. `reports/stage08d_r1r6_fast_rollback_release_checkpoint_report.md` — настоящий итоговый отчет.

---

## 6. Итоговый статус

- **Финальный статус:** `TECHNOREBOOT_STAGE08D_R1R6_FAST_ROLLBACK_RELEASE_CHECKPOINT_READY`
- **Готовность к аудиту и приемке Владельцем:** ДА.
