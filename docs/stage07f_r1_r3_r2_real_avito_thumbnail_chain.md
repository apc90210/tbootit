# ТехноРебут: Этап 07F-R1-R3-R2 — Сквозная цепочка передачи миниатюр Avito и сверка данных

## 1. Контекст и цели этапа

В ходе аудита предыдущего этапа (07F-R1-R3-R1) были выявлены следующие ключевые проблемы:
1. **Расхождение в хронологии количества товаров**:
   - В отчете R1-R3-R1 зафиксировано 195 товаров (160 исходных + 35 восстановленных).
   - При детальном аудите обнаружено, что записи с `id=171` (`AVITO-111`) и `id=172` (`AVITO-222`) являлись тестовыми заглушками, созданными тестом `avito-module/tests/test_extension_my_listings_discovery.py` при обращении к живому сервису Core.
   - Реальных товаров Avito было ровно **33** (с `id` 296..328), а исходных товаров — **160** (с `id` 1..170). Чистое бизнес-количество товаров в базе должно составлять ровно **193**.
2. **Потеря фото при парсинге реального кабинета Avito**:
   - В `content.js` селектор `cardSelectors` содержал префиксный шаблон `[data-marker^="item-"]`, который матчил дочерние листовые элементы (например, `item-title`, `item-price`).
   - Функция `querySelectorAll` извлекала элемент заголовка без окружающего контейнера `iva-item-root`, в результате чего в карточке не находилось `<img>`, а `seenIds` помечал идентификатор объявления как уже обработанный.
   - Реальная современная верстка Avito использует разнообразные варианты рендеринга картинок: `<picture><source srcset>`, `currentSrc`, `data-src`, `data-srcset`, CSS `background-image`, а также содержит аватары продавцов и логотипы магазинов, которые не должны ошибочно попадать в фото товара.
3. **Отсутствие визуальной диагностики в попапе**:
   - Пользователь не видел, сколько фото было фактически обнаружено на открытой странице.

---

## 2. Архитектурные и технические решения

### 2.1. Сверка базы данных и изоляция тестов
- Проведен аудит записей `id=171` и `id=172`:
  - Записи создавались в функции `test_discovery_creates_product_via_extension_payload` файла `avito-module/tests/test_extension_my_listings_discovery.py`.
  - Записи `id=171` и `id=172` удалены из БД (вместе со связанными строками `product_external_listings`).
  - Тест `test_extension_my_listings_discovery.py` изолирован через `unittest.mock.patch("httpx.AsyncClient.post")`, предотвращая создание тестовых строк в рабочей БД при прогоне тестов.
  - Актуальный счетчик реальных товаров зафиксирован: **193 товара**.

### 2.2. Восхождение к контейнеру карточки (`findCardContainer`)
В `chrome-extension/technoreboot-avito/content.js`:
- Создана функция `findCardContainer(node)`, которая ищет ближайший корневой контейнер карточки:
  - Проверяет `node.closest(...)` по селекторам контейнеров карточек (`iva-item-root`, `[data-marker="item"]`, `[data-marker*="snippet"]`, `[class*="item-root"]`, `[class*="iva-item"]`, `article`, `li`, `tr`).
  - Если не найден, поднимается по родителям (до 12 уровней), пока не найдет элемент с маркером или классом карточки/сниппета.
- В функции `parseListingCardElement(cardEl, fallbackAnchor)`:
  - Перед поиском фото и атрибутов гарантированно восходит к полному контейнеру карточки: `container = findCardContainer(baseNode) || baseNode`.
  - Поиск фото и цен производится внутри контейнера `container`.
- В функции `extractMyListingsData()`:
  - Удален селектор листовых элементов `[data-marker^="item-"]`.
  - Заменена логика на словарь по идентификаторам `itemsById = new Map()`. Если повторно встречается тот же `avito_id`, запись обогащается фотографией или недостающей ценой.

### 2.3. Мульти-паттерное извлечение реальных изображений Avito
Функция поиска фото проверяет все современные варианты разметки:
1. `<picture><source srcset="...">`: парсинг `srcset`, выбор URL максимального разрешения, нормализация относительных ссылок вида `//...` в `https:...`.
2. `img.currentSrc` (активное изображение в DOM).
3. `img[data-srcset]` и `img[srcset]`.
4. `img[data-src]` и `img[data-origin-src]` (lazy-loading).
5. `img[src]`.
6. CSS `background-image` на контейнерах превью (`url(...)`).
7. **Фильтрация паразитных изображений**:
   - Исключаются элементы и URL, содержащие: `avatar`, `user-avatar`, `seller-avatar`, `user_avatar`, `logo`, `badge`, `.svg`, `data:image/svg+xml`, `placeholder`, `empty`, `blank`.

