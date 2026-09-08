# Архитектура и спецификация: Stage 07B-R2 — Веб-интерфейс резервного копирования и восстановления

## 1. Назначение и контекст

В рамках этапа Stage 07B-R2 реализован полноценный веб-ориентированный механизм резервного копирования и восстановления системы ТехноРебут, доступный **исключительно Владельцу (OWNER)** через веб-интерфейс панели управления `admin-shell`.

### Решаемые задачи:
- **Отказ от CLI/CMD для Владельца:** Исключена необходимость входа на сервер по RDP/SSH или ручного запуска batch-скриптов (`backup_full.cmd`, `restore_full.cmd` удалены).
- **Единый графический интерфейс:** Управление созданием архива и восстановлением сосредоточено на странице `/backups` защищенного веб-интерфейса `admin-shell`.
- **Строгая авторизация:** Доступ к веб-странице и соответствующим REST API эндпоинтам защищен взаимной аутентификацией TLS (mTLS) и валидацией роли `is_owner=True`.
- **Изоляция изменяемых данных:** Резервная копия включает только актуальное состояние БД, медиа-файлов, PKI-сертификатов и настроек, полностью исключая исходный код, историю Git и артефакты сборки Docker.

---

## 2. Архитектурная схема

```mermaid
graph TD
    subgraph Client Browser
        OwnerCert[Браузер с сертификатом OWNER]
        UserCert[Браузер с сертификатом USER]
    end

    subgraph Gateway [Nginx Gateway :8443]
        SSLVerify[mTLS Handshake & ssl_verify_client optional]
        AuthSubreq[auth_request /internal-auth/verify]
    end

    subgraph AdminShell [Admin Shell :8010]
        VerifyEndpoint[/internal-auth/verify]
        RequireOwner[_require_owner check]
        PageBackups[GET /backups]
        DownloadAPI[POST /admin-api/backups/download]
        RestoreAPI[POST /admin-api/backups/restore]
        BackupService[app/backup_service.py]
    end

    subgraph PersistentData [Mounted Volumes /data]
        DB[(data/db/technoreboot.db)]
        Storage[data/storage/product_photos/]
        Auth[data/auth/ - CA & Registry]
        Avito[data/avito-module/]
    end

    OwnerCert -->|mTLS| SSLVerify
    UserCert -->|mTLS| SSLVerify

    SSLVerify --> AuthSubreq
    AuthSubreq --> VerifyEndpoint
    VerifyEndpoint -->|Validate Serial & Registry| Auth

    SSLVerify -->|Proxy Pass| RequireOwner
    RequireOwner -->|200 OK if OWNER| PageBackups
    RequireOwner -->|403 Forbidden if USER| UserCert

    PageBackups --> BackupService
    DownloadAPI --> BackupService
    RestoreAPI --> BackupService

    BackupService -->|Hot Backup / iter-dump| DB
    BackupService -->|Sync Photos| Storage
    BackupService -->|Sync Registry & Keys| Auth
    BackupService -->|Sync State| Avito
```

---

## 3. Компоненты системы

### 3.1. Маршруты Admin Shell (`admin-shell/app/main.py`)
1. **`GET /backups`**:
   - Рендерит шаблон `backups.html`.
   - Защищен проверкой `_require_owner(request)`: возвращает 403 при отсутствии флага `X-Auth-Is-Owner == "1"`.
2. **`POST /admin-api/backups/download`**:
   - Инициирует создание резервной копии через `backup_service.create_backup()`.
   - Формирует архив `TECHNOREBOOT_BACKUP_YYYY-MM-DD_HHMMSS.zip`.
   - Передает файл клиенту через `FileResponse` с заголовком `Content-Disposition: attachment` и фоновой задачей (`BackgroundTasks`) на удаление временного файла после завершения передачи.
3. **`POST /admin-api/backups/restore`**:
   - Принимает загружаемый multipart ZIP-файл (`UploadFile`).
   - Сохраняет во временную директорию и вызывает `backup_service.restore_backup()`.
   - Возвращает JSON-структуру с результатом операции: `{"status": "ok", "message": "...", "details": {...}}` или `{"status": "error", "message": "..."}` с HTTP 400.

### 3.2. Сервис резервного копирования (`admin-shell/app/backup_service.py`)
- **`create_backup()`**:
  - Создает снимок БД с помощью встроенного в SQLite метода `src_conn.backup(dst_conn)`.
  - Формирует логический SQL-дамп всех таблиц (`.iterdump()`).
  - Копирует каталог хранения фотографий товаров `storage/product_photos/`.
  - Упаковывает сертификаты и ключи mTLS PKI (`auth/ca/`, `auth/certificates/`, `registry.json`, `owner_password.txt`).
  - Формирует структурированный `manifest.json` со статистикой таблиц, хэшем git-ревизии и отпечатками SHA-256 корневого CA и сертификата Владельца.
- **`validate_backup()`**:
  - Проверяет целостность архива (`testzip()`).
  - Контролирует присутствие `manifest.json`, корректность версии формата (`1.0`).
  - Проверяет наличие обязательных компонентов (`database`, `storage`, `auth`) и ключевых файлов (`technoreboot.db`, `ca.crt`, `owner.crt`, `registry.json`).
- **`restore_backup()`**:
  - Выполняет валидацию.
  - Распаковывает архив в изолированную временную директорию.
  - Атомарно перезаписывает базу данных `technoreboot.db`.
  - Синхронизирует директорию фотографий `storage/` и модуль безопасности `auth/`, сохраняя структуру каталогов и дескрипторы точек монтирования.
  - Проверяет целостность восстановленной базы данных и неизменность отпечатков CA и сертификата Владельца.

### 3.3. Пользовательский интерфейс (`admin-shell/app/templates/backups.html`)
- Выполнен в строгом едином неоново-темном стиле панели управления (Industrial Cyberpunk / Dark Glow).
- Содержит две основные секции:
  1. **Создание резервной копии:** описание состава, кнопка `[ Скачать резервную копию ]` с индикатором процесса.
  2. **Восстановление системы:** поле выбора ZIP-архива, предупреждающий блок о перезаписи текущих данных, кнопка `[ Восстановить систему ]` с подтверждением через модальный диалог (`confirm()`), полоса прогресса и блок детального статуса.

---

## 4. Гарантии безопасности

1. **Защита данных Владельца:** Сертификаты Владельца, пароль `owner_password.txt` и закрытые ключи сохраняются в архиве в зашифрованном/защищенном виде.
2. **Исключение кода:** В архиве отсутствуют `.py`, `.git`, `.env` (если не задан) и служебные файлы проекта.
3. **Сохранение сессии mTLS:** При восстановлении отпечатки CA и сертификата Владельца валидируются против манифеста; сертификат Владельца не инвалидируется, позволяя продолжать сессию в браузере без повторного импорта.
4. **Отказоустойчивость при поврежденном бэкапе:** При любой ошибке в архиве (битый zip, отсутствие `manifest.json`, неверный формат) операция прерывается до изменения файлов на диске.
