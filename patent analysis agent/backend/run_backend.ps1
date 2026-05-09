# Patent Analysis Agent — backend FastAPI
# 실행 정책 오류 시(최초 1회): Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
Write-Host "Working directory: $(Get-Location)"
python -m pip install -r requirements.txt
python -m uvicorn api:app --reload --host 127.0.0.1 --port 8000
