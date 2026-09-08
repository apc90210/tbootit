@echo off
setlocal
cd /d "%~dp0.."
python "%~dp0backup_full.py" %*
exit /b %ERRORLEVEL%
