# PROMPT — Техноребут / GitHub Publish `apc90210/tbootit`

## Роль агента

Ты senior release engineer, Git/GitHub publishing engineer, security preflight auditor и repository hygiene auditor проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Цель — безопасно выложить локальный репозиторий на GitHub:

```text
GitHub owner: apc90210
GitHub repo: tbootit
Target: apc90210/tbootit
```

Это release/publish stage, не новый функциональный этап.

---

# 1. Входной контекст

Последний рабочий статус проекта:

```text
TECHNOREBOOT_STAGE04E_R5_AUDIT_FINALIZATION_REPAIR_READY_FOR_OWNER_MANUAL_CHECK
```

Заявлено:

```text
core pytest: PASS
inventory-sales-module pytest: PASS
avito-module pytest: PASS
Git hygiene: clean after targeted commit
runtime DB not tracked
```

Перед публикацией всё равно нужно повторить preflight.

---

# 2. Строгие запреты

Запрещено:

```text
git push --force
git push --force-with-lease
git reset
git clean
git rebase
git commit --amend
git add .
git add -A
git add -u
публиковать .env/secrets/private keys
публиковать runtime DB
публиковать data/db или data/avito-module
создавать public GitHub repo без явного подтверждения владельца
начинать новый функционал
```

Разрешено:

```text
git status
git log
git remote
git ls-files
secret scan
добавить remote origin, если отсутствует
создать private repo через gh CLI, если repo отсутствует и GitHub auth готов
обычный git push без force
```

Если видимость repo не определена:

```text
DEFAULT: private
```

Если команда создания repo требует выбрать public/private и владелец заранее не подтвердил public:

```text
создать private
```

---

# 3. Prompt discovery

Найти prompt:

```text
TECHNOREBOOT_GITHUB_PUBLISH_APC90210_TBOOTIT_PROMPT.md
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

# 4. Preflight Git state

Выполнить:

```powershell
Set-Location C:\tbootit

git status --short --untracked-files=all
git branch --show-current
git log --oneline -10
git remote -v
```

Ожидание:

```text
working tree clean
branch known, preferably main/master
latest commit includes Stage04E-R5 finalization
```

Если worktree dirty:

```text
STOP
не push
сообщить список dirty files
```

---

# 5. Git hygiene scan before push

Проверить, что runtime/temp не tracked:

```powershell
git ls-files | Select-String -Pattern "tbootit\.db|technoreboot\.db|\.sqlite|\.sqlite3|data/db|data/avito-module|__pycache__|\.pytest_cache|debug\.py|\.env$|id_rsa|id_ed25519|private_key|\.pem|\.p12|\.pfx"
```

Ожидание:

```text
no output
```

Если есть output:

```text
STOP
не push
нужен cleanup prompt
```

Проверить ignored runtime status:

```powershell
git status --ignored --short --untracked-files=all -- data/db
git status --ignored --short --untracked-files=all -- data/avito-module
```

---

# 6. Secret scan

Выполнить минимум:

```powershell
git grep -n -I "SECRET_KEY\|PRIVATE_KEY\|BEGIN RSA PRIVATE KEY\|BEGIN OPENSSH PRIVATE KEY\|password\s*=\|PASSWORD\s*=\|token\s*=\|TOKEN\s*=\|api_key\|API_KEY\|BOT_TOKEN\|TELEGRAM_TOKEN\|ssh_private_key\|Authorization: Bearer" -- .
```

Проверить `.env`:

```powershell
git ls-files | Select-String -Pattern "^\.env$|\.env"
```

Ожидание:

```text
нет реальных секретов
.env не tracked
```

Если найдены реальные секреты:

```text
STOP
не push
создать список файлов/строк
```

Важно: false positives в docs/prompts можно отметить, но если сомневаешься — STOP.

---

# 7. Optional tests before push

Если контейнеры подняты и доступно время, выполнить:

```powershell
docker compose ps
docker compose exec core pytest
docker compose exec inventory-sales-module pytest
docker compose exec avito-module pytest
```

Если контейнеры не подняты и тесты только что были успешно пройдены в предыдущем этапе, можно не запускать, но в report явно указать:

```text
Tests not rerun during publish; last verified in Stage04E-R5 finalization.
```

Предпочтительно rerun.

---

# 8. GitHub auth and remote check

Проверить GitHub CLI:

```powershell
gh --version
gh auth status
```

Если `gh` недоступен, использовать обычный git remote HTTPS/SSH, но только если credentials настроены.

Проверить repo:

```powershell
gh repo view apc90210/tbootit
```

Варианты:

## Repo exists

Проверить remote.

Если `origin` отсутствует:

```powershell
git remote add origin https://github.com/apc90210/tbootit.git
```

Если `origin` есть, проверить:

```powershell
git remote get-url origin
```

Если origin указывает не на `apc90210/tbootit`:

```text
STOP
не менять remote без owner confirmation
сообщить текущий origin
```

Если origin правильный — продолжить.

## Repo does not exist

Создать private repo:

```powershell
gh repo create apc90210/tbootit --private --source . --remote origin
```

Если `gh repo create` спрашивает подтверждение или нет auth:

```text
STOP
сообщить, что нужно войти в GitHub CLI или создать repo вручную
```

Не создавать public repo без отдельного owner approval.

---

# 9. Push

Определить текущую ветку:

```powershell
$branch = git branch --show-current
```

Если ветка `main` или `master`:

```powershell
git push -u origin $branch
```

Если локальная ветка отличается:

```text
STOP или спросить owner confirmation.
```

Не использовать force.

После push проверить:

```powershell
git status --short --untracked-files=all
git log --oneline -1
git remote -v
```

Если `gh` доступен:

```powershell
gh repo view apc90210/tbootit --web
```

или без открытия browser:

```powershell
gh repo view apc90210/tbootit
```

---

# 10. GitHub publish report

Создать:

```text
reports/github_publish_apc90210_tbootit_report.md
```

Структура:

```text
# GitHub Publish Report — apc90210/tbootit

