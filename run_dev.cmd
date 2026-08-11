@echo off
setlocal
set "ROOT=%~dp0"
cd /d "%ROOT%"

echo ==============================================
echo BILLING ONE / SIS-FACT - DEV
echo Ruta: %ROOT%
echo Puerto: 5040
echo ==============================================

if not exist "%ROOT%wsgi.py" (
  echo ERROR: no existe wsgi.py
  exit /b 10
)

if not exist "%ROOT%config.ini" (
  echo ERROR: no existe config.ini
  exit /b 11
)

if not exist "%ROOT%.venv\Scripts\python.exe" (
  echo ERROR: no existe .venv\Scripts\python.exe
  exit /b 12
)

set "FLASK_APP="
set "FLASK_DEBUG=0"
set "FLASK_ENV="
set "PYTHONPATH=%ROOT%"

"%ROOT%.venv\Scripts\python.exe" -m flask --app wsgi:app run --no-debugger --no-reload --host 0.0.0.0 --port 5040
set "EXITCODE=%ERRORLEVEL%"
exit /b %EXITCODE%
