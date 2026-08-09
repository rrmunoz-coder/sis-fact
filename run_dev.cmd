@echo off
setlocal EnableExtensions

title SIS-FACT / Billing One - DEV

set "APP_DIR=%~dp0"
set "APP_DIR=%APP_DIR:~0,-1%"
set "ORACLE_CLIENT=C:\Oracle\product\instantclient_19_19"

echo ==================================================
echo Iniciando SIS-FACT / Billing One en modo desarrollo
echo ==================================================
echo.

cd /d "%APP_DIR%"

echo Carpeta actual:
cd
echo.

if not exist "wsgi.py" (
    echo ERROR: No existe wsgi.py en %APP_DIR%
    echo Estas parado en una carpeta incorrecta.
    pause
    exit /b 1
)

if not exist "config.ini" (
    echo ERROR: No existe config.ini en %APP_DIR%
    echo Copia config.ini.example a config.ini y completa los datos reales.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: No existe .venv\Scripts\python.exe
    echo Ejecuta primero:
    echo python -m venv .venv
    echo .venv\Scripts\python.exe -m pip install --upgrade pip
    echo .venv\Scripts\python.exe -m pip install -r requirements.txt
    pause
    exit /b 1
)

set "PYTHONPATH=%APP_DIR%"
set "FLASK_APP=wsgi:app"
set "FLASK_DEBUG=1"

if exist "%ORACLE_CLIENT%" (
    set "PATH=%ORACLE_CLIENT%;%APP_DIR%\.venv\Scripts;%PATH%"
) else (
    set "PATH=%APP_DIR%\.venv\Scripts;%PATH%"
    echo ADVERTENCIA: No existe Oracle Client en:
    echo %ORACLE_CLIENT%
    echo Si usas thick_mode=true, Oracle puede fallar.
    echo.
)

echo Validando Python y config.ini...
".venv\Scripts\python.exe" -c "import sys,configparser; print('Python:', sys.executable); p=configparser.ConfigParser(); p.read('config.ini', encoding='utf-8'); print('Secciones config:', p.sections())"

if errorlevel 1 (
    echo.
    echo ERROR validando config.ini o Python.
    pause
    exit /b 1
)

echo.
echo Iniciando Flask en puerto 5060...
echo.

".venv\Scripts\python.exe" -m flask --app wsgi:app run --host 0.0.0.0 --port 5060 --debug

echo.
echo Flask se detuvo.
pause
