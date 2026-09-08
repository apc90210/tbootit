# Документация: Исправление обнаружения фотографий в расширении Avito (Stage 07B-R5-R2)

## 1. Описание проблемы

При открытии любого объявления на Avito (`https://www.avito.ru/...`) всплывающее окно (popup) Chrome-расширения отображало:
```text
Обнаружено фото: 0 (сканирование HD...)
```
и после завершения сканирования:
```text
Обнаружено фото: 0 (все в HD) ✓
```
В результате расширение не обнаруживало фотографии объявления и передавало товар в систему учета Техноребут без фотографий (`photos: []`).

---

## 2. Диагностика и корневая причина (Root Cause)

1. **Фатальная ошибка `ReferenceError: triggerInitialDataCapture is not defined` в `content.js`:**
   - В коммите `166e771` из начала файла `content.js` были случайно удалены строки объявления `let pageInitialData = null;` и функции `function triggerInitialDataCapture() { ... }`.
   - В функции `extractPhotosFromEmbeddedState()` (строка 438) вызывалась `triggerInitialDataCapture()`.
   - В браузере вызов необъявленной функции мгновенно приводил к `Uncaught ReferenceError: triggerInitialDataCapture is not defined`.
   - В функции `extractAllPhotos()` вызов `extractPhotosFromEmbeddedState()` падал с ошибкой до того, как код доходил до сбора фото из DOM (`extractPhotosFromDom()`).
   - В функции `extractListingData()` блок `try { photos = extractAllPhotos(...); } catch (e) {}` перехватывал исключение, оставляя массив `photos = []` (0 фото).
   - В функции глубокого сканирования `extractListingDataMultiPass()` строка 1264 также вызывала `triggerInitialDataCapture()`, приводя к повторному падению и аварийному возврату 0 фото.

2. **Экранированные URL в JSON тегах `<script>` (Next.js / SSR):**
   - В современных версиях Avito данные передаются в скриптах с экранированием слэшей: `https:\/\/10.img.avito.st\/image\/...` или `\u002F`.
   - Регулярное выражение `match(/https?:\/\/[a-zA-Z0-9_\-\.]*img\.avito\.st\/[^\s"'\\]+/g)` не могло сопоставить такие URL из-за символа `\`.

3. **Ложные срабатывания фильтра исключений DOM (`isInsideExcluded`):**
   - Если верстка Avito оборачивала блок галереи в контейнер с атрибутами продавца (`data-marker*="seller"`), функция `isInsideExcluded` ошибочно исключала элементы галереи.

4. **Отсутствие сквозного полностраничного резервного поиска:**
   - При любых нестандартных изменениях DOM-структуры Avito отсутствовал гарантированный fallback, сканирующий весь HTML документа.

---

## 3. Внесенные исправления

### 3.1. Восстановление `pageInitialData` и безопасной функции `triggerInitialDataCapture`
В начало `chrome-extension/technoreboot-avito/content.js` добавлено:
- Объявление переменной `let pageInitialData = null;`.
- Регистрация слушателя событий `document.addEventListener('TechnorebootInitialData', ...)`.
- Определение защищенной функции `triggerInitialDataCapture()`, инжектирующей скрипт для чтения `window.__initialData__` / `__INITIAL_STATE__` / `__state__` из главного контекста страницы.
- Все вызовы `triggerInitialDataCapture()` обернуты в безопасные проверки `typeof triggerInitialDataCapture === 'function'` и блоки `try / catch`.

### 3.2. Разименование и парсинг JSON в тегах `<script>`
В `extractPhotosFromEmbeddedState()`:
- Добавлено разименование экранированных символов: `.replace(/\\u002F/ig, '/').replace(/\\\//g, '/')`.
- Добавлен прямой парсинг тегов `<script type="application/json">` и `<script id="__NEXT_DATA__">`.
- Регулярное выражение теперь безупречно находит все ссылки на CDN `img.avito.st` в скриптах страницы.

### 3.3. Приоритетная защита галереи от исключения
В `isInsideExcluded` и обходчике миниатюр добавлен безусловный приоритет:
```javascript
if (el.closest('[data-marker*="gallery"], [data-marker*="image-frame"], [data-marker*="item-view/gallery"], [data-marker="item-view/main"], .gallery-root, [class*="gallery-"], [class*="image-frame"]')) {
    return false; // Никогда не исключать элементы галереи
}
```

### 3.4. Полностраничный аварийный сканер (Full-Page HTML Fallback)
В `extractAllPhotos`:
- Все подотделы сбора (JSON-LD, Embedded State, DOM Gallery, Walker) изолированы в отдельные `try / catch`.
- Если ни один селектор не сработал (`rawUrls.length === 0`), выполняется полностраничный regex-поиск по `document.documentElement.innerHTML` для гарантированного извлечения всех фотографий `img.avito.st`.

### 3.5. Группировка вариантов разрешений одной фотографии
В `getCanonicalAvitoImageIdentity`:
- Добавлен разбор идентификаторов версий разрешения вида `[prefix][letter]a[digit]` (например, `sePk6ba4...` в HD и `sePk6ra1...` в миниатюре). Обе версии теперь получают единый канонический ключ `avito_photo_sePk6`, и алгоритм отбирает наивысшее разрешение (1280x960 HD), исключая дубликаты.

### 3.6. Повышение версии расширения до `0.2.44`
- Обновлен `manifest.json`: `"version": "0.2.44"`.
- Обновлены версии в ответах `content.js` и `popup.js`.
- Обновлены шаблоны `admin-shell/app/templates/avito_extension.html` и роут загрузки `admin-shell/app/main.py`.
- Собраны и верифицированы архивы:
  - `dist/technoreboot-avito-extension-0.2.44.zip`
  - `admin-shell/app/technoreboot-avito-extension-0.2.44.zip`
  - `admin-shell/app/technoreboot-avito-extension.zip`

---

## 4. Инструкция для владельца по обновлению расширения

1. **В браузере Chrome:**
   - Откройте вкладку `chrome://extensions`.
   - В правом верхнем углу убедитесь, что включен **«Режим разработчика»** (Developer mode).
   - Найдите карточку **«Техноребут Avito Мост»**.
   - Если расширение установлено из папки: нажмите кнопку **«Обновить»** (круг со стрелкой) на карточке расширения.
   - Если расширение устанавливалось из ZIP-архива:
     1. Скачайте обновленный архив по ссылке со страницы Админ-панели:
        `https://127.0.0.1:8443/avito/extension` (кнопка «Скачать расширение (ZIP, v0.2.44)»)
        или напрямую `http://127.0.0.1:8011/avito/extension/download`.
     2. Распакуйте архив в удобную папку.
     3. На странице `chrome://extensions` нажмите **«Загрузить распакованное расширение»** и укажите распакованную папку.

2. **Проверка работы на Avito:**
   - Откройте любое объявление на `avito.ru`.
   - Откройте popup расширения (иконка Техноребут на панели расширений).
   - Убедитесь, что отображается:
     `Обнаружено фото: N (все в HD) ✓` (где N > 0, например 5, 8, 12).
   - Нажмите **«Передать объявление в Техноребут»**.
   - Убедитесь, что товар успешно создается, а все фотографии сохраняются на сервере и отображаются в карточке товара Техноребут.
