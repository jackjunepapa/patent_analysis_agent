# Patent Analysis Agent — FastAPI 백엔드 (이 스크립트는 patent_analysis_agent\backend 에 두고 실행)
# 실행 정책 오류 시(최초 1회): Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
Write-Host "Working directory: $(Get-Location)"
python -m pip install -r requirements.txt
python -m uvicorn api:app --reload --host 127.0.0.1 --port 8000
