# Patent Analysis Agent — 전체 테스트 (PowerShell)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

Set-Location (Join-Path $Root "backend")
python -m pip install -q -r requirements.txt -r requirements-dev.txt
python -m pytest tests -v --tb=short
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Set-Location (Join-Path $Root "web")
npm run test
exit $LASTEXITCODE
