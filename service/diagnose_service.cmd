@echo off
setlocal
set "NSSM=%~dp0nssm.exe"
set "SERVICE=BillingOne_Web"
if not exist "%NSSM%" (
  echo ERROR: falta service\nssm.exe
  exit /b 10
)
"%NSSM%" status %SERVICE%
"%NSSM%" get %SERVICE% Application
"%NSSM%" get %SERVICE% AppParameters
"%NSSM%" get %SERVICE% AppDirectory
netstat -ano | findstr ":5060"
