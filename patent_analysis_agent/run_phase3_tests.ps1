# Patent Analysis Agent — Phase 3 개발 현황만 검증 (이 스크립트는 `patent_analysis_agent` 저장소 루트에 두고 실행)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

Set-Location (Join-Path $Root "backend")
python -m pip install -q -r requirements.txt -r requirements-dev.txt
python -m pytest tests -m phase3 -v --tb=short
exit $LASTEXITCODE
