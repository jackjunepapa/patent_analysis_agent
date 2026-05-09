# Patent Analysis Agent — Phase 3 개발 현황 테스트만 실행 (백엔드 pytest -m phase3)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

Set-Location (Join-Path $Root "backend")
python -m pip install -q -r requirements.txt -r requirements-dev.txt
python -m pytest tests -m phase3 -v --tb=short
exit $LASTEXITCODE
