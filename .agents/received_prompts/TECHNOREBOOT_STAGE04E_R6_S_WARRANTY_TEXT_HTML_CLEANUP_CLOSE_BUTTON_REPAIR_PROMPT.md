# PROMPT — Техноребут / Stage 04E-R6-S Warranty Text HTML Cleanup and Close Button Repair

## Роль агента

Ты senior fullstack bugfix engineer, Jinja2/HTML escaping reviewer, UX regression engineer и QA/release auditor проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Твоя задача — исправить owner-check fail после Stage04E-R6-R: в текстах гарантии видны служебные `<br>`, а кнопка «Закрыть» не работает.

Это repair-этап. Не начинать Stage04F и не добавлять новый функционал.

---

# 1. Owner-reported fail

Владелец сообщил:

```text
На все Б/У товары предоставляется гарантия 30 дней.
Гарантийный ремонт и обмен Б/У товара возможен только в случае обнаружения дефекта товара в течении 30 дней с даты продажи. <br>Товар Б/У без дефектов возврату - не подлежит, возможен обмен, но только по согласованию с менеджером магазина. В случае обнаружения дефекта товара по вине покупателя обмен и возврат товара – невозможен. <br>На программное обеспечение и расходные материалы гарантия не предоставляется. <br>В случае обнаружения неисправности – товар сдается на диагностику. По согласованию с продавцом – возможна мгновенная замена товара, без проведения диагностики.

в тексте гарантии - служебные символы
кнопка закрыть не работает
без гарантии все то же самое символы и не закрыть
```

Интерпретация:

```text
1. В настройках организации или в товарном чеке пользователь видит literal "<br>".
2. Это недопустимо: warranty_text/no_warranty_text должны быть plain text.
3. В textarea должны быть обычные переносы строк, не HTML.
4. В чеке переносы должны отображаться красиво, но безопасно.
5. Кнопка "Закрыть" в чеке/preview не работает.
```

---

# 2. Target status

Текущий статус:

```text
STAGE04E_R6_R_OWNER_RECHECK_FAILED_HTML_BR_AND_CLOSE_BUTTON
```

Целевой статус:

```text
TECHNOREBOOT_STAGE04E_R6_S_WARRANTY_TEXT_HTML_CLEANUP_CLOSE_BUTTON_READY_FOR_OWNER_RECHECK
```

Gate:

```text
OWNER_MANUAL_CHECK_REQUIRED: true
OWNER_ACCEPTANCE_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 3. Strict prohibitions

Запрещено:

```text
начинать Stage04F
делать новый функционал
делать direct DB access из inventory-sales-module
создавать отдельную DB для inventory-sales-module
использовать git add .
использовать git add -A
использовать git add -u
использовать git commit --amend
использовать git reset / git clean / rebase / force push
коммитить runtime DB/temp/cache
делать Base.metadata.drop_all/create_all
очищать runtime DB для прохождения проверки
рендерить user-editable warranty_text через |safe без очистки
```

Разрешено:

```text
точечный bugfix Core settings text normalization
точечный bugfix inventory fallback defaults
точечный bugfix Jinja template rendering
точечный bugfix close button behavior
tests
report/log
targeted commit
normal push
```

---

# 4. Prompt discovery

Найти prompt:

```text
TECHNOREBOOT_STAGE04E_R6_S_WARRANTY_TEXT_HTML_CLEANUP_CLOSE_BUTTON_REPAIR_PROMPT.md
```

Искать:

```text
C:\tbootit
C:\tbootit\.agents
C:\tbootit\docs
C:\tbootit\docs\obsidian
C:\tbootit\prompts
C:\tbootit\logs\prompts
C:\Users\Apc\Downloads
```

Если найден в Downloads — скопировать в:

```text
C:\tbootit\.agents\received_prompts\
```

В report указать:

```text
PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:
```

---

# 5. Preflight

Выполнить:

```powershell
Set-Location C:\tbootit

git status --short --untracked-files=all
git branch --show-current
git log --oneline -10
git diff --name-status
git diff --stat
docker compose ps
```

Если worktree dirty — сначала понять почему.

---

# 6. Root cause checks

Найти все места, где появляются `<br>` в гарантийном тексте:

```powershell
git grep -n -I "<br>\|br />\|br/>|replace.*newline|replace.*\\n|warranty_text|no_warranty_text" -- core inventory-sales-module
```

Проверить runtime API:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/settings/organization" | ConvertTo-Json -Depth 10
```

Проверить UI HTML:

```powershell
$page = Invoke-WebRequest "http://127.0.0.1:8030/settings/organization" -TimeoutSec 15
$page.Content | Select-String "<br>"
$page.Content | Select-String "&lt;br"
```

Если есть продажа, проверить receipt:

```powershell
# заменить <sale_id> на реальный ID
$page = Invoke-WebRequest "http://127.0.0.1:8030/sales/<sale_id>/receipt" -TimeoutSec 15
$page.Content | Select-String "<br>"
$page.Content | Select-String "&lt;br"
$page.Content | Select-String "Закрыть"
```

