# 09 Development Workflow

## Рабочая папка

```powershell
C:\tbootit
```

## Общий порядок

1. Зафиксировать модуль.
2. Реализовать большой рабочий блок.
3. Запустить Docker.
4. Проверить API.
5. Проверить оболочку.
6. Создать отчет.
7. Сделать commit.
8. Передать пользователю на тестирование, если требуется.

## Команды запуска

```powershell
Set-Location C:\tbootit
docker compose up --build
```

## Проверка API

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/version
Invoke-RestMethod http://127.0.0.1:8000/api/admin/db/schema
```

## Проверка Shell

Открыть:

```text
http://127.0.0.1:8010
```

## Git

```powershell
git status
git add .
git commit -m "Implement Technoreboot Core MVP prototype"
```

## Отчеты

Каждый большой модуль должен иметь отчет в:

```text
reports/
```

## Документация

Документация должна обновляться вместе с кодом:

```text
docs/
```

## Принцип безопасности MVP

На первом этапе безопасность низкого уровня допустима, но:

- dev endpoints должны быть явно помечены;
- нельзя случайно удалять данные без подтверждения;
- нельзя хранить секреты в git;
- `.env` должен быть в `.gitignore`;
- `.env.example` можно хранить в git.
