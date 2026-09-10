# Документация: Этап 07F-R1-R3 — Точность извлечения полей Avito, сохранение миниатюр, колонка превью и очистка тестовых данных

## 1. Контекст и цели этапа

На этапе **Stage 07F-R1-R3** решены ключевые проблемы качества легковесного импорта объявлений из профиля продавца Avito в каталог ТехноРебут:
1. **Устранение контаминации цен номерами моделей:** В предыдущей реализации `parseListingCardElement` использовался широкий regex-фоллбэк по всему тексту карточки, из-за чего цифры из названия модели (например, `HP LaserJet P2055`, `1022`, `E3-1220`) попадали в цену (`20553500 ₽` вместо `3500 ₽`).
2. **Извлечение, загрузка и персистентное сохранение миниатюр:** Карточка объявления содержит превью-фотографию. Теперь миниатюра загружается и сохраняется в каноническое постоянное хранилище (`/media/product_photos/`) как полноправная `ProductPhoto` с `sort_order = 0` (главное фото).
3. **Идемпотентность фотографий:** Если у товара уже есть фотографии (ручные или полная галерея после дообогащения), повторный массовый импорт не удаляет, не переупорядочивает и не заменяет фото низкокачественной миниатюрой. При отсутствии фото миниатюра добавляется.
4. **Отображение превью в таблице товаров (`products.html`):** В таблицу списка товаров добавлена колонка «Фото». При наличии главного фото отображается миниатюра `42x42`, при отсутствии — дефис `—`.
5. **Очистка синтетических тестовых данных Stage07F:** Выявлено и удалено 123 синтетических товара с префиксом `live_07f_*` / `AVITO-live_07f_*`, 0 реальных товаров затронуто.
6. **Инвариант очистки будущих live-тестов:** Введена обязательная очистка в блоке `finally`:
   `product_count_after_live_test == product_count_before_live_test`.
7. **Повышение версии расширения до `0.2.51`:** Синхронно обновлена версия расширения во всех манифестах, скриптах, шаблонах и дистрибутивах.

---

## 2. Архитектурные и алгоритмические изменения

### 2.1. Изоляция цены в `chrome-extension/technoreboot-avito/content.js`

В функции `parseListingCardElement(container)` реализована строгая многоуровневая стратегия извлечения цены:
1. **Уровень 1 (Мета-данные):** `meta[itemprop="price"]` — точное машинное значение от Avito (наивысший приоритет).
2. **Уровень 2 (Выделенный элемент цены):** Поиск специализированных селекторов:
   `[data-marker*="price"]`, `[data-marker="item-price"]`, `span[class*="price-text"]`, `[class*="price-root"]` и др.
   Применение строгого регулярного выражения:
   ```javascript
   /(?:^|[^\d])(\d{1,3}(?:[\s\u00A0]\d{3})*|\d+)\s*(?:₽|руб\.?|rub)/i
   ```
   Данное выражение сопоставляет **только группу цифр, непосредственно предшествующую знаку валюты**, отсекая любые предшествующие символы и цифры моделей.
3. **Уровень 3 (Узкий листовой фоллбэк):** Поиск только среди листовых текстовых узлов, содержащих символ `₽` или `руб`, исключая элементы заголовка и названия товара. Если валидное значение не найдено, возвращается `null` (resilient handling).

### 2.2. Извлечение миниатюры карточки в `content.js`

Введена функция фильтрации и извлечения превью-фотографии:
- Игнорируются аватары, логотипы, бейджи продавцов (`avatar`, `badge`, `seller`, `logo`).
- Проверяются атрибуты по приоритету: `currentSrc` -> `data-src` -> `data-origin-src` -> `src` -> `srcset` -> тег `<picture> <source>` -> `background-image`.
- URL отдается как `photo_url` и `thumbnail_url`.

### 2.3. Персистентное сохранение и идемпотентность в `core/app/routers/integrations.py`

1. Распознавание массового импорта (`is_bulk_import`):
   - Если `payload.raw_source_data.get("bulk_import")` или `payload.description is None`.