Важно:

```text
В HTML самой страницы могут быть технические <br> в layout, но в textarea/видимом тексте гарантии не должно быть literal "<br>".
В rendered receipt допускаются HTML-теги, если они не видны пользователю.
Но user-provided/editable text нельзя выводить через |safe без нормализации.
```

---

# 7. Fix A — normalize warranty text to plain text

Создать/использовать функцию нормализации в Core и Inventory fallback:

```python
def normalize_multiline_text(value: str | None) -> str:
    if value is None:
        return ""
    text = str(value)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"(?i)&lt;\s*br\s*/?\s*&gt;", "\n", text)
    text = re.sub(r"(?i)<\s*br\s*/?\s*>", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
```

Использовать для:

```text
1. Default warranty_text.
2. Default no_warranty_text.
3. Backfill existing DB values.
4. GET /api/settings/organization response.
5. PUT /api/settings/organization save path.
6. Inventory fallback get_effective_settings().
```

Требование:

```text
В БД и API желательно хранить plain text with newline, а не HTML.
```

---

# 8. Fix B — Jinja rendering

## Settings page

В `settings_organization.html` textarea должен показывать plain text:

```jinja2
<textarea name="warranty_text">{{ settings.warranty_text }}</textarea>
<textarea name="no_warranty_text">{{ settings.no_warranty_text }}</textarea>
```

Не должно быть:

```text
<br>
&lt;br&gt;
|safe
```

в textarea.

## Receipt page

В `sale_receipt_preview.html` гарантийный текст должен отображаться с переносами строк.

Рекомендуемый вариант:

```html
<div class="warranty-text">{{ warranty_text }}</div>
```

CSS:

```css
.warranty-text {
  white-space: pre-line;
}
```

То есть Jinja сам экранирует текст, а переносы строк отображаются CSS.

Не использовать:

```jinja2
{{ warranty_text | safe }}
```

если текст редактируется пользователем.

---

# 9. Fix C — close button

Найти кнопку:

```powershell
git grep -n -I "Закрыть\|window.close\|history.back\|close" -- inventory-sales-module/app/templates
```

Исправить так, чтобы работало надежно.

Рекомендуемый вариант для preview:

```html
<button type="button" onclick="window.history.length > 1 ? window.history.back() : window.location.href='/sales'">
  Закрыть
</button>
```

или просто ссылка:

```html
<a class="btn" href="/sales">Закрыть</a>
```

Если чек открыт из конкретной продажи, лучше:

```text
Закрыть → назад к продаже или /sales
```

Требование:

```text
Кнопка "Закрыть" должна работать в обычном браузере, а не зависеть только от window.close(),
потому что window.close() часто не работает для вкладок, открытых вручную.
```

---

# 10. Tests — Core

Обновить/добавить:

```text
core/tests/test_organization_settings_defaults.py
```

Покрыть:

```text
1. GET backfills existing warranty_text containing "<br>" to newline/plain text.
2. GET response does not contain literal "<br>" or "&lt;br&gt;" in warranty_text/no_warranty_text.
3. PUT with warranty_text containing "<br>" saves normalized newline text.
4. Default warranty_text contains newline separators and no HTML br tags.
```

---

# 11. Tests — Inventory

Обновить/добавить:

```text
inventory-sales-module/tests/test_organization_settings_defaults_ui.py
inventory-sales-module/tests/test_receipt_organization_and_warranty_text.py
```

Покрыть:

```text
1. /settings/organization textarea does not visibly contain literal <br>.
2. /settings/organization textarea contains plain text/newlines.
3. Receipt with warranty does not show escaped &lt;br&gt;.
4. Receipt with warranty does not show literal visible <br> text.
5. Receipt no-warranty does not show escaped/literal br text.
6. Receipt page has a working close control:
   - either href="/sales";
   - or onclick with history.back fallback.
```

---

# 12. Manual smoke

Rebuild/recreate:

```powershell
docker compose up --build -d --force-recreate core inventory-sales-module
docker compose ps
```

Check settings page:

```powershell
$page = Invoke-WebRequest "http://127.0.0.1:8030/settings/organization" -TimeoutSec 15
$page.StatusCode
$page.Content | Select-String "ИП Атанов Павел Сергеевич"
$page.Content | Select-String "На все Б/У товары предоставляется гарантия 30 дней"
$page.Content | Select-String "&lt;br"
```

Expected:

```text
StatusCode 200
Atanov visible
Warranty text visible
No escaped &lt;br&gt; in visible text/textarea
```

Browser manual check:

```text
http://127.0.0.1:8030/settings/organization
```

Verify:

```text
1. Warranty textarea has normal lines.
2. No visible <br>.
3. No visible &lt;br&gt;.
4. No-warranty textarea has normal lines.
```

Receipt check:

