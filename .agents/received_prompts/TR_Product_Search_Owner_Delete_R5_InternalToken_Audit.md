# TR — Product Search + OWNER Delete — R5 Internal Token Audit

R4 в целом успешен. Нужна последняя точечная проверка внутреннего `x-api-token` перед OWNER manual test.

## Цель

Убедиться, что новый внутренний токен является ТОЛЬКО service-to-service trust mechanism и никогда не используется как браузерная/пользовательская авторизация.

## Проверить

1. `x-api-token` НЕ должен:
   - попадать в браузер;
   - ожидаться от браузера;
   - храниться в HTML/JS;
   - возвращаться в response headers/body;
   - использоваться как признак OWNER для отображения UI.

2. OWNER UI должен определяться только существующей mTLS/OWNER-сессией через доверенный gateway/admin-shell слой.

3. В `inventory-sales-module/app/routers/products.py` проверить текущую логику `is_owner_request`.
   Если там OWNER определяется через `x-api-token`, исправить:
   - внутренний токен используется только между сервисами;
   - пользовательская роль OWNER приходит только из доверенного auth-контекста после проверки сертификата.

4. Проверить NGINX/admin-shell:
   - входящий клиентский `x-api-token` всегда удаляется/игнорируется;
   - входящий клиентский `x-auth-is-owner` всегда удаляется/перезаписывается;
   - оба доверенных заголовка формируются только серверной стороной.

5. Проверить конфигурацию токена:
   - LOCAL/dev может использовать dev-token;
   - production token НЕ должен быть захардкожен в репозитории;
   - production должен получать секрет через environment/secret;
   - не коммитить реальный production secret.

6. Проверить оба сценария:
   - обычный USER без OWNER сертификата не видит кнопку и не может удалить;
   - OWNER через штатный mTLS путь видит кнопку и получает разрешение на удаление;
   - spoofed `x-auth-is-owner: 1` без внутреннего trust context -> 403;
   - spoofed `x-api-token` снаружи не помогает.

## Тесты

Добавить/обновить regression tests, если нужно.

Повторно запустить:
- `tests/test_product_search_and_owner_delete.py`;
- `tests/test_hard_delete_audit.py`;
- `tests/test_stage11d_owner_bulk_delete.py`.

Production/VDS не трогать.
Не деплоить.

## Итог

Верни короткий отчёт:

1. PASS/FAIL.
2. Где хранится/откуда берётся internal token.
3. Попадает ли token в браузер — YES/NO.
4. Чем реально определяется OWNER в UI.
5. Можно ли spoof-ить оба заголовка снаружи.
6. Какие файлы изменены.
7. Результаты тестов.
8. `git status`.
9. Готово ли к OWNER manual test — YES/NO.

После отчёта остановиться.
