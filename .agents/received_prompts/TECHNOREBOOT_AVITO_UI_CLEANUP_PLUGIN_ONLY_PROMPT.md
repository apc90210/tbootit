# TECHNOREBOOT — Avito UI Cleanup: Plugin-Only Owner Interface

Репозиторий:

```powershell
C:\tbootit
```

Дата:

```text
2026-08-14
```

Это отдельный UI-cleanup step.

Он выполняется ПЕРЕД:

```text
Stage06A-R9-R1
TECHNOREBOOT_STAGE06A_R9_R1_ATTRIBUTE_PROVENANCE_EXTENSION_SCOPE_AUDIT_PROMPT.md
```

R9-R1 сейчас ПРИОСТАНОВЛЕН и НЕ должен выполняться в рамках этого prompt.

---

# 1. ЦЕЛЬ

Очистить пользовательский интерфейс Техноребута от всех старых Avito-элементов, оставшихся от предыдущих попыток интеграции/синхронизации.

После cleanup у Owner должен остаться только один понятный актуальный Avito-инструмент:

```text
Chrome-плагин / расширение Avito
```

То есть owner-facing Avito UI должен быть:

```text
Avito
→ Расширение Avito
```

и больше никаких старых экранов/кнопок/надписей, связанных с предыдущими экспериментальными сценариями синхронизации.

---

# 2. ВАЖНО: ЭТО UI CLEANUP, А НЕ BACKEND CLEANUP

НЕ удалять без необходимости:

```text
Core API
Avito models
DB tables
external listing records
photo data
category/attribute model R9
service methods
integration routes
tests backend logic
```

если они не мешают пользовательскому интерфейсу.

Главная задача:

```text
убрать старое из UI
```

а не разрушить архитектурный фундамент.

---

# 3. ПЕРЕД РАБОТОЙ — GIT/RUNTIME AUDIT

```powershell
Set-Location C:\tbootit

git status --short --untracked-files=all
git branch --show-current
git rev-parse HEAD
git log --oneline -10
git diff --name-status
git diff --stat
docker compose ps
```

Не затереть unrelated changes.

---

# 4. НАЙТИ ВСЕ OWNER-VISIBLE AVITO SURFACES

Проаудировать минимум:

```text
admin-shell/app/templates
admin-shell/app/main.py
inventory-sales-module templates/routes
core-rendered templates if any
navigation/sidebar/header
product detail pages
Avito pages
extension page
legacy import/sync pages
buttons/forms/cards/links
```

И поиск по пользовательским текстам:

```text
Авито
Avito
синхронизация
синхронизировать
импорт
обратная синхронизация
reverse sync
парсер
аккаунт
объявления
выгрузить
загрузить
```

Отделить:

```text
ACTIVE_PLUGIN_UI
LEGACY_SYNC_UI
TECHNICAL_BACKEND_ONLY
```

---

# 5. РАЗРЕШЁННЫЙ OWNER-VISIBLE AVITO UI

После cleanup обязательно оставить:

## 5.1 Навигация

Один понятный пункт:

```text
Расширение Avito
```

или:

```text
Avito → Расширение
```

если текущая структура меню уже двухуровневая.

Не создавать сложное меню ради одного пункта.

## 5.2 Страница расширения

Сохранить рабочей:

```text
http://localhost:8011/avito/extension
```

На странице должны остаться только актуальные вещи:

```text
название расширения
текущая версия
кнопка скачать ZIP
краткая инструкция установки/обновления
статус/описание назначения расширения
```

Тексты — полностью на русском.

---

# 6. УБРАТЬ ИЗ OWNER UI СТАРЫЕ ПОПЫТКИ СИНХРОНИЗАЦИИ

Если существуют, убрать из навигации и экранов:

```text
старый импорт Avito
импорт аккаунта
массовая синхронизация
синхронизация объявлений
старый парсер
reverse sync
ручная отправка через старые формы
старые кнопки «синхронизировать»
старые карточки статуса синхронизации
экспериментальные Avito-экраны
старые инструкции по предыдущим механизмам
```

Критерий:

```text
Owner не должен видеть несколько конкурирующих способов работать с Avito.
```

Остаётся только:

```text
Chrome extension
```

---

# 7. PRODUCT DETAIL — ВРЕМЕННО НЕ ПОКАЗЫВАТЬ СТАРЫЙ AVITO UI

