@echo off
REM Patent Analysis Agent — FastAPI 백엔드 (이 파일은 patent_analysis_agent\backend 에 두고 실행)
cd /d "%~dp0"
echo [%CD%]
python -m pip install -r requirements.txt
python -m uvicorn api:app --reload --host 127.0.0.1 --port 8000
pause
