@echo off
setlocal
set "ROOT=%~dp0..\"
set "NSSM=%~dp0nssm.exe"
set "PYTHON=%ROOT%.venv\Scripts\python.exe"
set "ENTRY=%ROOT%worker_entry.py"
set "SERVICE=BillingOne_Worker"

if not exist "%NSSM%" (echo ERROR: falta service\nssm.exe x64.& exit /b 10)
if not exist "%PYTHON%" (echo ERROR: falta %PYTHON%& exit /b 11)
if not exist "%ENTRY%" (echo ERROR: falta %ENTRY%& exit /b 12)
if not exist "%ROOT%config.ini" (echo ERROR: falta config.ini& exit /b 13)
if not exist "%ROOT%logs" mkdir "%ROOT%logs"

"%NSSM%" install %SERVICE% "%PYTHON%" "%ENTRY%"
if errorlevel 1 exit /b %ERRORLEVEL%
"%NSSM%" set %SERVICE% AppDirectory "%ROOT%"
"%NSSM%" set %SERVICE% Start SERVICE_AUTO_START
"%NSSM%" set %SERVICE% AppStdout "%ROOT%logs\billing_one_worker_out.log"
"%NSSM%" set %SERVICE% AppStderr "%ROOT%logs\billing_one_worker_err.log"
"%NSSM%" set %SERVICE% AppRotateFiles 1
"%NSSM%" set %SERVICE% AppRotateOnline 1
"%NSSM%" set %SERVICE% AppRotateBytes 10485760
"%NSSM%" start %SERVICE%
"%NSSM%" status %SERVICE%
