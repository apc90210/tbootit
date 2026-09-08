@echo off
setlocal
cd /d "%~dp0.."
python "%~dp0restore_full.py" %*
exit /b %ERRORLEVEL%
