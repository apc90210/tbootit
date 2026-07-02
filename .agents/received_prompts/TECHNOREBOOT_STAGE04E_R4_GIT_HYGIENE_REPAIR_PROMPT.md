# PROMPT — Техноребут / Stage 04E-R4 Git Hygiene Repair after Audit

## Роль агента

Ты senior release engineer, Git hygiene auditor, repository safety engineer и QA/recovery engineer проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Твоя задача — исправить Git hygiene blocker, найденный после Stage04E-R4-Audit.

Это cleanup/recovery stage. Новый функционал не делать.

---

# 1. Причина этапа

Stage04E-R4-Audit заявил функциональный `PASS_WITH_NOTES`, но обнаружил серьёзную проблему:

```text
Предыдущий агент использовал запрещённый git add -A.
Из-за этого в репозиторий попали:
- runtime database: core/tbootit.db
- временный debug.py
- старые/временные отчёты
```

Это нельзя считать мелким замечанием.

Статус:

```text
STAGE04E_R4_AUDIT_FUNCTIONAL_PASS_BUT_GIT_HYGIENE_BLOCKED
```

Цель:

```text
удалить runtime/temp artifacts из git index,
усилить .gitignore,
проверить, что рабочее дерево чистое,
не переписывать историю,
не ломать функциональность.
```

---

# 2. Главные правила

Строго запрещено:

```text
git add .
git add -A
git add -u
git commit --amend
git reset
git clean
git rebase
git push --force
удалять runtime данные физически без явной причины
Base.metadata.drop_all/create_all
начинать новый функционал
начинать Stage04F
```

Разрешено:

```text
git rm --cached <file>     # убрать файл из индекса, но оставить локально
git add <точный файл>
git commit -m "<message>"
```

Если нужно убрать файл из репозитория, но оставить на диске:

```powershell
git rm --cached core/tbootit.db
```

---

# 3. Prompt discovery

Найти prompt:

```text
TECHNOREBOOT_STAGE04E_R4_GIT_HYGIENE_REPAIR_PROMPT.md
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

В отчете указать:

```text
PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:
```

---

# 4. Preflight

Выполнить:

```powershell
Set-Location C:\tbootit

git status --short --untracked-files=all
git branch --show-current
git log --oneline -20
git show --name-status --oneline --stat HEAD
```

Проверить, есть ли изменения после audit:

```powershell
git diff --name-status
git diff --stat
```

---

# 5. Найти все опасные tracked files

Выполнить:

```powershell
git ls-files | Select-String -Pattern "tbootit\.db|technoreboot\.db|\.sqlite|\.sqlite3|data/db|data/avito-module|__pycache__|\.pytest_cache|debug\.py|task\.md|implementation_plan\.md|TECHNOREBOOT_STAGE04E_R3_REPORT\.md"
```

Также:

```powershell
git status --ignored --short --untracked-files=all -- data/db
git status --ignored --short --untracked-files=all -- data/avito-module
```

Классификация:

## Обязательно убрать из git index

```text
core/tbootit.db
любые *.db / *.sqlite / *.sqlite3 runtime DB
debug.py
__pycache__
.pytest_cache
```

## Проверить и решить

```text
task.md
implementation_plan.md
TECHNOREBOOT_STAGE04E_R3_REPORT.md
старые root reports
```

Если это временные agent artifacts — убрать из индекса.

Если это документация/отчёт, перенести/оставить только в правильном месте:

```text
reports/
docs/
.logs/
```

Но не коммитить мусор в корень.

---

# 6. Обновить .gitignore

Проверить `.gitignore`.

Добавить, если нет:

```gitignore
# Runtime databases
*.db
*.sqlite
*.sqlite3
data/db/
data/avito-module/

# Python/test/cache
__pycache__/
*.pyc
.pytest_cache/

# Local debug/temp artifacts
debug.py
task.md
implementation_plan.md
TECHNOREBOOT_*_REPORT.md

