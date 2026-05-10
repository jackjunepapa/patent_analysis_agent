@echo off
REM Phase 4 Streamlit beta — start FastAPI on :8000 first.
cd /d "%~dp0streamlit_beta"
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
