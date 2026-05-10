@echo off

setlocal

cd /d "%~dp0backend"

python -m pip install -q -r requirements.txt -r requirements-dev.txt

python -m pytest tests -m phase3 -v --tb=short

exit /b %ERRORLEVEL%

