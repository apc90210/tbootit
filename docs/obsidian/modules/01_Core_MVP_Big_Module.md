# 01 Core MVP Big Module

## Цель

Создать полностью рабочий прототип ядра и внешнюю оболочку для тестирования.

## Входит

- Docker Compose.
- Core API.
- SQLite DB.
- Storage.
- Products API.
- Categories API.
- Customers API.
- Repairs API.
- Sales API.
- Photos API.
- Admin API.
- Admin/Test Shell.
- Документация.
- Отчет.

## Не входит

- полноценный сайт;
- полноценный Авито;
- сложная авторизация;
- роли;
- касса;
- 1С.

## Критерии готовности

```text
docker compose up --build
Core API работает
Shell работает
данные создаются
фото загружаются
БД видна
audit log работает
отчет создан
commit создан
```
