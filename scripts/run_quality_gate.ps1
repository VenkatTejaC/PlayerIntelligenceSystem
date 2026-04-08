$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$pythonExe = Join-Path $repoRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    Write-Error "Virtual environment Python not found at $pythonExe"
}

Set-Location $repoRoot

Write-Host "Running unit and integration tests with coverage >= 70%..." -ForegroundColor Cyan
& $pythonExe -m pytest --cov=. --cov-report=term-missing --cov-fail-under=70 -q

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "Quality gate passed. Push may continue." -ForegroundColor Green
