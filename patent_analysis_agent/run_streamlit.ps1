# Phase 4 Streamlit 베타 — FastAPI(127.0.0.1:8000)를 먼저 실행한 뒤 사용하세요.
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $Root "streamlit_beta")
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
