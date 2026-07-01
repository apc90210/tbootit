# 10 Testing and Acceptance

## Виды проверок

### Internal Self-Check

Выполняет агент.

Цель:

- убедиться, что модуль работает технически.

### Owner Manual Testing

Выполняет пользователь.

Цель:

- убедиться, что модуль понятен и подходит для реальной работы.

## Минимальные проверки Core MVP

```text
docker compose up --build
Core health
API docs
Admin Shell
создание товара
просмотр товара
фото
структура БД
клиент
ремонт
продажа
audit log
сохранение после перезапуска
```

## Owner acceptance status

Возможные статусы:

```text
OWNER_MANUAL_TEST_PASSED
OWNER_MANUAL_TEST_PASSED_WITH_NOTES
OWNER_MANUAL_TEST_FAILED
```

## Если есть замечания

Замечания фиксируются отдельным списком:

```text
1. Раздел.
2. Что делал.
3. Что ожидал.
4. Что произошло.
5. Насколько критично.
```

После этого создается repair module или patch stage.