Если в карточке товара сейчас есть owner-visible блоки/вкладки Avito, возникшие из старых попыток синхронизации:

```text
старые параметры
старый статус
старые кнопки sync/import
старый external listing debug
```

их убрать/скрыть из owner UI.

ВАЖНО:

не удалять данные и API.

Если R9 добавил новый read-only блок характеристик Avito, который ещё не прошёл R9-R1 audit:

```text
его тоже временно скрыть из owner UI до завершения R9-R1,
если он сейчас виден Owner.
```

Причина:

```text
Owner попросил plugin-only Avito UI на время cleanup.
```

После R9-R1/R10 нужный чистый блок характеристик будет возвращён осознанно.

---

# 8. LEGACY ROUTES

Если есть старые UI routes вроде:

```text
/avito
/avito/import
/avito/sync
/avito/account
...
```

которые ведут на старые owner pages:

предпочтительно:

```text
убрать links/navigation
```

и либо:

```text
redirect legacy owner page → /avito/extension
```

если это безопасно и логично,

либо оставить route технически существующим, но недоступным из UI.

Не удалять API endpoints только ради cleanup.

---

# 9. НЕ ТРОГАТЬ РАБОТАЮЩИЙ PLUGIN FLOW

Сохранить без изменений функционально:

```text
extension download
extension ZIP
dynamic version display
server binding/status
single listing transfer
photo transfer
best-quality photos
error handling
```

Этот cleanup не должен ломать текущий успешно работающий импорт через плагин.

---

# 10. НЕ ТРОГАТЬ R9 DATA MODEL

Сохранить:

```text
AvitoCategory
AvitoAttributeDefinition
AvitoAttributeOption
ProductAvitoAttributeValue
```

и связанные Core изменения R9.

R9-R1 audit будет выполнен ПОСЛЕ cleanup отдельным prompt.

---

# 11. UI STYLE

Требования:

```text
полностью русский интерфейс
никаких технических debug-блоков для Owner
никаких JSON dump
никаких внутренних endpoint names
никаких англоязычных legacy labels
```

Страница расширения должна быть простой:

```text
что это
какая версия
скачать
как установить/обновить
```

---

# 12. NAVIGATION CLEANUP

После cleanup проверить глобальное меню.

Не должно быть одновременно:

```text
Авито
Avито импорт
Avито синхронизация
Парсер Avito
Расширение Avito
```

Должен остаться один owner-facing entry:

```text
Расширение Avito
```

или эквивалентный один понятный путь.

---

# 13. SEARCH FOR STALE COPY

После изменений выполнить поиск по owner-visible templates на stale phrases.

Особенно:

```text
«синхронизация Avito»
«импорт аккаунта»
«обратная синхронизация»
«парсер Avito»
«старый импорт»
```

В документации/код-комментариях такие слова могут оставаться.

Критерий касается именно пользовательского UI.

---

# 14. TESTS — UI

Добавить/обновить тесты минимум:

```text
navigation shows extension Avito entry
navigation does not show legacy Avito sync entries
extension page returns 200
extension download still returns 200
product detail does not show stale Avito sync controls
legacy owner Avito page redirects or is hidden according to chosen design
```

Если R9 read-only block временно скрыт:

добавить тест, что owner UI его сейчас не показывает,
но API/data model остаются доступны.

---

# 15. FULL REGRESSION

Запустить:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
docker compose exec -T inventory-sales-module pytest
docker compose exec -T avito-module pytest
docker compose exec -T repairs-module pytest
pytest admin-shell/tests
pytest chrome-extension/technoreboot-avito/tests
```

Указать фактические counts.

---

# 16. MANUAL OWNER ROUTES TO VERIFY

Проверить:

```text
http://localhost:8011/
http://localhost:8011/avito/extension
http://localhost:8011/inventory/products/58
```

Ожидаемо:

### Главный интерфейс

```text
нет старых Avito sync/import элементов
есть только понятный путь к расширению
```

### /avito/extension

```text
страница чистая
актуальная версия
скачивание работает
нет старых sync controls
```

### Product 58

```text
товар и фото работают как раньше
нет старых owner-visible Avito sync/debug блоков
```

---

# 17. НЕ МЕНЯТЬ EXTENSION VERSION БЕЗ ИЗМЕНЕНИЯ EXTENSION CODE

Если cleanup затрагивает только Admin Shell/templates:

```text
extension version НЕ bump.
```

Если extension runtime не меняется:

не пересобирать новый номер только ради UI cleanup.

ZIP можно оставить текущий.

---

# 18. DOCUMENTATION

Создать:

```text
reports/avito_ui_cleanup_plugin_only_report.md
```

Обновить:

```text
logs/2026-08-14.md
```

Сохранить prompt:

```text
.agents/received_prompts/TECHNOREBOOT_AVITO_UI_CLEANUP_PLUGIN_ONLY_PROMPT.md
```

---

# 19. REPORT STRUCTURE

Обязательно:

```text
STATUS

