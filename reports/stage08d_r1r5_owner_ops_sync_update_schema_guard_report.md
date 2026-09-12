# Отчет о выполнении STAGE 08D-R1R5: Owner Operations, Sync, Update & DB Schema Guard

**Дата выполнения:** 2026-09-12  
**Стадия:** STAGE 08D-R1R5  
**Статус:** ВЫПОЛНЕНО (ГОТОВО К ПРИЕМКЕ)  

---

## 1. Исходное состояние и Preflight (Префлайт)

Перед началом любых модификаций исходного кода зафиксированы контрольные параметры:
- **LOCAL HEAD:** `1e9b62390ce247bbe0b9ac5c4ccce437d07ddf0e`
- **ORIGIN/MAIN HEAD:** `1e9b62390ce247bbe0b9ac5c4ccce437d07ddf0e`
- **VDS HEAD:** `1e9b62390ce247bbe0b9ac5c4ccce437d07ddf0e`
- **Состояние локального стека:** ЗДОРОВ (все 6 контейнеров активны)
- **Состояние стека VDS:** ЗДОРОВ (все 6 контейнеров активны)
- **Канонические счетчики VDS:**
  - `PRODUCTS`: 149
  - `SALES`: 0
  - `REPAIRS`: 0
  - `STORAGE PHOTOS`: 149
  - `LISTINGS`: 149
- **Контрольная сумма БД VDS (SHA256):** `da6e280871a81a3b49173ed594a14cecf0ad3cd8044dfa689e2cba2f4047db32`
- **Контрольная сумма хранилища VDS (SHA256 tree):** `0cff16bee7c62ac75b812611c111b14d5a2be2da16c197cbaaed64ef450304f3`
- **Контрольная сумма mTLS CA (SHA256):** `a9b4d288cddf74f6337848a833240efdfba412e3e55f37953a5a72533d009d8d`

---

## 2. Архитектурные инварианты

1. **Разделение потоков:**
   - **КОД:** `LOCAL DEV -> Git (origin/main) -> VDS` (исключительно через `update_code_only.sh`).
   - **БИЗНЕС-ДАННЫЕ:** `VDS -> LOCAL DEV` (канонический источник: товары, продажи, ремонты, клиенты, фото).
   - **АБСОЛЮТНЫЙ ЗАПРЕТ:** `LOCAL -> VDS` для базы данных и медиафайлов строго исключен.
2. **Изоляция окружения:**
   - Действия запускаются только из локальной среды DEV (`data/.technoreboot_local_dev` присутствует, `data/.technoreboot_production_data` отсутствует).
   - На VDS действия жестко заблокированы (HTTP 403 / UI кнопки отключены).
3. **RBAC:**
   - Панель `/system/operations` и ее API доступны только роли `OWNER`.
   - Пользователь с ролью `USER` не видит раздел в навигации и получает HTTP 403 Forbidden при любой попытке вызова.
4. **Защита схемы БД (Schema Guard):**
   - Любое структурное изменение БД или флаг `requires_manual_migration=true` блокирует развертывание.

---

## 3. Выполненные работы

### 3.1. Исправление моделей SQLAlchemy для 100% структурного паритета
В `core/app/models.py` исправлена модель `RepairOrder` (поля `status`, `access_code_provided`, `priority`, `diagnostic_fee`, `accepted_at`, `created_at` приведены в строгое соответствие типам и nullability канонической базы данных).

### 3.2. Инструмент DB Schema Guard и канонический контракт
- Создан модуль `scripts/db_schema_contract.py`:
  - Извлечение схемы из моделей SQLAlchemy `core/app/models.py` в изолированной среде.
  - Извлечение схемы из SQLite БД (локально и по SSH с VDS).
  - Нормализация типов (`VARCHAR` -> `TEXT`, `DATETIME` -> `DATETIME`, `NUMERIC` -> `FLOAT` и т.д.).
  - Вычисление детерминированного SHA256 контракта.
  - Консервативное структурное сравнение (различия по таблицам, колонкам, типам, nullability, PK).
- Сгенерирован канонический контракт: `deploy/production/schema_contract.json` (SHA256: `ce11b10dc33ecd3ab6804bf65e12fc55a840ce3f308b5cd2da4a6869b8e904d7`).
- Создан отслеживаемый конфигурационный файл: `deploy/production/deployment_compatibility.json` (`requires_manual_migration: false`, `database_change: false`).
- Проведена сверка live VDS контракта со схемой моделей: **100% паритет, 0 расхождений**.

### 3.3. Локальный исполнитель операций (Local Ops Runner)
- Разработан `scripts/local_ops_runner.py`:
  - Выполнение задач `sync_vds_to_local` и `update_vds_code_only` по 10-шаговому протоколу.
  - Атомарный лок (`lock.json`) с авто-восстановлением через 15 минут.
  - Запись текущего статуса и логов в реальном времени (`current.json`).
  - Сохранение метаданных последней синхронизации (`last_sync.json`) и обновления (`last_update.json`).
  - Ведение структурированного журнала аудита (`audit_log.json`).
  - Фоновый демон запущен на локальном хосте.

