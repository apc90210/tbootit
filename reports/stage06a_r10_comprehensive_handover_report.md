# Technoreboot — Комплексный отчет и Handover-документация (Stage 06A R10, v0.2.17)

## 1. Общий контекст проекта и назначение
**Technoreboot (`tbootit`)** — локальная система автоматизации сервисного центра, склада, учета запчастей и прямых розничных продаж компьютерной техники с бесшовной интеграцией торговой площадки **Avito**.

### Ключевые сервисы архитектуры (Docker Compose):
| Сервис | Стек | Внутренний порт | Назначение |
|---|---|---|---|
| **`core`** | FastAPI, SQLAlchemy, SQLite (`/data/technoreboot.db`) | `8000` | Главное ядро учета, база данных товаров (`Product`), фотографий (`ProductPhoto`), связок с площадками (`ProductExternalListing`), заказов на ремонт и динамических схем атрибутов. |
| **`admin-shell`** | FastAPI, Jinja2, Bootstrap 5 | `8011` (Host: `8011`) | Единый веб-интерфейс и Reverse Proxy для всех модулей, раздача статики, медиафайлов и скачивание плагина. |
| **`avito-module`** | FastAPI, Playwright/Chromium | `8004` | Модуль интеграции с Avito, обработчик API моста расширения (`/api/extension/*`), сессии и профили. |
| **`inventory-sales-module`** | FastAPI, HTML/JS UI | `8002` | Складской учет, корзина продаж, генерация чеков, печать гарантийных талонов и ценников. |
| **`repairs-module`** | FastAPI, HTML/JS UI | `8003` | Модуль приемки, диагностики, калькуляции и выдачи ремонтов. |
| **`chrome-extension`** | Manifest V3 (JS/HTML/CSS) | Browser Client | Клиентское расширение **«Техноребут Avito Мост» (v0.2.17)** для захвата объявлений напрямую из браузера владельца. |

---

## 2. Архитектура интеграции с Avito (Chrome Extension Flow)

```
[Пользователь на avito.ru] 
      │
      ▼
[Chrome Extension: content.js (v0.2.17)]
  ├─ 1. Autonomous Gallery Walker: кликает миниатюры ➔ извлекает 100% фото в HD (1280x960 / ra4)
  ├─ 2. DOM & Script Parser: извлекает характеристики (Модель, Бренд, Состояние и параметры)
  └─ 3. Title Fallback: распознает токены модели из заголовка
      │
      ▼ (POST /api/extension/ingest с Bearer-токеном)
[avito-module: extension_bridge.py]
  ├─ 1. Валидация payload (проверка отсутствия куков/сессий)
  ├─ 2. Сохранение ParsedAd
  └─ 3. Передача в Core API (import_service.py)
      │
      ▼ (POST /api/integrations/avito/import-item)
[core: integrations.py]
  ├─ 1. Создание / обновление Product (brand, model, condition, SKU, sale_price)
  ├─ 2. Upsert ProductExternalListing (внешний ID и URL объявления)
  ├─ 3. Динамическая схема атрибутов: upsert_avito_category_schema & upsert_product_avito_attributes
  └─ 4. Idempotent Photo Ingestion & Quality Reconciliation (загрузка байт, SHA256, удаление старых low-res превью)
```

---

## 3. Ключевые файлы и их ответственность

1. **`chrome-extension/technoreboot-avito/content.js`**:
   - `walkAndCollectAllGalleryPhotos()`: Автоматически обходит все элементы галереи (`ul[data-marker="gallery/list"] li`, стрелки слайдера), инициируя события `click` / `pointerdown` для монтирования полноразмерных картинок в React DOM.
   - `extractAllPhotos(jsonLd, extraPhotos)`: Собирает ссылки из JSON-LD, `__initialData__`, DOM и результатов активного обхода; группирует по каноническому идентификатору и выбирает вариант наивысшего качества.
   - `getCanonicalAvitoImageIdentity(url)`: Извлекает уникальный хэш-токен изображения без искажения подписанных параметров Avito CDN.
   - `extractCharacteristicsFromDom()`: Извлекает пары ключ-значение параметров Avito (включая слитный текст `<span>Модель</span>H510M...` без двоеточий) и фильтрует статистику просмотров/расходов.
   - `extractListingData(extraPhotos)`: Формирует итоговый JSON-объект карточки объявления с fallback-распознаванием модели из заголовка.

