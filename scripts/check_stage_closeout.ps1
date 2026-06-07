$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

Write-Host "== RepoPilot stage closeout check =="
Write-Host "Repository: $repoRoot"

Write-Host ""
Write-Host "== openspec list =="
$openSpecList = openspec list 2>&1
$openSpecList | ForEach-Object { Write-Host $_ }
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
if (($openSpecList -join "`n") -notmatch "No active changes found") {
    Write-Host "Active OpenSpec changes remain. Closeout requires no active changes, or a recorded exception." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "== openspec validate --all =="
openspec validate --all
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "== stage docs drift scan =="
powershell -ExecutionPolicy Bypass -File scripts/check_stage_docs.ps1
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "== skill eval structure scan =="
powershell -ExecutionPolicy Bypass -File scripts/check_skill_evals.ps1
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "== git diff --check =="
git diff --check
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Stage closeout check passed."
