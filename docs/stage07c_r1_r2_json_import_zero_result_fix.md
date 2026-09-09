# Документация: Stage 07C-R1-R2 — Исправление ложного успеха импорта JSON ("Создано: 0, обновлено: 0, ошибок: 0")

## 1. Контекст и описание дефекта

При выполнении реального импорта двух товаров в каноническом формате JSON через веб-интерфейс панели управления `/products/json` Владелец получил вводящий в заблуждение статус:
```text
✓ Импорт успешно завершён! Создано: 0, обновлено: 0, ошибок: 0.
```
При этом переданный JSON-файл содержал 2 валидных товара (монитор Dell P2419H и ноутбук HP ProBook 450 G6) без явных `id` и `sku`, которые согласно политике дубликатов должны были быть созданы в базе данных как новые позиции (`Создано: 2`).

---

## 2. Доказанная первопричина (Root Cause Analysis)

Расследование и захват сквозного контракта запроса/ответа выявили:

1. **Запрос от браузера:**
   `POST /admin-api/products/json/import` с телом:
   ```json
   {
     "format": "technoreboot-products",
     "version": 1,
     "products": [
       {"title": "Монитор Dell P2419H 24\" Full HD", ...},
       {"title": "Ноутбук HP ProBook 450 G6 15.6\"", ...}
     ]
   }
   ```
2. **Прокси Admin Shell -> Core API:**
   Admin Shell пересылает `POST http://core:8000/api/products/json/import` с тем же телом.
3. **Ответ Core API:**
   Core API фактически **создавал** оба товара в базе данных (`imported_product_ids: [154, 155]`), но возвращал ответ в плоском формате:
   ```json
   {
     "success": true,
     "created_count": 2,
     "updated_count": 0,
     "skipped_count": 0,
     "errors": [],
     "imported_product_ids": [154, 155]
   }
   ```
4. **Несоответствие ключей во Frontend UI (`products_json.html`):**
   Функция `renderImportResults(data)` в браузере считывала вложенный объект `data.summary` и детальный массив строк `data.results`:
   ```javascript
   const summary = data.summary || {
       total_in_payload: 0,
       created: 0,
       updated: 0,
       skipped: 0
   };
   ```
   Поскольку `data.summary` и `data.results` отсутствовали в ответе бэкенда, JavaScript:
   - Применил значения по умолчанию: `created = 0`, `updated = 0`, `skipped = 0`.
   - Проверил условие `summary.skipped > 0` (0 > 0 — `false`).
   - Перешел в ветку `else`, отобразив зеленую плашку успеха:
     *«✓ Импорт успешно завершён! Создано: 0, обновлено: 0, ошибок: 0.»*
   - Оставил детальную таблицу пустой (так как `data.results` был `undefined`).

---

## 3. Архитектурные исправления

### 3.1. Technoreboot Core (`core/app/services/product_json_service.py`)
1. **Структурированный ответ со сводкой и детальными результатами:**
   Ответ `import_canonical_products` теперь включает как вложенный объект `summary`, так и поэлементный массив `results`:
   ```python
   summary = {
       "total_in_payload": total_in_payload,
       "total": total_in_payload,
       "created": created_count,
       "updated": updated_count,
       "skipped": skipped_count,
       "errors": error_count
   }
   ```
   Каждая строка в `results` содержит:
   `{"index": idx + 1, "id": prod_id, "sku": sku, "title": title, "status": "created" | "updated" | "skipped" | "error", "error": err_str}`.
2. **Строгий инвариант учета (Accounting Invariant):**
   ```python
   created_count + updated_count + skipped_count + error_count == total_in_payload
   ```
   Ни один товар из непустого пакета не может потеряться при обработке.
3. **Защита от ложного успеха:**
   Если непустой входной пакет дал нулевое количество обработанных элементов (`total_processed == 0`), операция откатывается (`db.rollback()`), возвращая `success=False` и понятное сообщение об ошибке.
4. **Обратная совместимость:**
   Сохранены корневые поля `created_count`, `updated_count`, `skipped_count`, `errors`, `imported_product_ids`.

### 3.2. Пользовательский интерфейс (`admin-shell/app/templates/products_json.html`)
1. **Все 4 класса исходов:**
   В блоке статистики отображаются 5 карточек:
   - `Всего в пакете` (`#statTotal`)
   - `Создано` (`#statCreated`)
   - `Обновлено` (`#statUpdated`)
   - `Пропущено` (`#statSkipped`)
   - `Ошибок` (`#statErrors`)
2. **Защита от отображения ложного зеленого успеха:**
   Если `totalInPayload > 0` и все счетчики равны нулю, выводится красное сообщение об ошибке, а не зеленый баннер успеха.
3. **Устойчивое извлечение данных:**
   JavaScript использует цепочку fallback-значений (`rawSummary.created ?? data.created_count ?? 0`).
4. **Детальная таблица:**
   Отображает бейджи (`СОЗДАН`, `ОБНОВЛЕН`, `ПРОПУЩЕН`, `ОШИБКА`), ID, SKU, название и статус/ошибку для каждой строки.

---

## 4. Верификация на эталонном пакете Владельца

На эталонном пакете из 2 товаров (Dell P2419H и HP ProBook 450 G6):
- **Сводка:** `Всего: 2, Создано: 2, Обновлено: 0, Пропущено: 0, Ошибок: 0`.
- **Инвариант:** `2 + 0 + 0 + 0 == 2`.
- **Сохранение полей:**
  - Монитор Dell: диагональ 24", IPS, 1920x1080, 60 Гц, разъемы, локация «Витрина», цены 8500 / 5000.
  - Ноутбук HP: Core i5-8265U, 8 ГБ RAM, 256 ГБ SSD, Intel UHD 620, экран 15.6", Windows 10 Pro, локация «Склад 1», цены 24500 / 15500.
- **Оба пути ввода:** Загрузка файла (`.json`) и вставка текста в текстовое поле (`textarea`) используют один и тот же канонический сервис и дают идентичный результат.