PRE_CLEANUP_AVITO_UI_INVENTORY
ACTIVE_PLUGIN_UI
LEGACY_UI_FOUND

REMOVED_FROM_NAVIGATION
REMOVED_FROM_PAGES
HIDDEN_PRODUCT_AVITO_UI
LEGACY_ROUTE_BEHAVIOR

BACKEND_PRESERVED
R9_DATA_MODEL_PRESERVED
PLUGIN_FLOW_PRESERVED

EXTENSION_CODE_CHANGED
EXTENSION_VERSION

TESTS
RUNTIME

FILES_CHANGED
COMMIT
PUSH
FINAL_GIT_STATUS

OWNER_CHECK_GUIDE
FINAL_STATUS
```

---

# 20. DEFINITION OF DONE

PASS только если:

```text
OWNER_AVITO_UI_PLUGIN_ONLY: true
LEGACY_AVITO_SYNC_UI_REMOVED: true
LEGACY_AVITO_IMPORT_UI_REMOVED: true
LEGACY_AVITO_PARSER_UI_REMOVED_IF_PRESENT: true
ONLY_EXTENSION_ENTRY_REMAINS: true
EXTENSION_PAGE_WORKS: true
EXTENSION_DOWNLOAD_WORKS: true
PRODUCT_FLOW_NOT_BROKEN: true
PHOTO_IMPORT_NOT_BROKEN: true
BACKEND_DATA_NOT_DELETED: true
R9_CORE_MODEL_PRESERVED: true
OWNER_MANUAL_CHECK_REQUIRED: true
```

---

# 21. GIT SAFETY

Запрещено:

```text
git add .
git add -A
git add -u
git reset
git clean
git rebase
git commit --amend
force push
DROP TABLE
mass DELETE
```

Targeted add only.

Commit message:

```text
Clean up Avito UI to plugin-only flow
```

или точнее по фактическим изменениям.

Push:

```powershell
git push origin main
```

---

# 22. OWNER CHECK GUIDE

После успешного отчёта ОСТАНОВИТЬСЯ.

Owner должен проверить:

```text
1. Открыть главный интерфейс.
2. Убедиться, что старых Avito import/sync/parser пунктов больше нет.
3. Найти один понятный пункт «Расширение Avito».
4. Открыть его.
5. Убедиться, что страница показывает только актуальный plugin flow.
6. Проверить скачивание расширения.
7. Открыть Product 58.
8. Убедиться, что товар/фото работают и старых Avito sync/debug элементов нет.
```

После OWNER acceptance cleanup:

```text
вернуться к:
TECHNOREBOOT_STAGE06A_R9_R1_ATTRIBUTE_PROVENANCE_EXTENSION_SCOPE_AUDIT_PROMPT.md
```

и продолжить проект с того же места.

---

# 23. FINAL STATUS

При успехе:

```text
FINAL_STATUS:
TECHNOREBOOT_AVITO_UI_CLEANUP_PLUGIN_ONLY_READY_FOR_OWNER_CHECK

OWNER_AVITO_UI_PLUGIN_ONLY: true
LEGACY_AVITO_SYNC_UI_REMOVED: true
LEGACY_AVITO_IMPORT_UI_REMOVED: true
ONLY_EXTENSION_ENTRY_REMAINS: true
EXTENSION_PAGE_WORKS: true
EXTENSION_DOWNLOAD_WORKS: true
PRODUCT_FLOW_NOT_BROKEN: true
R9_CORE_MODEL_PRESERVED: true
OWNER_MANUAL_CHECK_REQUIRED: true

PROJECT_NEXT_STEP_AFTER_OWNER_ACCEPTANCE:
RESUME_STAGE06A_R9_R1
```

После отчёта ОСТАНОВИТЬСЯ.
