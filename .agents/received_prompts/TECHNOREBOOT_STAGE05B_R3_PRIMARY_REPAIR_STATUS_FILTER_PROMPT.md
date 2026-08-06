# PROMPT - Техноребут / Stage05B-R3 Primary Repair Status Filter

## Роль

Ты senior FastAPI/Jinja2 developer, UX engineer и release QA проекта «Техноребут».

Репозиторий:

```powershell
C:\tbootit
```

Нужно выполнить точечную доработку реестра ремонтов.

Stage05C не начинать.

## 1. Требование владельца

На основной странице ремонтов отсутствует главный рабочий фильтр:

```text
Статус ремонта
```

Страница:

```text
http://localhost:8040/repairs
```

Добавить хорошо заметный выпадающий список со всеми существующими статусами ремонта.

## 2. Варианты фильтра

Первый пункт:

```text
Все статусы
```

Остальные значения брать из существующего Core options/status contract:

```text
Принят
Диагностика
Ожидает клиента
Ожидает запчасти
В ремонте
Готов
Ремонт невозможен
Выдан
Отменён
```

Использовать точные текущие системные значения и русские подписи.

Не добавлять новые статусы и не дублировать список вручную в HTML, если Core уже возвращает options.

## 3. Core API

Проверить существующую поддержку:

```text
GET /api/repairs?status=diagnostics
```

Если фильтр уже есть:

```text
не переписывать;
подключить его к UI;
добавить недостающие тесты.
```

Если отсутствует:

```text
реализовать точную фильтрацию по одному статусу.
```

Не использовать substring matching.

Неизвестный status не должен вызывать HTTP 500.

## 4. Размещение в UI

Фильтр разместить в верхней части реестра и сделать первым основным фильтром.

Рекомендуемый порядок:

```text
1. Статус ремонта
2. Поиск
3. Приоритет
4. Тип устройства
5. Ответственный
6. Даты
```

Не прятать статус в дополнительный блок, меню или модальное окно.

## 5. Поведение

При выборе статуса:

```text
отображаются только ремонты выбранного статуса;
выбранное значение сохраняется после обновления страницы;
URL содержит status=<code>;
смена статуса сбрасывает page на 1.
```

Допустима кнопка «Применить» или автоматическая отправка формы через простой `onchange`.

Без JavaScript фильтр также должен работать через submit формы.

## 6. Совместная работа

Фильтр статуса должен одновременно работать с:

```text
q
priority
device_type
assigned_to
date_from
date_to
customer_phone
serial_number
page
page_size
sort
```

Пример:

```text
/repairs?status=diagnostics&q=ноутбук&priority=high
```

Нельзя удалять остальные query parameters при выборе статуса.

## 7. Пагинация

Ссылки пагинации должны сохранять:

```text
status
q
priority
device_type
assigned_to
date_from
date_to
sort
page_size
```

При изменении `status`:

```text
page=1
```

## 8. Сброс

Добавить или проверить кнопку:

```text
Сбросить фильтры
```

Она ведёт на:

```text
/repairs
```

После сброса:

```text
Статус ремонта = Все статусы
остальные фильтры очищены
page=1
```

## 9. Пустой результат

Если записей нет:

```text
Ремонты с выбранным статусом не найдены.
```

Показать кнопку сброса фильтров.

Не показывать пустую таблицу без объяснения или raw JSON.

## 10. Не делать

На этом этапе не добавлять:

```text
счётчики по статусам;
дашборд;
графики;
канбан;
вкладки;
множественный выбор статусов;
сохранённые представления.
```

Нужен только один простой фильтр по одному статусу.

## 11. Core tests

Создать или обновить:

```text
core/tests/test_repairs_status_filter.py
```

Проверить:

```text
каждый существующий статус;
точное соответствие;
status + q;
status + priority;
status + device_type;
status + assigned_to;
status + date range;
status + pagination;
status + sort;
пустой результат;
неизвестный status без HTTP 500.
```

## 12. Repairs-module tests

Создать:

```text
repairs-module/tests/test_repairs_status_filter_ui.py
```

Проверить:

```text
видимый select «Статус ремонта»;
пункт «Все статусы»;
все фактические статусы;
русские подписи;
выбранное значение сохраняется;
status передаётся в Core;
остальные query parameters сохраняются;
pagination сохраняет status;
смена status сбрасывает page;
сброс очищает фильтры;
понятный пустой результат;
нет прямого доступа к DB.
```

