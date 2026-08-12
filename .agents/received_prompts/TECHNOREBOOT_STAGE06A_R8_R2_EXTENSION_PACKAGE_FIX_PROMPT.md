# TECHNOREBOOT — Stage06A-R8-R2 Fix Chrome Extension Package / Missing Icons

Репозиторий:

```powershell
C:\tbootit
```

Стартовая точка:

```text
Stage06A-R8-R1
Commit: d88aa3a
```

Это corrective stage. Не начинать R9 и Stage06B.

---

## 1. Реальный owner blocker

Владелец скачал ZIP расширения, распаковал его и попытался загрузить через:

```text
chrome://extensions
→ Режим разработчика
→ Загрузить распакованное расширение
```

Chrome вернул:

```text
Could not load icon 'icons/icon16.png' specified in 'icons'.
Не удалось загрузить манифест.
```

Следовательно:

```text
ZIP скачивается;
manifest.json читается;
но пакет расширения неполный/неконсистентный.
```

R8-R1 НЕ принят как installable extension.

---

## 2. Цель

Добиться, чтобы скачанный через:

```text
http://localhost:8011/avito/extension/download
```

ZIP после распаковки можно было загрузить в Chrome без ошибок manifest/resources.

---

## 3. Сначала воспроизвести

До изменений:

```text
1. Скачать текущий ZIP через localhost:8011.
2. Распаковать во временную папку.
3. Прочитать manifest.json.
4. Проверить все paths из manifest.
```

Зафиксировать:

```text
ZIP_FILE_LIST
MANIFEST_ICON_PATHS
MISSING_RESOURCES
ROOT_CAUSE
```

---

## 4. Проверить manifest.json

Проверить все resource references:

```text
icons
action.default_icon
action.default_popup
background.service_worker
content_scripts.js
content_scripts.css
web_accessible_resources
```

Каждый referenced file должен реально существовать в package.

---

## 5. Icons

Если manifest содержит:

```json
"icons": {
  "16": "icons/icon16.png",
  "32": "icons/icon32.png",
  "48": "icons/icon48.png",
  "128": "icons/icon128.png"
}
```

создать реальные PNG:

```text
chrome-extension/technoreboot-avito/icons/icon16.png
chrome-extension/technoreboot-avito/icons/icon32.png
chrome-extension/technoreboot-avito/icons/icon48.png
chrome-extension/technoreboot-avito/icons/icon128.png
```

И аналогично для `action.default_icon`, если он используется.

Иконки могут быть простыми локальными проектными изображениями.

Не использовать внешние URL.

---

## 6. Не лечить удалением обязательных ссылок вслепую

Можно удалить необязательные icon declarations только если архитектурно решено, что иконки не нужны.

Предпочтительно:
```text
оставить icons и положить корректные файлы.
```

---

## 7. Build script

Проверить:

```text
scripts/build_extension_zip.py
```

Он должен рекурсивно включать:

```text
manifest.json
service_worker.js
content.js
popup.html
popup.js
popup.css
README.md
icons/**
и любые другие runtime resources
```

Не использовать whitelist, который забывает новые подпапки.

Предпочтительно собирать весь extension directory рекурсивно, исключая только:

```text
tests/
fixtures/
__pycache__/
*.pyc
development artifacts
```

если они не нужны в runtime.

---

## 8. ZIP root structure

После распаковки должно быть:

```text
technoreboot-avito/
├── manifest.json
├── service_worker.js
├── content.js
├── popup.html
├── popup.js
├── popup.css
└── icons/
    ├── icon16.png
    ├── icon32.png
    ├── icon48.png
    └── icon128.png
```

Важно:

Когда owner выбирает папку через «Загрузить распакованное расширение»,
`manifest.json` должен лежать непосредственно в выбранной папке.

Не должно быть лишней вложенности:

```text
technoreboot-avito/technoreboot-avito/manifest.json
```

---

## 9. Manifest resource validator

Добавить build-time validator.

Например:

```text
scripts/validate_extension_package.py
```

Он должен:

```text
load manifest.json;
collect referenced files;
verify each exists;
verify referenced PNG files are valid non-empty PNG;
verify service worker exists;
verify popup exists;
verify content scripts exist.
```

При missing resource:

```text
exit code != 0
build FAIL
```

---

## 10. ZIP validator

После build:

```text
open generated ZIP;
extract to temp;
run same manifest resource validation against extracted contents.
```

Это обязательно.

Проверка source folder недостаточна — баг мог появиться именно при packaging.

---

## 11. Live download validator

После размещения ZIP в Admin Shell:

```text
GET http://localhost:8011/avito/extension/download
```

Агент должен:

```text
скачать live ZIP;
распаковать;
validate manifest resources.
```

Это mandatory runtime proof.

---

