# Stage 06C: Release Readiness, In-App Updater & Server Settings Preflight Report

- **Date:** 2026-10-09
- **Stage:** Stage 06C — Release Readiness, In-App Updater, Server Settings Preflight & Rollout Runbook
- **Baseline Git HEAD:** `3aaf3b429d2b24d7756f1ce3e8d2643a60f64c67` (branch: `main`)
- **Status:** **PASS** (Audit, local verification and runbook completed; production rollout gated by OWNER GO)
- **Target Release Scope:** Stage 06A (Mobile Inventory Catalog) + Stage 06B (Mobile Sales Reports Drill-down)
- **Target Production Environment:** Production VDS (`144.31.15.88`) — **STRICTLY UNTOUCHED DURING THIS STAGE**

---

## 1. Executive Summary & Code Classification

In accordance with `TR_Android_Stage06C_Release_Readiness_Updater_Server_Settings_Preflight_R1.md`, a complete architectural and code audit of the Technoreboot mobile in-app updater and server settings mechanisms was conducted, followed by full local test verification and the preparation of an operator-ready production rollout runbook.

### 1.1. Preflight Audit Classification Matrix (Prompt Section 0.3)

| # | Функциональный элемент | Статус | Фактическая реализация в коде |
|---|---|---|---|
| 1 | Пользовательская настройка адреса сервера | **ALREADY EXISTS** | `ServerSettingsRepository.kt`, `SettingsScreen.kt`. Адрес настраивается, сохраняется в `SharedPreferences`, валидируется и отображается в UI. |
| 2 | Безопасное применение URL ко всем API-запросам | **ALREADY EXISTS** | `MobileApiClient.kt` (`updateBaseUrl()`), `ServerSettingsRepository.kt`. Динамически обновляет OkHttp `baseUrl` без перезапуска приложения; release-сборки принудительно требуют схему `https://`. |
| 3 | Проверка доступности и доверия к серверу | **ALREADY EXISTS** | `ServerSettingsRepository.kt` (`validateServerUrl`), пинг через mTLS/TLS, явный отказ при некорректном сертификате или схеме. |
| 4 | Установка/смена enrollment при смене сервера | **ALREADY EXISTS** | `MobileApp.kt` (`handleServerUrlChanged`), `SessionRepository.kt`, `DeviceIdentityManager.kt`. При изменении URL сервера выводится диалог с предупреждением, сбрасывается сессия, удаляется аппаратный P-256 ключ из Android Keystore, очищается локальный кэш, приложение возвращается на экран первичного Enrollment. Учетные данные старого сервера никогда не отправляются на новый. |
| 5 | Серверный endpoint информации о новой версии | **ALREADY EXISTS** | `admin-shell/app/main.py` (`GET /api/mobile/app/update/manifest`). Защищён аутентификацией TRMOBILE1 PoP, возвращает метаданные (`version_code`, `version_name`, `sha256`, `apk_size`, `min_sdk`, `release_notes`, `mandatory`). |
| 6 | Выдача APK/manifest и контроль доступа | **ALREADY EXISTS** | `admin-shell/app/main.py` (`GET /api/mobile/app/update/apk`). Защищён TRMOBILE1 PoP, проверяет валидность и неотзыв устройства/сертификата, отдает файл через `FileResponse` с того же origin, поддерживает HTTP Range / 206 Partial Content и ETag для докачки. Защищён от path traversal. |
| 7 | Клиентское обнаружение версии, загрузка, hash check и OS Package Installer | **ALREADY EXISTS** | `UpdateManager.kt`, `UpdateDownloadRepository.kt`, `UpdateDownloadService.kt`. Проверка версии при старте (12ч throttling) и вручную; потоковая докачиваемая загрузка во foreground-сервисе; проверка SHA-256; проверка соответствия `applicationId`; проверка совпадения сертификата подписи с установленным приложением (`verifyApkSignerAgainstInstalled`); запуск стандартного системного инсталлятора через `FileProvider` (`com.technoreboot.mobile.fileprovider`). Запрет silent install. |
| 8 | Совместимость подписи и applicationId | **PARTIALLY EXISTS / BLOCKED** | `applicationId` совпадает (`com.technoreboot.mobile`). Отпечаток SHA-256 рабочего сертификата подписи известен (`741ffd5582e3ab46aee12a746a3aae7454fcaa79553b9702102bf3a4ec47bcd1`), но сам файл закрытого release keystore не хранится в git (стандарт безопасности). Сборка production APK требует секретов OWNER. |
| 9 | Миграция/обратная совместимость API Stage06A/06B | **ALREADY EXISTS** | Все эндпоинты Stage 06A (`/api/mobile/catalog/products`, photo proxy) и Stage 06B (`/api/mobile/reports/sales` с drilldown) являются аддитивными и обратно-совместимыми. Базовые Core схемы не ломают предыдущие версии. |
| 10 | Rollback на текущую production-версию | **ALREADY EXISTS** | Серверный rollback выполняется мгновенно переключением docker image / git commit без изменения БД. Клиентский rollback в Android (в случае установленного APK с повышенным `versionCode`) блокируется ОС Android от downgrade; регламентирован выпуск rollback-патча с `versionCode = V_current + 1` либо откат манифеста на сервере до canary-приёмки. |

