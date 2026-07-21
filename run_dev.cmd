@echo off
setlocal
set FLASK_APP=wsgi:app
python -m flask --app wsgi:app run --host 0.0.0.0 --port 5060 --debug
endlocal