## 12. Chrome load smoke test

Если в окружении доступен Chromium/Chrome с extension loading, выполнить автоматический smoke:

```text
--load-extension=<unpacked-extension-path>
```

и убедиться:

```text
manifest load error = 0
extension process loads
```

Не требуется авторизация Avito.

Если GUI automation неудобна, минимум — validate manifest + Chrome startup logs.

---

## 13. Extension version

Поднять patch version:

```text
0.1.0 → 0.1.1
```

или текущую корректную patch version.

На странице Technoreboot показать новую version.

---

## 14. Download cache

Проверить, что браузер owner не скачивает старый ZIP из cache.

Для download response добавить корректно:

```text
Cache-Control: no-store
```

или versioned filename:

```text
technoreboot-avito-extension-0.1.1.zip
```

Предпочтительно versioned filename.

---

## 15. Admin Shell page

На `/avito/extension` показывать:

```text
Версия расширения: 0.1.1
```

Кнопка:

```text
Скачать расширение 0.1.1
```

Чтобы owner понимал, что скачал новую сборку.

---

## 16. Tests

Добавить:

```text
chrome-extension/technoreboot-avito/tests/test_manifest_resources_exist.py
chrome-extension/technoreboot-avito/tests/test_extension_zip_contents.py
chrome-extension/technoreboot-avito/tests/test_icons_are_valid_png.py
admin-shell/tests/test_extension_download_is_current_version.py
admin-shell/tests/test_extension_download_manifest_valid.py
```

---

## 17. Explicit regression for reported bug

Test должен падать, если:

```text
manifest references icons/icon16.png
```

а файла нет в ZIP.

Назвать:

```text
test_all_manifest_referenced_resources_exist_in_download_zip
```

---

## 18. Runtime proof

После final build/restart:

```text
1. GET /avito/extension = 200
2. Download ZIP through localhost:8011
3. ZIP non-zero
4. Extract
5. manifest.json found
6. icons/icon16.png exists
7. icons/icon32.png exists
8. icons/icon48.png exists
9. icons/icon128.png exists
10. all manifest resources valid
11. extension loads without manifest error
```

---

## 19. Не менять integration logic

R8-R2 не переписывает:

```text
pairing
bridge endpoints
listing parser
Core import
photo import
idempotency
```

если это не требуется для packaging fix.

---

## 20. Regression

Обязательно:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
docker compose exec -T inventory-sales-module pytest
docker compose exec -T avito-module pytest
docker compose exec -T repairs-module pytest
pytest admin-shell/tests
pytest chrome-extension/technoreboot-avito/tests
```

---

## 21. Documentation

Обновить:

```text
chrome-extension/technoreboot-avito/README.md
docs/stage06a_r8_chrome_extension_avito_bridge.md
reports/stage06a_r8_chrome_extension_avito_bridge_report.md
logs/2026-08-12.md
```

---

## 22. Git

Expected HEAD:

```text
d88aa3a
```

или фактический потомок.

Только targeted add.

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
```

Commit:

```powershell
git commit -m "Fix Chrome extension package resources"
git push origin main
```

---

## 23. Definition of Done

Готово только если:

```text
download page works;
new version shown;
live ZIP downloads;
manifest.json present;
all manifest referenced files present;
all icon files present;
PNG icons valid;
no excessive folder nesting;
live downloaded ZIP validates;
Chrome loads unpacked extension without manifest error;
all regression suites PASS;
commit pushed;
git clean.
```

---

## 24. Owner check after R8-R2

Owner делает только:

```text
1. Удалить старую распакованную папку расширения.
2. Открыть http://localhost:8011/avito/extension.
3. Скачать НОВУЮ версию ZIP.
4. Распаковать в новую папку.
5. Открыть chrome://extensions.
6. Включить режим разработчика.
7. Нажать «Загрузить распакованное расширение».
8. Выбрать папку, где прямо лежит manifest.json.
9. Убедиться, что расширение загрузилось без ошибки.
```

После этого STOP.

Pairing и импорт пока не проверять до owner confirmation, что extension успешно установлен.

---

## 25. Final status

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE06A_R8_R2_EXTENSION_PACKAGE_READY_FOR_OWNER_INSTALL_CHECK

OWNER_EXTENSION_INSTALL_REQUIRED: true
OWNER_PAIRING_NOT_YET_ACCEPTED: true
OWNER_ONE_ITEM_EXTENSION_PROBE_NOT_YET_ACCEPTED: true
FULL_ACCOUNT_IMPORT_NOT_YET_AUTHORIZED: true
DO_NOT_START_STAGE06A_R9_WITHOUT_OWNER_ACCEPTANCE: true
DO_NOT_START_STAGE06B_REVERSE_SYNC_WITHOUT_OWNER_ACCEPTANCE: true
```
