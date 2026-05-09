@echo off
REM Patent Analysis Agent — backend FastAPI (더블클릭 또는 cmd에서 실행)
cd /d "%~dp0"
echo [%CD%]
python -m pip install -r requirements.txt
python -m uvicorn api:app --reload --host 127.0.0.1 --port 8000
pause
