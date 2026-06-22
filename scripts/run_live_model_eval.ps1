$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$python = Get-Command "python" -ErrorAction SilentlyContinue
$py = Get-Command "py" -ErrorAction SilentlyContinue

if ($python) {
    & $python.Source -m evals.live_model_provider.runner
    if ($LASTEXITCODE -ne 9009) {
        exit $LASTEXITCODE
    }
}

if ($py) {
    & $py.Source -3 -m evals.live_model_provider.runner
    exit $LASTEXITCODE
}

$pytest = Get-Command "pytest" -ErrorAction SilentlyContinue
if ($pytest) {
    $scriptsDir = Split-Path -Parent $pytest.Source
    $environmentDir = Split-Path -Parent $scriptsDir
    $environmentPython = Join-Path $environmentDir "python.exe"
    if (Test-Path -LiteralPath $environmentPython) {
        & $environmentPython -m evals.live_model_provider.runner
        exit $LASTEXITCODE
    }
}

Write-Host "ERROR live model provider eval: PythonInterpreterUnavailable" -ForegroundColor Red
exit 2