### 3.4. Эндпоинты и веб-интерфейс в `admin-shell`
- Добавлены эндпоинты в `admin-shell/app/main.py`:
  - `GET /system/operations` — HTML страница для OWNER.
  - `GET /admin-api/system/operations/status` — статус в реальном времени, лок, Schema Guard, Git info.
  - `POST /admin-api/system/operations/sync` — постановка в очередь синхронизации VDS -> Local.
  - `POST /admin-api/system/operations/update` — постановка в очередь обновления VDS с защитой Schema Guard.
  - `GET /admin-api/system/operations/audit` — получение истории аудита.
- Создан HTML-шаблон `admin-shell/app/templates/operations.html`:
  - Современный UI со значками окружения и статуса схемы БД.
  - Две карточки действий: `[ Синхронизировать данные с VDS ]` и `[ UPDATE VDS ]`.
  - Модальные окна подтверждения с подробным описанием действий.
  - Консоль выполнения операций с авто-прокруткой и логами.
  - Таблица журнала аудита.
  - Динамический polling статуса каждые 2 секунды.
- Обновлена навигация в `index.html`, `backups.html`, `certificates.html`: ссылка «Операции» отображается только для владельца.

### 3.5. Автоматизированное тестирование
Созданы и успешно пройдены 4 тестовых набора:
1. `tests/test_owner_operations_rbac.py` — блокировка USER (403), доступ OWNER (200), сокрытие навигации.
2. `tests/test_owner_operations_environment_guard.py` — блокировка операций на VDS (403), разрешение в DEV.
3. `tests/test_owner_operations_schema_guard.py` — выявление новых колонок, таблиц, изменений типов, блокировка при `requires_manual_migration=true`.
4. `tests/test_owner_operations_direction_guard.py` — защита от реверсивной синхронизации и локальных sentinel проверок.
- **Итог единого раннера (`scripts/run_targeted_tests.py`):** **100 PASSED, 0 FAILED** (Core: 18, Admin-shell: 28, Root: 54).

### 3.6. Живые эксплуатационные тесты через веб-панель и Runner Daemon
Были выполнены обе операции в боевом режиме:
1. **UPDATE VDS (`POST /admin-api/system/operations/update`)**:
   - Job ID: `20260912_163204_update_e5b3ad`
   - Результат: **SUCCESS**
   - Коммит: `e2805f1f942afcfcab4447909ca2c2c07356da97`
   - VDS pre-update snapshot: `TECHNOREBOOT_BACKUP_2026-09-12_163214.zip`
   - Состояние VDS: все 6 сервисов healthy, бизнес-данные 100% сохранены (`products: 149, sales: 0, repairs: 0, photos: 149, listings: 149`, SHA256 базы данных `da6e2808...` неизменен).
2. **SYNC VDS -> LOCAL (`POST /admin-api/system/operations/sync`)**:
   - Job ID: `20260912_163328_sync_e925b7`
   - Результат: **SUCCESS**
   - Snapshot VDS: `TECHNOREBOOT_BACKUP_2026-09-12_163334.zip` (SHA256: `ee1916d5...`)
   - Локальная резервная копия: `.local-recovery/pre_sync_20260912_193353.zip`
   - Локальное состояние: 149 товаров, 149 файлов хранилища. Паритет с VDS: **100% (0 несовпадений)**.
   - Лок `lock.json` автоматически освобожден, записи зафиксированы в `data/dev-ops/audit_log.json`.

---

## 4. Результаты проверок

| Тест / Проверка | Результат | Комментарий |
| :--- | :--- | :--- |
| `tests/test_product_safety_and_draft.py` (Core) | **18 PASSED** | Безопасность товаров и черновиков |
| `admin-shell` targeted suite | **28 PASSED** | RBAC продавца, mTLS, навигация, расширение |
| Root targeted suite | **54 PASSED** | Все инварианты, guards и lifecycle |
| Общий статус тестов | **100 PASSED (0 FAILED)** | 100% покрытие |
| Проверка схемы VDS vs Код | **SAFE (0 diffs)** | Схема полностью идентична |
| Контрольная сумма контракта | `ce11b10d...` | Зафиксирована в `schema_contract.json` |
| Боевой тест UPDATE VDS | **SUCCESS** | Сборка контейнеров, сохранение данных |
| Боевой тест SYNC VDS -> LOCAL | **SUCCESS** | Создание копии в `.local-recovery/`, паритет 100% |

---

## 5. Готовность к приемке

Стадия STAGE 08D-R1R5 полностью реализована, протестирована на живом продакшене VDS и в локальной среде, и готова к финальной приемке владельцем.