## 13. Runtime-проверка

Открыть:

```text
http://localhost:8040/repairs
```

Проверить:

```text
Все статусы
Диагностика
Готов
Отменён
Выдан
Ожидает запчасти
```

Для каждого выбранного значения убедиться, что в таблице нет ремонтов другого статуса.

Проверить сочетания:

```text
status + поиск
status + тип устройства
status + дата
status + сортировка
status + пагинация
```

## 14. Prompt discovery

Найти только:

```text
TECHNOREBOOT_STAGE05B_R3_PRIMARY_REPAIR_STATUS_FILTER_PROMPT.md
```

Скопировать в:

```text
C:\tbootit\.agents\received_prompts\
```

В отчёте указать:

```text
PROMPT_SEARCH_DONE
PROMPT_USED
PROMPT_SOURCE
PROMPT_LOCAL_COPY
PROMPT_SHA256
```

## 15. Preflight

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

Ожидаемый HEAD:

```text
cafe9a8
```

## 16. Полные тесты

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
docker compose exec -T inventory-sales-module pytest
docker compose exec -T avito-module pytest
docker compose exec -T repairs-module pytest
```

До и после тестов сравнить SHA256 live DB и counts.

## 17. Safety scans

```powershell
git grep -n -I "drop_all\|DROP TABLE\|DELETE FROM" -- core/app core/tests inventory-sales-module/app inventory-sales-module/tests repairs-module
```

```powershell
git grep -n -I "create_engine\|SessionLocal\|sqlite\|technoreboot.db\|data/db\|sqlalchemy\|SELECT .* FROM\|INSERT INTO\|UPDATE .* SET\|DELETE FROM" -- repairs-module/app
```

```powershell
git ls-files | Select-String -Pattern "tbootit\.db|technoreboot\.db|\.sqlite|\.sqlite3|data/db|__pycache__|\.pytest_cache"
```

## 18. Документация

Создать:

```text
docs/stage05b_r3_primary_repair_status_filter.md
reports/stage05b_r3_primary_repair_status_filter_report.md
```

Обновить:

```text
logs/2026-08-05.md
```

## 19. Git

Только targeted add.

Возможные файлы:

```powershell
git add core/app/routers/repairs.py
git add core/tests/test_repairs_status_filter.py
git add repairs-module/app/routers/repairs.py
git add repairs-module/app/templates/repairs_list.html
git add repairs-module/app/templates/repair_list.html
git add repairs-module/tests/test_repairs_status_filter_ui.py
git add docs/stage05b_r3_primary_repair_status_filter.md
git add reports/stage05b_r3_primary_repair_status_filter_report.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE05B_R3_PRIMARY_REPAIR_STATUS_FILTER_PROMPT.md
git add -f logs/2026-08-05.md
```

Не добавлять несуществующие файлы.

Запрещено:

```text
git add .
git add -A
git add -u
```

Коммит:

```powershell
git commit -m "Add primary repair status filter"
git push origin main
```

## 20. Definition of Done

Готово только если:

```text
на странице ремонтов есть заметный фильтр статуса;
есть «Все статусы»;
есть все существующие статусы;
options берутся из Core;
фильтрация точная;
выбор сохраняется;
работает совместно с другими фильтрами;
pagination сохраняет status;
смена status сбрасывает page;
сброс работает;
пустой результат понятен;
неизвестный status не вызывает 500;
Core safe tests PASS;
Inventory PASS;
Avito PASS;
Repairs PASS;
live DB не меняется от tests;
safety scans clean;
targeted commit;
push;
clean Git;
owner manual check required.
```

## 21. Owner check guide

```text
1. Открыть http://localhost:8040/repairs
2. Найти фильтр «Статус ремонта»
3. Выбрать «Диагностика»
4. Проверить, что показаны только ремонты в диагностике
5. Выбрать «Готов»
6. Проверить, что показаны только готовые ремонты
7. Совместить статус с поиском
8. Совместить статус с типом устройства
9. Перейти на следующую страницу
10. Проверить сохранение статуса
11. Нажать «Сбросить фильтры»
12. Проверить возврат ко всем статусам
```

## 22. Финальный статус

Успех:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE05B_R3_PRIMARY_REPAIR_STATUS_FILTER_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_STAGE05C_WITHOUT_OWNER_ACCEPTANCE: true
```

Проблема:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE05B_R3_PRIMARY_REPAIR_STATUS_FILTER_FAIL

BLOCKERS:
...
```