---

## 2. Архитектура обновления и сетевых настроек

### 2.1. Серверные механизмы (`admin-shell`)
1. **Манифест (`/api/mobile/app/update/manifest`)**:
   - Читает активный `manifest.json` из директории `data/releases/mobile/` (или настроенной через переменную окружения `MOBILE_APP_RELEASE_DIR`).
   - Валидирует обязательные поля: `application_id`, `version_code`, `version_name`, `sha256`.
   - Сверяет реальный SHA-256 и размер лежащего на диске APK-файла перед публикацией метаданных.
   - Защищён PoP ECDSA подписью заголовка `X-Mobile-Signature` и сертификата устройства.
2. **Скачивание APK (`/api/mobile/app/update/apk?version_code=<n>`)**:
   - Строгая проверка совпадения запрошенного `version_code` с опубликованным релизом.
   - Поддержка заголовка `Range: bytes=start-end` и `If-Range` (HTTP 206 Partial Content), что критично для надёжной докачки на мобильных сетях.
   - Запрет path traversal (нормализация путей и проверка нахождения внутри каталога релизов).

### 2.2. Клиентские механизмы (`android-app`)
1. **Настройки сервера (`ServerSettingsRepository` + `SettingsScreen`)**:
   - Доступны как до первичной регистрации (на экране `EnrollmentScreen`), так и в основном интерфейсе приложения (`SettingsScreen`).
   - Release-сборки принудительно требуют HTTPS. Debug-сборки разрешают HTTP `127.0.0.1` / `10.0.2.2` для локальной разработки.
   - Безопасная изоляция сессии: при подтверждении смены URL стираются текущие токены, удаляется ключ устройства из Android Keystore, сбрасывается состояние API-клиента.
2. **Проверка и установка обновлений (`UpdateManager`)**:
   - **Anti-downgrade**: отклоняет предложения обновления, если `version_code <= current_version_code`.
   - **Same-origin & Integrity**: скачивает бинарник только с того же сервера, сверяет побайтовый SHA-256 хеш с манифестом.
   - **Signer verification**: вызывает `PackageManager.getPackageArchiveInfo()` и проверяет, что сертификат скачанного APK в точности совпадает с сертификатом установленного на устройстве пакета (`verifyApkSignerAgainstInstalled`). Если подписи не совпадают (например, попытка обновить release отладочным debug-ключом), процесс немедленно прерывается с ошибкой `SIGNATURE_MISMATCH`.
   - **Системный диалог установки**: вызывает стандартный Android `Intent.ACTION_VIEW` с MIME-типом `application/vnd.android.package-archive` и URI от `FileProvider`. Пользователь видит стандартное системное окно подтверждения установки.

---

## 3. Результаты локальной тестовой матрицы

Все тесты выполнены локально на рабочей станции `C:\tbootit`.

### 3.1. Admin-Shell тесты
- **Обновление и докачка (Range/206)**:
  - `admin-shell/tests/test_stage01d_mobile_update.py` + `admin-shell/tests/test_stage02a_server_range_update.py`
  - **Результат:** **31 / 31 PASS** (43.39s)
- **Мобильный каталог и отчёты drill-down**:
  - `admin-shell/tests/test_stage06a_mobile_catalog.py` + `admin-shell/tests/test_stage06b_mobile_sales_reports_drilldown.py`
  - **Результат:** **17 / 17 PASS** (5.56s)

