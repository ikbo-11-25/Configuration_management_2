@echo off
setlocal
cd /d "%~dp0" || exit /b 1
set "PYTHONPATH=%~dp0src"
where py >nul 2>nul
if errorlevel 1 goto python_path
py -3 -m apt_graph %*
exit /b %errorlevel%
:python_path
python -m apt_graph %*
exit /b %errorlevel%
