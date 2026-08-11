@echo off
chcp 65001 > nul
echo ===================================================
echo   Запуск информационной системы Техноребут
echo ===================================================
echo.

echo [1/3] Проверка состояния Docker Desktop...
docker info >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ОШИБКА] Docker Desktop не запущен или недоступен!
    echo Пожалуйста, запустите Docker Desktop и повторите запуск.
    echo.
    pause
    exit /b 1
)

echo [2/3] Запуск сервисов системы...
cd /d "%~dp0\.."
docker compose up -d
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ОШИБКА] Не удалось запустить контейнеры системы.
    echo Проверьте логи Docker.
    echo.
    pause
    exit /b 1
)

echo [3/3] Ожидание готовности системы (5 секунд)...
timeout /t 5 /nobreak > nul

echo.
echo ===================================================
echo   Система Техноребут успешно запущена!
echo   Открываем панель управления в браузере...
echo ===================================================
echo.

start http://localhost:8011/avito

exit /b 0
