
# PROMPT_SEARCH_RULES — обязательное правило поиска prompt-файлов

## Назначение

Агент обязан искать актуальный prompt не только в текущей папке проекта, но и во всех стандартных местах, где пользователь мог сохранить или скачать prompt.

Это правило обязательно для проекта:

```text
C:\tbootit
```

## Где искать prompt

Перед началом работы агент должен проверить следующие места:

```text
C:\tbootit
C:\tbootit\.agents
C:\tbootit\docs
C:\tbootit\docs\obsidian
C:\tbootit\prompts
C:\tbootit\logs\prompts
C:\Users\Apc\Downloads
```

## Какие файлы считать prompt-файлами

Искать файлы:

```text
*.md
*.txt
*PROMPT*
*prompt*
*ПРОМТ*
*промт*
```

## Обязательная PowerShell-проверка

Перед стартом реализации выполнить:

```powershell
Set-Location C:\tbootit

$PromptSearchRoots = @(
  "C:\tbootit",
  "C:\tbootit\.agents",
  "C:\tbootit\docs",
  "C:\tbootit\docs\obsidian",
  "C:\tbootit\prompts",
  "C:\tbootit\logs\prompts",
  "C:\Users\Apc\Downloads"
)

$PromptFiles = foreach ($Root in $PromptSearchRoots) {
  if (Test-Path $Root) {
    Get-ChildItem -Path $Root -Recurse -File -ErrorAction SilentlyContinue |
      Where-Object {
        $_.Name -match "prompt|PROMPT|промт|ПРОМТ" -or
        $_.Extension -in ".md", ".txt"
      } |
      Select-Object FullName, LastWriteTime, Length
  }
}

$PromptFiles | Sort-Object LastWriteTime -Descending | Format-Table -AutoSize
```

## Как выбрать актуальный prompt

Агент должен:

1. Найти все возможные prompt-файлы.
2. Отсортировать их по дате изменения.
3. Проверить названия и содержимое.
4. Выбрать prompt, который соответствует текущей задаче пользователя.
5. Если prompt найден в `C:\Users\Apc\Downloads`, скопировать его в проект.

## Копирование prompt из Downloads

Если актуальный prompt найден в:

```text
C:\Users\Apc\Downloads
```

агент должен сохранить локальную копию в проекте:

```text
C:\tbootit\.agents\received_prompts\
```

Команда:

```powershell
New-Item -ItemType Directory -Force -Path "C:\tbootit\.agents\received_prompts"

Copy-Item "C:\Users\Apc\Downloads\<prompt_file_name>" `
  "C:\tbootit\.agents\received_prompts\<prompt_file_name>" `
  -Force
```

## Логирование найденного prompt

Агент должен записать в отчет:

```text
PROMPT_SEARCH_DONE: true
PROMPT_SEARCH_ROOTS:
- C:\tbootit
- C:\tbootit\.agents
- C:\tbootit\docs
- C:\tbootit\docs\obsidian
- C:\tbootit\prompts
- C:\tbootit\logs\prompts
- C:\Users\Apc\Downloads

PROMPT_USED: <full path>
PROMPT_COPIED_TO_PROJECT: true/false
```

## Стоп-условие

Если найдено несколько похожих prompt-файлов и невозможно надежно определить актуальный, агент должен:

1. Не начинать реализацию.
2. Показать список найденных prompt.
3. Попросить пользователя выбрать нужный файл.

## Обязательная фиксация

Каждый отчет модуля должен содержать блок:

```text
## Prompt discovery

PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:
```
