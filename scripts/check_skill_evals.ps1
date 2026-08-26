$ErrorActionPreference = "Stop"

$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCommand) {
    [Console]::Error.WriteLine("verification_tool_unavailable:python")
    exit 2
}
& $pythonCommand.Source -I (Join-Path $PSScriptRoot "check_skill_evals.py")
exit $LASTEXITCODE