```text
http://127.0.0.1:8030/sales
→ open sale
→ товарный чек
```

Verify:

```text
1. Warranty text has normal line breaks.
2. No visible <br>.
3. No visible &lt;br&gt;.
4. "Закрыть" returns to previous page or /sales.
```

---

# 13. Full regression

Обязательно:

```powershell
docker compose exec core pytest
docker compose exec inventory-sales-module pytest
docker compose exec avito-module pytest
```

All PASS.

---

# 14. Safety scans

Runtime tracked:

```powershell
git ls-files | Select-String -Pattern "tbootit\.db|technoreboot\.db|\.sqlite|\.sqlite3|data/db|data/avito-module|__pycache__|\.pytest_cache|debug\.py"
```

Direct DB access in inventory-sales-module:

```powershell
git grep -n -I "create_engine\|SessionLocal\|sqlite\|technoreboot.db\|tbootit.db\|data/db\|sqlalchemy\|SELECT .* FROM\|INSERT INTO" -- inventory-sales-module
```

Destructive DB calls:

```powershell
git grep -n -I "drop_all\|DROP TABLE\|DELETE FROM" -- core inventory-sales-module
```

Secrets:

```powershell
git ls-files | Select-String -Pattern "\.env$|id_rsa|id_ed25519|private_key|\.pem|\.p12|\.pfx"
```

---

# 15. Report/log

Создать:

```text
reports/stage04e_r6_s_warranty_text_html_cleanup_close_button_repair_report.md
docs/stage04e_r6_s_warranty_text_html_cleanup_close_button_repair.md
```

Обновить:

```text
logs/2026-07-03.md
```

Report structure:

```text
# Stage 04E-R6-S Warranty Text HTML Cleanup and Close Button Repair Report

## STATUS

READY_FOR_OWNER_RECHECK / FAIL

## OWNER_REPORTED_FAIL

## ROOT_CAUSE

Stored HTML br:
Template rendering:
Close button:

## FIXES

### Plain text normalization

### Settings textarea rendering

### Receipt safe multiline rendering

### Close button fallback

## TESTS

Core:
Inventory:
Avito:

## MANUAL_SMOKE

Settings page:
Receipt warranty:
Receipt no-warranty:
Close button:

## SAFETY_SCAN

Runtime tracked:
Direct DB access:
Destructive DB calls:
Secrets:

## FILES_CHANGED

## COMMIT

## PUSH

## OWNER_RECHECK_GUIDE

## FINAL_STATUS

TECHNOREBOOT_STAGE04E_R6_S_WARRANTY_TEXT_HTML_CLEANUP_CLOSE_BUTTON_READY_FOR_OWNER_RECHECK
OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 16. Git

Use targeted add only.

Possible files:

```powershell
git add core/app/defaults.py
git add core/app/routers/settings.py
git add core/tests/test_organization_settings_defaults.py

git add inventory-sales-module/app/defaults.py
git add inventory-sales-module/app/core_client.py
git add inventory-sales-module/app/routers/settings.py
git add inventory-sales-module/app/routers/sales.py
git add inventory-sales-module/app/templates/settings_organization.html
git add inventory-sales-module/app/templates/sale_receipt_preview.html
git add inventory-sales-module/tests/test_organization_settings_defaults_ui.py
git add inventory-sales-module/tests/test_receipt_organization_and_warranty_text.py

git add docs/stage04e_r6_s_warranty_text_html_cleanup_close_button_repair.md
git add reports/stage04e_r6_s_warranty_text_html_cleanup_close_button_repair_report.md
git add logs/2026-07-03.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04E_R6_S_WARRANTY_TEXT_HTML_CLEANUP_CLOSE_BUTTON_REPAIR_PROMPT.md

git commit -m "Repair warranty text rendering and receipt close button"
git status --short --untracked-files=all
```

Forbidden:

```text
git add .
git add -A
git add -u
git commit --amend
```

If remote exists:

```powershell
git push
```

No force push.

---

# 17. Definition of Done

Готово, если:

```text
warranty_text stored/returned as plain text with newline
no_warranty_text stored/returned as plain text with newline
/settings/organization shows no visible <br> or &lt;br&gt;
receipt warranty shows no visible <br> or &lt;br&gt;
receipt no-warranty shows no visible <br> or &lt;br&gt;
receipt line breaks display correctly
close button works via history.back fallback or /sales link
full core pytest PASS
full inventory-sales-module pytest PASS
full avito-module pytest PASS
safety scans clean
targeted commit
push
READY_FOR_OWNER_RECHECK
```

---

# 18. Final answer required from agent

Финальный ответ должен быть подробным в чат.

Обязательно:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04E_R6_S_WARRANTY_TEXT_HTML_CLEANUP_CLOSE_BUTTON_READY_FOR_OWNER_RECHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

Если есть blockers:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04E_R6_S_WARRANTY_TEXT_HTML_CLEANUP_CLOSE_BUTTON_FAIL

BLOCKERS:
...
```