2. Правила идемпотентности фото:
   - Если у товара `existing_photos_count > 0`: массовый импорт пропускает добавление фото (`photos_skipped += len(...)`, `effective_photos = []`), не переупорядочивает и не перезаписывает существующие фото.
   - Если `existing_photos_count == 0`: берется первая доступная миниатюра, скачивается байтовое содержимое, сохраняется в постоянный каталог `/data/product_photos/{product_id}_{uuid}.jpg`, создается запись `ProductPhoto(sort_order=0, media_url="/media/product_photos/...")`.
3. Защита галереи от усечения:
   - Сверка (reconciliation) удаляет устаревшие Avito-фото **только** при детальном импорте карточки (`if not is_bulk_import and len(payload.photos) > 0:`). Массовый импорт никогда не запускает сверку и не стирает существующие фотографии.
4. Исправление некорректных цен:
   - При повторном импорте объявления обновляется тот же товар (`ProductExternalListing` находит существующий `Product`), корректируется `sale_price` и `source_price`, дубликат товара не создается.

### 2.4. Колонка превью в `inventory-sales-module/app/templates/products.html`

- В шапку таблицы добавлен заголовок `<th style="width: 50px; text-align: center;">Фото</th>`.
- В каждую строку добавлена ячейка:
  ```html
  <td style="text-align: center; vertical-align: middle; padding: 4px;">
      {% if item.main_photo_url %}
          {% set img_url = item.main_photo_url if item.main_photo_url.startswith('/') else '/' ~ item.main_photo_url %}
          <a href="/inventory/products/{{ item.id }}" title="Открыть товар">
              <img src="{{ img_url }}" alt="Превью" style="width: 42px; height: 42px; object-fit: cover; border-radius: 4px; border: 1px solid #cbd5e1; display: inline-block;">
          </a>
      {% else %}
          <span style="color: #94a3b8;">—</span>
      {% endif %}
  </td>
  ```
- Свойство `main_photo_url` вычисляется динамически из связанных `ProductPhoto` (с минимальным `sort_order`).

### 2.5. Очистка синтетических тестовых данных

- Создан полный резервный снапшот БД: `data/db/technoreboot.db.bak_before_cleanup_20260910`.
- В базе идентифицировано и безопасно удалено 123 синтетических тестовых товара `live_07f_*` и поврежденные записи текущей сессии (ID >= 171).
- 100% реальных и базовых фикстурных товаров сохранены (включая фикстуру ID=58).
- В скрипты live-верификации внедрен строгий инвариант:
  ```python
  assert product_count_after == product_count_before
  ```

### 2.6. Синхронизация версии `0.2.51`

Версия плагина повышена до **`0.2.51`** во всех манифестах, скриптах, шаблонах и сборках:
- `chrome-extension/technoreboot-avito/manifest.json`: `"version": "0.2.51"`
- `chrome-extension/technoreboot-avito/popup.html`: `v0.2.51`
- `chrome-extension/technoreboot-avito/popup.js`: `manifestVer = "0.2.51"`, `extension_version: "0.2.51"`
- `chrome-extension/technoreboot-avito/service_worker.js`: `v0.2.51`, `extension_version = "0.2.51"`
- `chrome-extension/technoreboot-avito/content.js`: `v0.2.51`, `extension_version: "0.2.51"`
- `avito-module/app/routers/extension_bridge.py`: `extension_version: str = "0.2.51"`, `version: "0.2.51"`
- `admin-shell/app/main.py`: `version = "0.2.51"`
- `admin-shell/app/templates/avito_extension.html`: `Скачать расширение (ZIP, v0.2.51)`
- Собраны архивы `dist/technoreboot-avito-extension-0.2.51.zip` и `admin-shell/app/technoreboot-avito-extension-0.2.51.zip`.

---

## 3. Результаты тестов

- **Core Module:** 238 passed (100%)
- **Avito Module:** 126 passed (100%)
- **Admin Shell:** 83 passed, 1 skipped (100%)
- **Inventory Sales Module:** 142 passed (100%)
- **Live Gateway mTLS Verification:** Все 6 сценариев пройдены успешно, инвариант `count_after == count_before` строго соблюден.
- **Общий итог:** 589 пройденных модульных и интеграционных тестов.
