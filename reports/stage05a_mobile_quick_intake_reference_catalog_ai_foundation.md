# Технический отчёт: Этап 05A — Mobile Quick Product Intake, Справочный каталог и Серверный AI-фундамент

## 1. Общие сведения
- **Этап:** Stage 05A (TR_Stage05A_Mobile_Quick_Intake_Reference_Catalog_AI_Foundation_R1)
- **Контур:** LOCAL / DEV ONLY (VDS `144.31.15.88` не затрагивался)
- **Целевая функциональность:**
  1. Инвентаризация каталога моделей принтеров и МФУ (166 товаров, 70 нормализованных эталонов).
  2. Серверная абстракция AI-провайдеров (`OpenAICompatibleProvider`, `DisabledAIProvider`) с изоляцией ключей на сервере и строгой валидацией схемы спецификаций.
  3. Генератор канонических технических описаний без утечки дефектов конкретных б/у товаров.
  4. Конечная точка быстрого приёма товаров `/api/products/quick-intake` в Core и PoP-защищённый фасад в `admin-shell` (`/api/mobile/product-reference/search`, `/api/mobile/product-reference/ai-assist`, `/api/mobile/products/quick-intake`).
  5. Мобильный пользовательский интерфейс быстрого приёма `QuickIntakeScreen` в Android-приложении: фотосъёмка, живой поиск эталонов, AI-помощник, строгая изоляция особенностей б/у товара (`Особенности / примечание конкретного товара`), расчёт цены/количества и сохранение карточки.

---

## 2. Результаты аудита каталога и инвентаризации
Полная таблица инвентаризации зафиксирована в [reports/stage05a_printer_reference_catalog_inventory.md](stage05a_printer_reference_catalog_inventory.md):
- **Всего товаров в локальной БД:** 421.
- **Принтеры и МФУ:** 166 позиций (145 в наличии, 21 продано/в архиве), 160 уникальных исходных названий.
- **Нормализованные эталонные модели (`product_reference_models`):** 70 моделей (32 принтера, 38 МФУ).
- **Связано с эталонами:** 153 товара (92.2%).
- **Несвязанные позиции (13):**
  - 1 кандидат в эталоны: `HP LaserJet Enterprise M507` (1 товар).
  - 2 неоднозначных мульти-модельных объявления (`Kyocera P4100/4200`, `P2040`).
  - 7 оптовых/рекламных сборных объявлений без единой модели.
  - 3 ошибочно классифицированных комплекта/аксессуара.

---

## 3. Схема данных и аддитивные миграции
В таблицу `product_reference_models` добавлены аддитивные поля:
- `verification_state VARCHAR DEFAULT 'verified'` — статус верификации эталона (`verified`, `ai_proposed`, `unverified`).
- `source_urls_json TEXT` — JSON-массив проверенных источников документации.
- `confidence FLOAT DEFAULT 1.0` — уровень уверенности соответствия эталона.

В `core/app/main.py` миграция выполняется автоматически в `migrate_db()` при старте сервиса.
Проверка целостности локальной базы данных:
- `PRAGMA quick_check;` -> `ok`
- `PRAGMA foreign_key_check;` -> `[]` (0 нарушений целостности внешних ключей)

---

## 4. Серверный AI-фундамент и канонические спецификации
Создан пакет `core/app/services/ai/`:
- `base.py`: Базовый класс `AIProvider` и строгая структура `AIIdentificationResult`.
- `disabled_provider.py`: `DisabledAIProvider` — безопасный оффлайн-фоллбэк при отключенном AI.
- `openai_compatible.py`: `OpenAICompatibleProvider` — поддержка API Cloud.ru Evolution и Yandex Cloud AI Studio с JSON-схемой и таймаутами.
- `factory.py`: `get_ai_provider()` с чтением настроек из `app/config.py`.
- `spec_schemas.py`: Схемы технических характеристик для принтеров и МФУ, а также функция `build_canonical_description`, гарантирующая чисто техническое эталонное описание без дефектов б/у.

Ключи API хранятся исключительно на сервере в конфигурации и никогда не передаются в Android-клиент и не возвращаются в API.

---