## STATUS

PUSHED / BLOCKED

## PROMPT_DISCOVERY

PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:

## PRE_PUSH_GIT_STATE

Branch:
HEAD:
Worktree:
Remote before:

## HYGIENE_SCAN

Runtime tracked files:
Ignored runtime status:
Temp/debug tracked:
Result:

## SECRET_SCAN

Command:
Findings:
Decision:

## TESTS

Core:
Inventory:
Avito:

## GITHUB_REMOTE

Repo existed:
Remote added/verified:
Remote URL:

## PUSH_RESULT

Command:
Branch pushed:
Remote HEAD:
GitHub repo:

## FINAL_GIT_STATUS

## BLOCKERS

## FINAL_STATUS

If pushed:

TECHNOREBOOT_GITHUB_PUBLISH_APC90210_TBOOTIT_PUSHED

If blocked:

TECHNOREBOOT_GITHUB_PUBLISH_APC90210_TBOOTIT_BLOCKED
```

---

# 11. Logs

Append to:

```text
logs/2026-07-03.md
```

Include:

```text
GitHub publish start
prompt filename
preflight status
secret scan result
remote status
push result or blocker
final status
```

---

# 12. Commit report before push or after push

If publish report/log/prompt copy are new files, commit them before final push:

```powershell
git add reports/github_publish_apc90210_tbootit_report.md
git add logs/2026-07-03.md
git add .agents/received_prompts/TECHNOREBOOT_GITHUB_PUBLISH_APC90210_TBOOTIT_PROMPT.md

git commit -m "Prepare GitHub publish report"
```

Then push.

Use targeted add only.

Forbidden:

```text
git add .
git add -A
git add -u
git commit --amend
```

---

# 13. Definition of Done

Готово, если:

```text
worktree clean before push or only publish report/log committed
runtime/temp tracked scan clean
secret scan clean
remote points to apc90210/tbootit
repo exists or was created private
push completed without force
final git status clean
report created
final chat report detailed
```

---

# 14. Final answer required from agent

Финальный ответ должен быть подробным в чат.

Если push successful:

```text
FINAL_STATUS:
TECHNOREBOOT_GITHUB_PUBLISH_APC90210_TBOOTIT_PUSHED

GITHUB_REPO:
https://github.com/apc90210/tbootit
```

Если blocked:

```text
FINAL_STATUS:
TECHNOREBOOT_GITHUB_PUBLISH_APC90210_TBOOTIT_BLOCKED

BLOCKERS:
...
```
