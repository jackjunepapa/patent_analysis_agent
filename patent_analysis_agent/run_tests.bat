@echo off
setlocal
cd /d "%~dp0backend"
python -m pip install -q -r requirements.txt -r requirements-dev.txt
python -m pytest tests -v --tb=short
if errorlevel 1 exit /b 1
cd ..\web
call npm run test