2. **`chrome-extension/technoreboot-avito/popup.js`**:
   - Отвечает за привязку расширения по PIN-коду (`pair_code`), отображение реального статуса подключения и сканирования HD-фотографий (`Обнаружено фото: N (все в HD) ✓`).
   - Перед нажатием кнопки «Передать в Техноребут» выполняет предварительный глубокий скан (`deepScan: true`), гарантируя отправку 100% фотографий в максимальном качестве.

3. **`avito-module/app/routers/extension_bridge.py` & `app/services/import_service.py`**:
   - Прием и валидация входящих данных от расширения.
   - Сопоставление полей: `brand` (`Производитель` || `Бренд` || `Марка`), `model` (`Модель`), `condition` (`Состояние`).

4. **`core/app/routers/integrations.py`**:
   - Эндпоинт `/api/integrations/avito/import-item`.
   - Запись товара в таблицу `Product`, связки в `ProductExternalListing`.
   - Скачивание файлов фотографий в `/data/product_photos/`, хэширование SHA256, создание записей `ProductPhoto`.
   - Автоматическая сверка (reconciliation) набора фотографий: при повторной передаче удаляет старые превью низкого качества, если пришли новые HD-фото.

5. **`core/app/services/avito_schema_service.py`**:
   - Динамическое создание категорий `AvitoCategorySchema` и атрибутов `ProductAttributeValue` на основе переданных характеристик.

6. **`admin-shell/app/main.py` & `app/templates/avito_extension.html`**:
   - Страница `/avito/extension` и эндпоинт скачивания `/avito/extension/download`, отдающий актуальный архив плагина с заголовками `Cache-Control: no-store`.

---

## 4. Решенные проблемы в последних итерациях (Changelog)

- **v0.2.12 (Commit `143abc1`)**: Устранен сбой с самопроизвольным редиректом на личный кабинет Avito.
- **v0.2.13 (Commit `5265d67`)**: Решена проблема серой/неактивной кнопки передачи — реализована автоматическая динамическая инъекция `content.js` через `chrome.scripting`.
- **v0.2.14 (Commit `006900f`)**: Исправлена очистка характеристик от мусорных параметров (показы, просмотры, контакты, расходы на продвижение).
- **v0.2.15 (Commit `bf5f537`)**: Устранена ошибка передачи только одной фотографии:
  - Выявлено, что URL Avito CDN содержат криптографически подписанные токены (мутация `ra1` -> `ra4` возвращала 400 Bad Request от CDN).
  - Сняты деструктивные мутации URL, исправлена каноническая группировка, которая ранее обрезала токены до 5 символов.
- **v0.2.16 (Commit `74da4ec`)**: 
  - Исправлен парсинг `window.__initialData__` из тегов `<script>` без повреждения кавычек.
  - Исправлено извлечение модели материнских плат (например, `H510M-H2/M.2 SE`) при отсутствии двоеточия в HTML.
  - Расширено сохранение `brand` и `model` в `core` и `avito-module`.
- **v0.2.17 (Commit `a5f21af`)**: 
  - Разработан и внедрен **автономный обходчик галереи (`walkAndCollectAllGalleryPhotos`)**, который автоматически прокликивает все слайды объявления, заставляя React отрендерить 100% фотографий в оригинальном Full HD разрешении (`1280x960`).

---

## 5. Текущее состояние и проверка качества

- **Общее количество тестов:** **544 теста**
  - `core/tests`: **192 passed**
  - `avito-module/tests`: **83 passed**
  - `admin-shell/tests`: **54 passed**
  - `chrome-extension/technoreboot-avito/tests`: **18 passed**
  - `inventory-sales-module` & `repairs-module`: **197 passed**
  - **Итог: 100% PASS (0 failures, 0 errors)**
- **Состояние контейнеров Docker:** Все сервисы собраны и находятся в статусе `Healthy`/`Running`.
- **Git статус:** Рабочее дерево чистое, ветка `main` синхронизирована с `origin/main`.

---

## 6. Рекомендации и открытые задачи для следующей нейросети

1. **Массовый экспорт и выгрузка на Avito (Stage 06B / 07):**
   - Реализовать обратный поток: публикация оприходованных или отремонтированных товаров из базы Technoreboot на Avito.
2. **Печать ценников с фото:**
   - В модуле `inventory-sales-module` использовать импортированные фотографии товаров (`ProductPhoto.media_url`) для визуального отображения на термоэтикетках и ценниках.
3. **Автоматическое списание запчастей при ремонте:**
   - Связать модуль ремонтов `repairs-module` со складом `Product` при использовании комплектующих (материнские платы, матрицы, накопители, оперативная память).
