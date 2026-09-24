# TR — Production Code-Only Deploy With Backup — R1

Проект: Техноребут / tbootit.

Нужно выполнить безопасный production deploy ВСЕХ текущих локальных изменений на основной VDS.

Канонический production VDS: 144.31.15.88.

## Главный принцип

PRODUCTION DATABASE И MEDIA — ИСТОЧНИК ИСТИНЫ.

Текущие production данные должны быть сохранены полностью:
- товары;
- продажи;
- ремонты;
- остатки;
- история;
- audit log;
- Avito-данные;
- фотографии/media;
- сертификаты/конфигурация.

Этот deploy должен быть CODE-ONLY.

НЕЛЬЗЯ:
- заменять production БД локальной БД;
- копировать локальный *.db / *.sqlite / *.sqlite3 на VDS;
- пересоздавать БД;
- делать seed;
- очищать БД;
- выполнять destructive migration;
- удалять volumes;
- использовать `docker compose down -v`;
- пересоздавать media из локальной копии;
- трогать production данные ради тестов.

## 1. Сначала зафиксировать LOCAL

Перед deploy:

1. Проверить branch / HEAD / git status.
2. Просмотреть все текущие изменения.
3. Убедиться, что в commit НЕ попадут:
   - локальные БД;
   - временные файлы;
   - `.agents.zip`;
   - scratch/test artifacts, которые не нужны проекту;
   - secrets;
   - production credentials.
4. Выполнить целевые тесты текущего этапа.
5. Если тесты PASS — создать нормальный commit со всеми относящимися к реализованным этапам изменениями.
6. Push в основной remote/branch согласно текущей принятой схеме проекта.

Не делать history rewrite / force push.

## 2. PRE-DEPLOY BACKUP НА VDS — ОБЯЗАТЕЛЬНО

До изменения production code сделать checkpoint.

Создать отдельную папку backup с timestamp.

Обязательно сохранить:

### Database
Сделать консистентную резервную копию текущей production SQLite БД штатным безопасным способом SQLite (`.backup` / backup API), а не простым рискованным копированием работающего файла.

После backup проверить:
- backup файл существует;
- размер > 0;
- `PRAGMA quick_check` на backup = `ok`;
- `PRAGMA foreign_key_check` на backup = пусто.

### Media
Сделать резервную копию production media/photo storage.

### Configuration
Сохранить используемые production:
- compose files;
- nginx/gateway config;
- env/config references БЕЗ вывода секретов в отчёт;
- текущий production git HEAD / image/container state.

### Current code
Зафиксировать текущий production commit/HEAD, чтобы можно было быстро откатить код.

В отчёте указать путь backup и размеры DB/media backup, но НЕ публиковать секреты.

## 3. PRE-DEPLOY DATA BASELINE

До deploy снять контрольные показатели production БД как минимум:

- количество products;
- sales;
- sale_items;
- repairs;
- repair history/status history;
- stock movements;
- audit log;
- product photos / media-linked records;
- основные денежные/продажные totals, если в текущей схеме есть надёжный запрос.

Также выполнить:
- `PRAGMA quick_check`;
- `PRAGMA foreign_key_check`.

Сохранить baseline в deployment report.

## 4. SCHEMA GUARD

До перезапуска сравнить ожидаемую схему текущего кода с production.

Для этого этапа ожидается CODE-ONLY deploy.

Если обнаружится, что новый код требует:
- ALTER TABLE;
- CREATE/DROP COLUMN;
- migration;
- несовместимое изменение схемы,

НЕ выполнять это автоматически.

Остановить deploy и вернуть BLOCKED с точным объяснением.

Никаких автоматических миграций БД в рамках этой задачи.

## 5. DEPLOY

После успешного backup/checkpoint:

1. Обновить на VDS только код из принятого commit.
2. Не заменять `.env` production локальным.
3. Не заменять DB/media.
4. Не удалять persistent volumes.
5. Пересобрать/перезапустить только необходимые Docker services.
6. Использовать production compose/config.
7. Убедиться, что контейнеры поднялись без restart loop.

Если используется новый internal API token/trust-boundary config:
- production secret должен поступать через production environment/secret;
- НЕ использовать захардкоженный LOCAL `dev-token` как production secret;
- не выводить secret в лог/отчёт.

## 6. POST-DEPLOY VALIDATION

После запуска проверить:

### Health
- gateway/nginx;
- core;
- admin-shell;
- inventory-sales-module;
- остальные затронутые сервисы.

### Database integrity
На ИСХОДНОЙ production БД выполнить:
- `PRAGMA quick_check` -> `ok`;
- `PRAGMA foreign_key_check` -> пусто.

### Data preservation
Повторить baseline counts и сравнить с PRE-DEPLOY.

Deploy не должен сам менять бизнес-данные.

Если counts отличаются без объяснимой пользовательской активности во время deploy — считать это BLOCKER и расследовать.

Особенно подтвердить сохранность:
- продаж;
- ремонтов;
- товаров;
- остатков;
- audit/history;
- media.

### Functional smoke tests — NON-DESTRUCTIVE
Проверить:
- сайт/админка открываются;
- список товаров открывается;
- поиск товара работает;
- поиск кириллицы в разном регистре работает;
- существующие продажи/ремонты читаются;
- OWNER UI загружается через штатный сертификатный путь;
- delete endpoint без OWNER/internal trust не даёт несанкционированный доступ.

НЕ удалять реальные production товары для smoke test.
НЕ создавать тестовые продажи/ремонты в production.

## 7. ROLLBACK

Если после обновления:
- сервисы не стартуют;
- schema guard нарушен;
- БД integrity check не проходит;
- пропали/изменились данные;
- критический функционал сломан,

немедленно:
1. остановить дальнейшие изменения;
2. откатить CODE к pre-deploy production HEAD;
3. БД не трогать, если она не была изменена;
4. если БД неожиданно была повреждена/изменена — использовать pre-deploy backup только после фиксации причины и проверки backup integrity;
5. вернуть отчёт BLOCKED/ROLLED_BACK.

## 8. Итоговый отчёт

Вернуть короткий, но конкретный отчёт:

1. LOCAL commit hash, который задеплоен.
2. PRE-deploy production HEAD.
3. Путь/имя DB backup и результат его integrity checks.
4. Путь/имя media backup.
5. PRE/POST counts ключевых таблиц.
6. Schema Guard: PASS/FAIL.
7. Какие контейнеры пересобраны/перезапущены.
8. Health checks.
9. Production DB `quick_check`.
10. Production DB `foreign_key_check`.
11. Smoke tests.
12. Подтверждение: production DB/media НЕ заменялись локальными.
13. Подтверждение: продажи/ремонты/товары/остатки сохранены.
14. Текущий production HEAD.
15. `git status` LOCAL и VDS.
16. FINAL_STATUS: PASS / BLOCKED / ROLLED_BACK.

Если всё PASS — после отчёта остановиться.

Не выполнять дополнительных изменений без следующего задания.
