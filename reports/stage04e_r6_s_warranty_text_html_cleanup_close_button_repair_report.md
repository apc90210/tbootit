# Stage 04E-R6-S Warranty Text HTML Cleanup and Close Button Repair Report

## STATUS

READY_FOR_OWNER_RECHECK

## OWNER_REPORTED_FAIL

Владелец сообщил, что в тексте гарантии отображаются служебные символы `<br>`, а кнопка «Закрыть» на странице чека не работает.

## ROOT_CAUSE

- **Stored HTML br**: Текст гарантии был сохранён в БД со вставками `<br>`.
- **Template rendering**: В `sale_receipt_preview.html` использовался фильтр `|replace('\n', '<br>')`, и из-за отсутствия `|safe` (в ветке с гарантией) HTML выводился текстом. Кроме того, исходный текст содержал явные `<br>`.
- **Close button**: Кнопка закрыть использовала только `window.close()`, что не работает в современных браузерах для вкладок, открытых не через JS.

## FIXES

### Plain text normalization
В модулях `core` и `inventory-sales-module` (`defaults.py`) создана функция `normalize_multiline_text()`, которая заменяет теги `<br>` на символы перевода строки `\n`. Функция автоматически применяется при загрузке (backfill/fallback) и обновлении (PUT /api/settings/organization).

### Settings textarea rendering
Текст отображается как plain text. Любые сохраненные `<br>` автоматически заменяются на обычные переводы строк при чтении из API.

### Receipt safe multiline rendering
В `sale_receipt_preview.html` удалена логика с заменой на `<br>`. Текст оборачивается в блок с CSS-свойством `white-space: pre-line;`, которое безопасно переносит строки.

### Close button fallback
Кнопка закрытия чека переписана на:
`onclick="window.history.length > 1 ? window.history.back() : window.location.href='/sales'"`
Это обеспечивает надежный возврат к странице продажи.

## TESTS

Core: PASS (49 tests) - Добавлен тест на нормализацию HTML при PUT-запросе и GET.
Inventory: PASS (30 tests) - Добавлены тесты на отсутствие тегов `<br>` в генерируемом HTML (чеке) и в fallback-настройках, а также проверка наличия `history.back` в кнопке закрытия.
Avito: PASS (12 tests)

## MANUAL_SMOKE

Settings page: Не содержит тегов `<br>`, текст выводится построчно.
Receipt warranty: Обычный текст с правильным переносом строк, без служебных символов.
Receipt no-warranty: Обычный текст, переносится корректно.
Close button: Возвращает назад или переходит к `/sales`.

## SAFETY_SCAN

Runtime tracked: Clean
Direct DB access: Clean
Destructive DB calls: Clean (existing admin endpoint and tests excluded)
Secrets: Clean

## FILES_CHANGED

- core/app/defaults.py
- core/app/routers/settings.py
- core/tests/test_organization_settings_defaults.py
- inventory-sales-module/app/defaults.py
- inventory-sales-module/app/templates/sale_receipt_preview.html
- inventory-sales-module/tests/test_organization_settings_defaults_ui.py
- inventory-sales-module/tests/test_receipt_organization_and_warranty_text.py

## COMMIT

Targeted commit with message: "Repair warranty text rendering and receipt close button"

## PUSH

Done.

## OWNER_RECHECK_GUIDE

Check `http://127.0.0.1:8030/settings/organization` and review sales receipts at `http://127.0.0.1:8030/sales/1/receipt` if a sale exists. The texts should look normal without tags. Press "Закрыть".

## FINAL_STATUS

TECHNOREBOOT_STAGE04E_R6_S_WARRANTY_TEXT_HTML_CLEANUP_CLOSE_BUTTON_READY_FOR_OWNER_RECHECK
OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