### 2.4. Диагностика в интерфейсе расширения (Popup UI)
В `chrome-extension/technoreboot-avito/popup.js` и `popup.html`:
- Добавлен блок счетчика: `Фото найдено: <span id="bulkPhotosFoundBadge" class="badge">X из N</span>`.
- Если объявлений > 0, но фото найдено 0, выводится яркий желтый/оранжевый баннер предупреждения:
  `⚠️ На странице найдено N объявлений, но ни у одного не найдено фото. Рекомендуется прокрутить страницу вниз, чтобы загрузились превью.`
- При успешном обнаружении фото бейдж подсвечивается зеленым (`badge-success`), при частичном — синим (`badge-info`).

### 2.5. Сквозная цепочка прохождения фото
Цепочка доставки изображения от карточки Avito до интерфейса ТехноРебут:
1. **DOM Avito**: `content.js` извлекает `thumbnail_url` из контейнера карточки.
2. **Фоновый скрипт**: `service_worker.js` формирует `BulkImportPayload`.
3. **Модуль Avito**: `extension_bridge.py` принимает запрос от плагина по токену сопряжения и проксирует его в Core `POST /products/bulk-avito-import`.
4. **Ядро Core**: сервис `avito_import_service.py` скачивает фото по URL (или декодирует base64), валидирует размер и Content-Type, сохраняет файл на диск в `/data/storage/product_photos/{product_id}_{hash}.jpg`, создает запись `ProductPhoto` с `sort_order = 0` и `media_url = /media/product_photos/...`.
5. **Gateway mTLS**: проксирует защищенный доступ к статическим файлам `/media/product_photos/...` (200 OK).
6. **Таблица инвентаря**: страница `/inventory/products` рендерит миниатюру `<img src="/media/product_photos/..." alt="Превью" style="width: 42px; height: 42px; ...">`.

### 2.6. Синхронизация версии 0.2.52
Версия плагина синхронно повышена до `0.2.52` во всех артефактах:
- `chrome-extension/technoreboot-avito/manifest.json`: `"version": "0.2.52"`
- `chrome-extension/technoreboot-avito/popup.html`: `v0.2.52`
- `chrome-extension/technoreboot-avito/popup.js`: `let manifestVer = "0.2.52";`, `extension_version: "0.2.52"`
- `chrome-extension/technoreboot-avito/service_worker.js`: `v0.2.52`, `extension_version = "0.2.52"`
- `chrome-extension/technoreboot-avito/content.js`: `v0.2.52`, `extension_version: "0.2.52"`
- `avito-module/app/routers/extension_bridge.py`: `default="0.2.52"`, `version="0.2.52"`
- `admin-shell/app/main.py`: `version = "0.2.52"`
- `admin-shell/app/templates/avito_extension.html`: `v0.2.52`
- Собраны дистрибутивы: `dist/technoreboot-avito-extension-0.2.52.zip` и `admin-shell/app/technoreboot-avito-extension.zip`.

---

## 3. Результаты автоматизированного тестирования

- **Core Module**: 238 passed (100%)
- **Inventory & Sales Module**: 142 passed (100%)
- **Avito Module**: 144 passed (100%)
- **Admin Shell Module**: 83 passed, 1 skipped (100%)
- **Live Gateway mTLS Verification (`scripts/verify_stage07f_r1_r3_r2_thumbnail_chain.py`)**:
  - Scenario 0: Baseline DB Audit (193 products, 0 stubs) -> PASS
  - Scenario 1: Gateway mTLS 403 unauth / 200 auth -> PASS
  - Scenario 2: Extension page & ZIP download v0.2.52 -> PASS
  - Scenario 3: Extension pairing & bridge status v0.2.52 -> PASS
  - Scenario 4: Real thumbnail ingestion chain -> PASS
  - Scenario 5: Media URL Gateway serving & preview img rendering -> PASS
  - Scenario 6: Repeat import idempotency -> PASS
  - Scenario 7: Deterministic cleanup & zero-pollution invariant -> PASS
