# Отчёт о реализации и верификации: Stage 07A-R1-R1
## Минимальный доступ по сертификатам (Minimal Certificate Access Gateway)

### 1. Статус этапа
- **Этап:** Stage 07A-R1 / Stage 07A-R1-R1 (Верификация, ротация пароля и финализация)
- **Итоговый статус:** `TECHNOREBOOT_STAGE07A_R1_READY_FOR_OWNER_CHECK`
- **Ветка:** `main`

---

### 2. Реализованная архитектура
1. **Nginx mTLS Gateway (`technoreboot-gateway`)**:
   - Порт: `8443` (готово к привязке `443` в production).
   - Требование сертификата: `ssl_verify_client on;` с проверкой по локальному `ca.crt`.
   - Проверка статуса в реальном времени: `auth_request /internal-auth/verify;`.
   - Защита от спуфинга: удаление входящих клиентских заголовков и проброс доверенных заголовков `X-Client-*`.

2. **Встроенный центр сертификации (`admin-shell/app/auth_manager.py`)**:
   - Автоматическая генерация Root CA, ключей и серверных сертификатов при первом старте.
   - Выпуск сертификата Владельца (`owner.crt`, `owner.key`, `owner.p12`).
   - Защита Владельца: программный запрет отзыва сертификата OWNER (`Cannot revoke OWNER certificate`).
   - Выпуск сертификатов для персонала/устройств через API и интерфейс с выдачей `.p12` и одноразового пароля.
   - Мгновенный отзыв сертификатов через реестр `data/auth/registry.json`.

3. **Веб-интерфейс (`admin-shell/app/templates/certificates.html`)**:
   - Доступен по пути `/certificates` только по сертификату Владельца (`X-Client-Is-Owner: 1`).
   - Попытка доступа с сертификатом USER или без сертификата возвращает `403 Forbidden`.

---

### 3. Ротация пароля бандла Владельца (OWNER PKCS#12)
- **OWNER_CERT_IDENTITY_UNCHANGED:** `true` (серийный номер и SHA-256 отпечаток сертификата идентичны до и после).
- **OWNER_P12_PASSWORD_ROTATED:** `true` (сгенерирован новый криптостойкий пароль, бандл пересобран).
- **OWNER_P12_PATH:** `data\auth\certificates\owner.p12`
- **OWNER_PASSWORD_FILE_PATH:** `data\auth\owner_password.txt`
- **CA_UNCHANGED:** `true` (Root CA не пересоздавался, все выданные сертификаты сохраняют валидность).
- Пароль сохранён локально в файле и не выводился в логи, чат или git.

---

### 4. Результаты сквозной верификации mTLS (Скрипт `scripts/verify_stage07a_mtls.py`)
Сквозной скрипт протестировал все сценарии безопасности через живой HTTPS шлюз:

| Тест | Проверяемое условие | Результат | Детали |
|---|---|---|---|
| **TEST A** | Базовые файлы и артефакты CA/OWNER | **PASS** | `ca.crt`, `owner.crt`, `owner.key`, `owner.p12`, `owner_password.txt` существуют |
| **TEST B** | Запрос без сертификата клиента | **PASS** | HTTP `403 Forbidden` на уровне шлюза |
| **TEST C** | Доступ Владельца к приложению | **PASS** | HTTP `200 OK` (главная страница открывается) |
| **TEST D** | Доступ Владельца к панели сертификатов | **PASS** | `/certificates` = 200, `/admin-api/certificates` = 200 |
| **TEST E** | Создание сертификата USER | **PASS** | Сертификат создан со статусом `ACTIVE`, `.p12` скачивается |
| **TEST F** | Доступ USER к приложению | **PASS** | HTTP `200 OK` (операционный доступ разрешён) |
| **TEST G** | Доступ USER к панели сертификатов | **PASS** | `/certificates` = 403, `/admin-api/certificates` = 403 |
| **TEST H** | Отзыв сертификата USER | **PASS** | Статус в реестре изменён на `REVOKED` |
| **TEST I** | Доступ отозванного USER | **PASS** | HTTP `403 Forbidden` (доступ заблокирован) |
| **TEST J** | Попытка отзыва сертификата OWNER | **PASS** | HTTP `403 Forbidden` (отзыв владельца аппаратно заблокирован) |
| **TEST K** | Сохранение состояния на диске | **PASS** | Реестр `registry.json` консистентен |
| **TEST L** | Попытка подделки заголовков без сертификата | **PASS** | HTTP `403 Forbidden` (шлюз не доверяет заголовкам клиента) |
| **TEST M** | Попытка обхода через внутренние порты модулей | **PASS** | Core (8000) = 404, Admin (8011) = 403 без шлюза |
| **RESTART** | Персистентность после перезапуска контейнеров | **PASS** | Перезапуск `gateway` и `admin-shell` проверен, все тесты PASS |

---

### 5. Точные результаты тестовых наборов (Exact Test Results)
Команды выполнены непосредственно в среде проекта:

1. `pytest admin-shell/tests`
   - **Результат:** `60 passed, 0 failed` (время: 15.94s)
2. `docker compose exec -T core pytest`
   - **Результат:** `26 passed, 0 failed` (время: 6.64s)
3. `docker compose exec -T inventory-sales-module pytest`
   - **Результат:** `124 passed, 0 failed` (время: 3.05s)
4. `docker compose exec -T repairs-module pytest`
   - **Результат:** `34 passed, 0 failed` (время: 1.31s)
5. `docker compose exec -T avito-module pytest`
   - **Результат:** `95 passed, 0 failed` (время: 11.62s)

---

### 6. Проверка секретов и git-безопасность
- **RUNTIME_AUTH_IGNORED:** `true` (директории `data/auth/`, `auth-data/` и файлы `*.key`, `*.crt`, `*.p12`, `*.password` добавлены в `.gitignore`).
- **TRACKED_SECRET_SCAN:** `CLEAN` (в отслеживаемых файлах проекта нет закрытых ключей, сертификатов или паролей).
- **STAGED_SECRET_SCAN:** `CLEAN` (в индекс git включаются только программный код, тесты, документация и конфигурации).

---

### 7. Готовность
Этап Stage 07A-R1-R1 готов к ручной проверке владельцем.
- **BACKUP_STAGE_NOT_STARTED:** `true`
- **INTERNET_DEPLOYMENT_NOT_STARTED:** `true`
- **DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE:** `true`