### 3.2. Core тесты
- **Каталог, фильтры, сортировка, отчёты о продажах, статусы чеков**:
  - `core/tests/test_sales_reports.py`
  - `core/tests/test_products.py`
  - `core/tests/test_stage02b_reports_month.py`
  - `core/tests/test_products_search_filters.py`
  - `core/tests/test_sales_cancel_reissue.py`
  - `core/tests/test_sale_reissue_status_semantics.py`
  - **Результат:** **59 / 59 PASS** (4.13s)
  *(В процессе проверки в тестовом изоляционном файле `core/tests/conftest.py` зарегистрирован обработчик `configure_sqlite_connection` для корректной поддержки регистронезависимых функций `lower`/`upper` и внешних ключей в изолированной SQLite DB)*.

### 3.3. Android тесты и сборка
- **Модульные тесты (`testDebugUnitTest`)**:
  - `CatalogModelAndPathTest`, `SalesReportDrilldownTest`, `SalesReportTest`, `ServerSettingsTest`, `UpdateManagerTest`, `UpdateManifestTest`, `UpdateResumableDownloadTest` и др.
  - **Результат:** **159 / 159 PASS** (16s)
- **Статический анализ (`lintDebug`)**:
  - **Результат:** **BUILD SUCCESSFUL** (0 ошибок)
- **Сборка пакета (`assembleDebug`)**:
  - **Результат:** **BUILD SUCCESSFUL** (11s)
  - Артефакт: `android-app/app/build/outputs/apk/debug/app-debug.apk`
  - Размер: `39,001,066` байт (~37.2 МБ)
  - SHA-256: `df0dcb28da26691f497bc75974a2d6bfbc70ce7f0f7cfccf5b5c4d3995f0105e`

### 3.4. Целостность локальной БД (`data/db/technoreboot.db`)
- `PRAGMA quick_check`: `ok`
- `PRAGMA foreign_key_check`: `[]` (0 ошибок)
- Количество записей:
  - Товары (`products`): `423`
  - Продажи (`sales`): `70`
  - Заказы на ремонт (`repair_orders`): `2`
  - Движения товаров (`stock_movements`): `103`
- Мутации в локальную каноническую БД в ходе тестов: **0** (полная изоляция).

---

## 4. Release Inventory (Состав релиза Stage06A + Stage06B)

Релиз включает только изменения, необходимые для каталога инвентаря и иерархических отчетов:

### Серверная часть (`admin-shell` & `core`)
1. `admin-shell/app/main.py`:
   - Эндпоинт каталога: `GET /api/mobile/catalog/products` (поддержка категорий, брендов с фиксированным порядком `HP → Kyocera → Canon → Xerox → Samsung`, флага наличия `only_in_stock`, сортировки по цене/новизне).
   - Эндпоинт проксирования фотографий: `GET /api/mobile/catalog/products/{product_id}/photo`.
   - Эндпоинт отчетов с drill-down: `GET /api/mobile/reports/sales` (поддержка `period=today|week|month|year|custom`, разбивки по дням и месяцам, чеков дня, исключения отмененных/перевыпущенных чеков).
2. `core/app/routers/products.py`:
   - Поддержка сортировки и фильтрации товаров с сохранением канонической изоляции.

### Мобильный клиент (`android-app`)
1. `model/CatalogProduct.kt`: структуры данных товаров каталога, фото и метаданных наличия.
2. `model/SalesReport.kt`: структуры данных иерархических отчетов (`DaySummary`, `MonthSummary`, `ReceiptItem`, `PaymentBreakdown`).
3. `network/MobileApiClient.kt`: клиентские вызовы каталога, прокси фото и отчетов с подписью TRMOBILE1 PoP.
4. `ui/catalog/CatalogScreen.kt`: интерфейс каталога, фильтр-чипы брендов и категорий, переключатель цен, кнопка перехода в POS.
5. `ui/catalog/RemoteImage.kt`: компонент асинхронной загрузки и кэширования миниатюр товаров.
6. `ui/reports/SalesReportScreen.kt`: вкладки верхнего уровня (Сегодня, Неделя, Месяц, Год), карточки периодов.
7. `ui/reports/DayReceiptsScreen.kt`: отдельный одноуровневый экран списка чеков конкретного дня.
8. `ui/reports/MonthDaysScreen.kt`: отдельный одноуровневый экран списка дней конкретного месяца (плоский список, без группировок).
9. `ui/reports/ReportFormatters.kt`: форматирование валюты, дат и локализованное склонение числительных.
10. `ui/MobileApp.kt`: симметричная навигация «Назад», управление состоянием и кэширование родительских списков.

