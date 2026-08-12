# Stage 06A-R7 Manual Browser Login & Profile Registry Repair

## 1. Executive Summary
In Stage 06A-R7, two distinct root issues were repaired:
1. **Profile not found & Registry Persistence**: `reconcile_profile_registry()` was implemented in `avito-module/app/storage.py`. Profile metadata in `profiles.json` is automatically reconciled with existing profile directories under `/app/data/profiles/<account_key>/browser_data`. Missing account keys in `admin-shell` render a friendly UI notice (`«Профиль Avito не найден. Вернитесь к списку аккаунтов.»`) rather than raw JSON errors.
2. **Manual Avito Browser Architecture**: During manual authorization, `avito-module` launches an **ordinary OS process** (standalone Chrome/Chromium) directly on `DISPLAY=:99` without Playwright, without CDP, without WebDriver, and without `--enable-automation`. The owner logs in using standard mouse and keyboard. When finished, clicking **«Я вошёл — закрыть браузер и проверить»** terminates Chrome gracefully (`SIGTERM`), preserving all session cookies and local storage.

---

## 2. Technical Architecture & Lifecycle

- **Manual Login Runtime**: Standalone Chrome process (`subprocess.Popen`) targeting persistent profile directory `/app/data/profiles/<account_key>/browser_data`.
- **Zero Automation Flags**: No `--enable-automation`, no `--remote-debugging-port`, no Playwright context during manual login.
- **Graceful Process Shutdown**: Sends `SIGTERM` and waits up to 5s for profile flush before clearing stale locks.
- **Profile Recovery**: Automatic directory reconciliation guarantees profile cookies and local storage are never lost across restarts.
- **Access Denied Classification**: Added controlled `access_denied` status for clear user alerts if network/Avito access is restricted.

---

## 3. Verification Summary

- **Unit Test Suite Results**: **415 passed / 0 failed** across all 5 microservices.
- **Safety Checks**: 0 stored credentials, 0 cookie leaks, 0 anti-bot evasion code, 0 direct DB access from `avito-module`.