# Local env/runtime
.env
*.log.tmp
```

Важно: если project rules требуют `task.md`/`implementation_plan.md` tracked, не добавлять их в ignore. Но по текущему проекту они выглядят как временные agent artifacts.

---

# 7. Убрать опасные файлы из index

Использовать только targeted commands.

Пример:

```powershell
git rm --cached core/tbootit.db
git rm --cached debug.py
```

Если файлы tracked и существуют в других путях — убрать точечно.

Не использовать:

```powershell
git rm -r --cached .
```

Не использовать:

```powershell
git add .
```

После каждого действия проверять:

```powershell
git status --short --untracked-files=all
```

---

# 8. Проверить, что runtime DB не удалена физически

Если использовался `git rm --cached`, файл должен остаться локально.

Проверить:

```powershell
Test-Path core\tbootit.db
```

Если файл реально не нужен — не удалять без отдельного owner approval.

---

# 9. Проверить функциональность после cleanup

Нужно убедиться, что удаление из git index не ломает runtime.

Запустить:

```powershell
docker compose ps
docker compose exec core pytest
docker compose exec inventory-sales-module pytest
docker compose exec avito-module pytest
```

Если контейнеры не подняты:

```powershell
docker compose up -d
```

Не делать destructive DB reset.

---

# 10. Safety scans

Проверить, что больше нет tracked runtime/temp:

```powershell
git ls-files | Select-String -Pattern "tbootit\.db|technoreboot\.db|\.sqlite|\.sqlite3|data/db|data/avito-module|__pycache__|\.pytest_cache|debug\.py"
```

Ожидание:

```text
ничего не найдено
```

Проверить direct DB access в inventory-sales-module:

```powershell
git grep -n -I "create_engine\|SessionLocal\|sqlite\|technoreboot.db\|tbootit.db\|data/db\|sqlalchemy\|SELECT .* FROM\|INSERT INTO" -- inventory-sales-module
```

Ожидание:

```text
нет прямого DB access
```

Проверить destructive DB calls:

```powershell
git grep -n -I "drop_all\|create_all\|DROP TABLE\|DELETE FROM" -- core inventory-sales-module
```

Оценка:

```text
Base.metadata.create_all в startup может быть допустимым только если это текущий установленный проектный стиль.
drop_all в runtime code — blocker.
```

---

# 11. Report

Создать:

```text
reports/stage04e_r4_git_hygiene_repair_report.md
```

Структура:

```text
# Stage 04E-R4 Git Hygiene Repair Report

## STATUS

READY_FOR_OWNER_CHECK / FAIL

## REASON

## PROMPT_DISCOVERY

PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:

## BEFORE_STATE

Branch:
Head:
Dirty files:
Tracked dangerous files:

## ACTIONS_TAKEN

Files removed from git index:
Files kept:
Files added to .gitignore:
Files not touched:

## TESTS

Core:
Inventory:
Avito:

## SAFETY_SCAN

Tracked runtime data:
Direct DB access:
Destructive DB calls:

## GIT_STATUS_AFTER

## BLOCKERS

## OWNER_RECHECK_GUIDE

## FINAL_STATUS

TECHNOREBOOT_STAGE04E_R4_GIT_HYGIENE_REPAIR_READY_FOR_OWNER_CHECK
OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 12. Logging

Append to:

```text
logs/2026-07-02.md
```

Include:

```text
prompt filename
prompt source/local copy
before HEAD
dangerous files found
cleanup actions
tests
final git status
final status
```

---

# 13. Git commit

Use targeted add only.

Example:

```powershell
git status --short --untracked-files=all

git add .gitignore
git add reports/stage04e_r4_git_hygiene_repair_report.md
git add logs/2026-07-02.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04E_R4_GIT_HYGIENE_REPAIR_PROMPT.md

git commit -m "Repair Stage 04E R4 git hygiene"
git status --short --untracked-files=all
```

If `git rm --cached` staged removals exist, they are already staged. Do not use broad add.

Forbidden:

```text
git add .
git add -A
git add -u
git commit --amend
```

---

# 14. Definition of Done

Готово, если:

```text
runtime DB removed from git index
debug/temp/cache removed from git index
.gitignore protects DB/cache/temp
tracked dangerous file scan clean
tests pass: core, inventory-sales-module, avito-module
no direct DB access in inventory-sales-module
no destructive drop_all in runtime code
cleanup report created
normal commit created
no amend used
final git status checked
```

---

# 15. Final answer required from agent

Финальный ответ должен быть подробным в чат, не только статус.

Обязательно указать:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04E_R4_GIT_HYGIENE_REPAIR_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

Не писать, что можно переходить дальше, пока владелец не примет.