**Строго исключено из релиза:**
- Искусственные тестовые чеки и данные, сгенерированные локально для проверки Stage06B.
- Любые дампы локальной БД `technoreboot.db`.
- Отладочные скрипты и временные файлы.

---

## 5. Production Rollout Runbook (Инструкция оператора)

> [!WARNING]
> **НЕ ВЫПОЛНЯТЬ БЕЗ ЯВНОГО РАЗРЕШЕНИЯ OWNER.**  
> Все команды ниже приведены в качестве утвержденной операторской инструкции для выполнения **после** получения `OWNER GO`.

### Шаг 1. Пре-релизный бэкап на боевом сервере (`144.31.15.88`)
Перед любыми действиями на VDS создается полный атомарный снапшот:
```bash
# Выполняется на сервере 144.31.15.88
BACKUP_DIR="/srv/technoreboot/data/backups/pre_stage06_rollout_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# 1. Атомарный бэкап SQLite базы данных через .backup
sqlite3 /srv/technoreboot/data/db/technoreboot.db ".backup '$BACKUP_DIR/technoreboot.db'"

# 2. Сохранение конфигурации и переменных окружения
cp /srv/technoreboot/docker-compose.yml "$BACKUP_DIR/"
cp /srv/technoreboot/.env "$BACKUP_DIR/" 2>/dev/null || true

# 3. Верификация целостности сохраненного бэкапа
sqlite3 "$BACKUP_DIR/technoreboot.db" "PRAGMA quick_check;"
# Ожидается: ok
```

### Шаг 2. Проверка связности и статуса контейнеров до обновления
```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
# Все 6-7 контейнеров должны быть Up / healthy
curl -s -f http://localhost:8000/health || echo "Core UNHEALTHY"
curl -s -f http://localhost:8011/health || echo "Admin-Shell UNHEALTHY"
```

### Шаг 3. Деплой серверных компонентов (`core` и `admin-shell`)
1. Доставка коммитов Stage06A + Stage06B в git-репозиторий на VDS:
   ```bash
   cd /srv/technoreboot
   git fetch origin main
   git checkout main
   # Проверить совпадение HEAD
   git log -n 1 --oneline
   ```
2. Перезапуск серверных сервисов с нулевой миграцией данных (схемы БД не менялись, изменения аддитивны):
   ```bash
   docker compose up -d --build core admin-shell gateway
   ```
3. Проверка запуска и логов:
   ```bash
   docker compose ps
   docker logs --tail 30 technoreboot-admin-shell
   docker logs --tail 30 technoreboot-core
   ```
4. Проверка целостности боевой БД после старта:
   ```bash
   sqlite3 /srv/technoreboot/data/db/technoreboot.db "PRAGMA quick_check;"
   sqlite3 /srv/technoreboot/data/db/technoreboot.db "PRAGMA foreign_key_check;"
   ```

### Шаг 4. Сборка и подпись релизного Android APK (`com.technoreboot.mobile`)
Сборка боевого APK выполняется с использованием закрытого release keystore владельца:
1. Задание параметров окружения подписи (секреты OWNER):
   ```bash
   export ANDROID_RELEASE_STORE_FILE="/path/to/owner/technoreboot-release.jks"
   export ANDROID_RELEASE_STORE_PASSWORD="***"
   export ANDROID_RELEASE_KEY_ALIAS="technoreboot"
   export ANDROID_RELEASE_KEY_PASSWORD="***"
   ```
2. Сборка release APK:
   ```bash
   cd android-app
   ./gradlew assembleRelease
   ```
3. Проверка параметров собранного APK:
   - Пакет: `com.technoreboot.mobile`
   - Целевой `versionCode`: **23**
   - Целевой `versionName`: **"1.7.0"**
   - Проверка отпечатка подписи:
     ```bash
     apksigner verify --print-certs app/build/outputs/apk/release/app-release.apk | grep "SHA-256 digest"
     # Должен в точности совпасть с: 741ffd5582e3ab46aee12a746a3aae7454fcaa79553b9702102bf3a4ec47bcd1
     ```
