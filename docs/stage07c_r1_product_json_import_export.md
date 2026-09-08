# Спецификация и архитектура: Stage 07C-R1 — Канонический JSON импорт/экспорт товаров и генератор AI-промпта

## 1. Назначение и контекст

Этап **Stage 07C-R1** внедряет стандартизированный, устойчивый к ошибкам веб-механизм пакетного и штучного импорта/экспорта товаров через JSON, а также встроенный генератор системных промптов для нейросетей (ChatGPT, Claude, Gemini, DeepSeek и др.).

### Ключевые требования:
1. **Единый канонический версионированный формат JSON (`technoreboot-products`, `version: 1`):**
   - Используется как для одиночного добавления товара, так и для массовой загрузки каталога.
   - Поддерживает базовые свойства (название, категория, бренд, модель, цены, остатки, описание, локация, штрихкод) и динамические характеристики (`characteristics`), совместимые со схемой Авито (`upsert_avito_category_schema` и `upsert_product_avito_attributes`).
   - Массив фотографий `photos` является полностью опциональным (`[]` или отсутствует).
2. **Безопасная политика дубликатов и обновлений:**
   - Если указан `id` и товар существует в базе данных — выполняется **обновление** (`UPDATE`).
   - Если указан `id`, но товар отсутствует — запись **пропускается** с понятной ошибкой (`Товар с ID ... не найден`).
   - Если `id` не указан, но передан существующий в базе `sku` — запись **пропускается** во избежание случайной перезаписи (`Товар с артикулом '...' уже существует (укажите 'id' для обновления)`).
   - Если `id` не указан и `sku` новый или отсутствует — создается **новый товар** (`CREATE`) с генерацией уникального `sku` (`PRD-YYYYMMDD-XXXXXX`).
3. **Сохранение целостности (Round-trip Fidelity):**
   - Полный цикл `Technoreboot -> Экспорт JSON -> Редактирование -> Импорт JSON -> Technoreboot` сохраняет все общие поля и специфические характеристики категорий без потерь.
4. **Русскоязычный Web UI в панели управления (`admin-shell` по адресу `/products/json`):**
   - **Секция A (Генератор AI-промпта):** готовый подробный русскоязычный системный промпт с правилами форматирования и примерами для нейросетей. Кнопки `[ Скопировать промпт ]` и `[ Скачать prompt.txt ]`.
   - **Секция B (Импорт JSON):** загрузка файла (`.json`) методом Drag-and-drop или вставка текста из буфера обмена. Кнопка `[ Импортировать товары ]`. Мгновенная визуальная сводка: Создано (зеленый), Обновлено (синий), Пропущено с ошибкой (красный), и подробная таблица результатов построчно.
   - **Секция C (Экспорт JSON):** кнопка `[ Экспортировать все товары в JSON ]` со скачиванием файла с временной меткой `TECHNOREBOOT_PRODUCTS_YYYY-MM-DD_HHMMSS.json`.
5. **Полное отсутствие требований к CLI для Владельца:** все действия выполняются на 100% через веб-браузер.

---

## 2. Формат данных: Каноническая схема v1 (`technoreboot-products`)

```json
{
  "format": "technoreboot-products",
  "version": 1,
  "products": [
    {
      "id": 105,
      "sku": "PRD-20260908-ABC123",
      "title": "Ноутбук Lenovo ThinkPad T480",
      "category": "Ноутбуки",
      "brand": "Lenovo",
      "model": "ThinkPad T480",
      "price": 25000.0,
      "purchase_price": 15000.0,
      "condition": "Б/у",
      "status": "in_stock",
      "quantity": 1,
      "description": "Корпоративный ноутбук в отличном состоянии.",
      "storage_location": "Склад 1",
      "barcode": "460000000001",
      "characteristics": {
        "Процессор": "Intel Core i5-8250U",
        "Оперативная память": "16 ГБ",
        "Объем накопителя": "512 ГБ SSD",
        "Диагональ экрана": "14\""
      },
      "photos": []
    }
  ]
}
```

### Правила полей:
- `format`: строковая константа `"technoreboot-products"`.
- `version`: целое число `1`.
- `products`: непустой массив объектов товаров.
- `title`: обязательное непустое строковое название товара.
- `price`: число >= 0 (цена продажи).
- `purchase_price`: опциональное число >= 0 (закупочная цена).
- `quantity`: опциональное целое число >= 0 (по умолчанию 1).
- `characteristics`: плоский словарь ключ-значение строк для категорийных характеристик (процессор, RAM, тип печати и т.д.).
- `photos`: опциональный массив URL/путей фото (может быть пустым или отсутствовать).
- Обратная совместимость: одиночные карточки формата `{"source": "chatgpt", "product": {...}}` автоматически нормализуются к канонической схеме.

---

## 3. Архитектура эндпоинтов

```mermaid
graph TD
    subgraph Browser [Браузер Владельца]
        UI[/products/json - Web UI]
    end

    subgraph AdminShell [Admin Shell :8010]
        AdminPage[GET /products/json]
        AdminPromptAPI[GET /admin-api/products/json/prompt.txt]
        AdminImportAPI[POST /admin-api/products/json/import]
        AdminExportAPI[GET /admin-api/products/json/export]
    end

    subgraph Core [Technoreboot Core :8000]
        CoreSchemaAPI[GET /api/products/json/schema]
        CoreImportAPI[POST /api/products/json/import]
        CoreExportAPI[GET /api/products/json/export]
        Service[app/services/product_json_service.py]
        DB[(SQLite technoreboot.db)]
    end

    UI -->|Render HTML| AdminPage
    UI -->|Download Prompt| AdminPromptAPI
    AdminPromptAPI -->|generate_ai_prompt| CoreSchemaAPI
    UI -->|Upload JSON / Paste Text| AdminImportAPI
    AdminImportAPI -->|Proxy payload| CoreImportAPI
    CoreImportAPI --> Service
    Service -->|upsert products & attributes| DB
    UI -->|Export Click| AdminExportAPI
    AdminExportAPI -->|Fetch full JSON| CoreExportAPI
    CoreExportAPI --> Service
    Service -->|Query all products & attributes| DB
```

---

## 4. Защита маршрутизации в Admin Shell

В `admin-shell/app/main.py` маршрут страницы `GET /products/json` размещен **строго до** динамического маршрута `GET /products/{product_id}`.
Это предотвращает перехват веб-страницы роутером редиректа на складской модуль и исключает ошибку валидации пути `422 Unprocessable Entity`.
