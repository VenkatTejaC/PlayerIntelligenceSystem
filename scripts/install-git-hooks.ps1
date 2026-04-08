$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

git config core.hooksPath scripts/git-hooks

Write-Host "Configured Git hooks path to scripts/git-hooks" -ForegroundColor Green
Write-Host "Pre-push hook is now active for this repository." -ForegroundColor Green