4. Вычисление SHA-256 хэша APK и его точного размера в байтах:
   ```bash
   sha256sum app/build/outputs/apk/release/app-release.apk
   stat -c %s app/build/outputs/apk/release/app-release.apk
   ```

### Шаг 5. Публикация релиза на сервере для In-App Updater
1. Копирование подписанного APK в директорию релизов на VDS:
   ```bash
   cp app-release.apk /srv/technoreboot/data/releases/mobile/app-release-v23.apk
   ```
2. Формирование и запись `/srv/technoreboot/data/releases/mobile/manifest.json`:
   ```json
   {
     "application_id": "com.technoreboot.mobile",
     "version_code": 23,
     "version_name": "1.7.0",
     "min_sdk": 26,
     "apk_filename": "app-release-v23.apk",
     "apk_size": <ACTUAL_APK_SIZE_BYTES>,
     "sha256": "<ACTUAL_APK_SHA256_LOWERCASE>",
     "signing_cert_sha256": "741ffd5582e3ab46aee12a746a3aae7454fcaa79553b9702102bf3a4ec47bcd1",
     "release_notes": "Техноребут 1.7.0: Каталог товаров с умной сортировкой и иерархические отчёты о продажах",
     "mandatory": false
   }
   ```
3. Проверка доступности через локальный curl на VDS:
   ```bash
   # Проверка манифеста (требуется PoP или служебная проверка файла)
   cat /srv/technoreboot/data/releases/mobile/manifest.json
   ```

### Шаг 6. Canary приёмка на 1 устройстве (Samsung Galaxy S22 Ultra OWNER)
1. На физическом телефоне открыть приложение `Техноребут` (боевая версия 1.6.0).
2. Перейти в `Настройки` -> проверить баннер «Доступна новая версия: 1.7.0 (23)».
3. Нажать «Обновить» -> проверить фоновую загрузку в шторке уведомлений с прогресс-баром.
4. По завершении загрузки подтвердить системный запрос обновления пакета.
5. Запустить обновленное приложение (v1.7.0):
   - Проверить сохранение существующей авторизации и сертификата (без повторного ввода паролей).
   - Открыть вкладку **Каталог**: проверить отображение товаров, фильтрацию по брендам (приоритет HP→Kyocera→Canon→Xerox→Samsung) и сортировку по цене.
   - Открыть вкладку **Отчеты**: проверить drill-down Сегодня → чеки, Неделя → дни → чеки, Месяц → дни → чеки, Год → месяцы → дни → чеки.
   - Проверить симметричную работу кнопки «Назад» и сохранение позиции списка.
   - Проверить POS-терминал: убедиться, что сканирование штрихкодов и продажа работают штатно.

### Шаг 7. План отката (Rollback Procedure)
1. **Серверный откат**:
   - Если выявлена несовместимость API:
     ```bash
     cd /srv/technoreboot
     git checkout 460c9b1 # коммит предыдущего релиза
     docker compose up -d --build core admin-shell gateway
     ```
   - База данных не откатывается, чтобы не потерять реальные продажи и ремонты, совершенные во время работы новой версии.
2. **Клиентский откат (Android APK)**:
   - Внимание: ОС Android запрещает установку пакета с меньшим `versionCode` поверх большего.
   - Если Canary выявил критический дефект в APK v23:
     - Немедленно удалить или переименовать файл `manifest.json` на сервере, чтобы остальные устройства не получили предложение обновиться.
     - Для исправления на уже обновившемся устройстве собирается хотфикс-пакет с `versionCode = 24`, содержащий стабильный код, и публикуется в манифесте как обязательное обновление.

---

## 6. Требуемые действия владельца (OWNER Actions)

Перед запуском процесса раскатки OWNER должен предоставить/выполнить:
1. **Предоставить параметры закрытого Release Keystore** для сборки боевого APK `com.technoreboot.mobile` (v1.7.0, versionCode 23).
2. **Подтвердить время технологического окна** для перезапуска контейнеров на VDS `144.31.15.88` (~2-3 минуты кратковременной недоступности API).
3. **Выдать явную команду `OWNER GO`** на выполнение Production Rollout по составленному Release Runbook.