## 5. Эндпоинты Core и Admin-Shell Facade
### Core API:
- `GET /api/product-reference/search` (и алиас `/api/product-references/search`): 3-уровневый детерминированный поиск эталонов по точным алиасам, каноническим названиям и подстрокам моделей/алиасов с ранжированием уверенности.
- `POST /api/product-reference/ai-assist`: серверный AI-ассистент для распознавания неизвестных моделей.
- `POST /api/products/quick-intake`: создание карточки товара с привязкой к эталону, изоляцией индивидуальных примечаний в `product.notes`, сохранением base64 фото в медиа-хранилище и созданием проводки `StockMovement(initial)`.

### Admin-Shell Mobile Facade (TRMOBILE1 PoP):
- `GET /api/mobile/product-reference/search?q=...`
- `POST /api/mobile/product-reference/ai-assist`
- `POST /api/mobile/products/quick-intake`
Все мобильные запросы защищены криптографической подписью ECDSA SHA-256 (с привязкой метода, канонического пути и SHA-256 тела запроса).

---

## 6. Мобильное приложение Android (`android-app`)
1. **Модели данных (`model/ProductReference.kt`):**
   - `ProductReferenceCandidate`, `ProductReferenceSearchResponse`.
   - `AiAssistResponse`.
   - `QuickIntakePhoto`, `QuickIntakeRequest`, `QuickIntakeResponse`.
2. **Сетевой клиент (`MobileApiClient.kt`):**
   - Методы `searchReferenceModels`, `requestAiAssist`, `quickIntakeProduct` с генерацией PoP заголовков в защищённом Android Keystore.
3. **Пользовательский интерфейс (`ui/intake/QuickIntakeScreen.kt`):**
   - Фотосъёмка сжатых JPEG с конвертацией в base64 (камера/галерея).
   - Живой поиск модели в каталоге с бейджами уверенности и превью характеристик.
   - Кнопка вызова AI-ассистента для распознавания неизвестных моделей.
   - Обособленное поле `Особенности / примечание конкретного товара` (дефекты, комплектность, картридж).
   - Цена продажи, количество, штрихкод и место хранения.
   - Экран успеха с показом SKU (`PRD-XXXXXXXX`) и быстрым переходом к приёму следующего товара.
4. **Навигация (`MobileApp.kt` и `SalesReportScreen.kt`):**
   - Добавлен экран `AppScreen.QUICK_INTAKE`.
   - Добавлена кнопка «Приём товара» (`Icons.Default.AddCircle`) в верхней панели главного экрана.

---

## 7. Результаты тестирования и верификации
1. **Core Unit Tests:**
   - `core/tests/test_stage05a_quick_intake_and_ai.py`: 7/7 PASSED.
   - `core/tests/test_product_reference_matcher.py`: 8/8 PASSED.
   - `core/tests/test_product_reference_api.py`: 6/6 PASSED.
   - Всего в Core: **21/21 PASSED**.
2. **Admin-Shell Facade Tests:**
   - `admin-shell/tests/test_stage05a_mobile_intake_facade.py`: 6/6 PASSED.
   - `admin-shell/tests/test_stage04a_mobile_barcode_lookup.py`: 12/12 PASSED.
   - `admin-shell/tests/test_stage04b_mobile_pos_checkout.py`: 7/7 PASSED.
   - Всего в Admin-Shell: **25/25 PASSED**.
3. **Android App Tests & Build:**
   - `.\gradlew.bat testDebugUnitTest`: BUILD SUCCESSFUL.
   - `.\gradlew.bat assembleDebug`: BUILD SUCCESSFUL (APK собран успешно).
   - `.\gradlew.bat lintDebug`: BUILD SUCCESSFUL (0 ошибок).
4. **База данных и безопасность:**
   - `PRAGMA quick_check`: ok.
   - `PRAGMA foreign_key_check`: [] (0 ошибок).
   - `scripts/verify_safety_baseline.py`: 0 нежелательных мутаций продаж/ремонтов.
   - Исторические продажи и архивные товары защищены.

---

## 8. Готовность к физической проверке Владельцем (OWNER Physical Gate)
Система готова к локальной проверке Владельцем на физическом устройстве Samsung Galaxy S22 Ultra:
1. Запуск Android приложения (`assembleDebug` готов).
2. Нажатие на зелёную иконку с плюсом «Приём товара» в верхней панели.
3. Добавление фото тестового принтера / наклейки.
4. Ввод модели `P1102w` или `M2040` -> моментальное отображение характеристик из каталога.
5. Заполнение состояния (`Б/у - хорошее`), примечания (`Картридж заправлен, тестовая печать без полос`), цены (`5500`) и количества.
6. Нажатие «Создать товар» -> получение присвоенного SKU `PRD-...`.
