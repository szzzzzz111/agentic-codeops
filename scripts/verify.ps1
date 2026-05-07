$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

Write-Host "== RepoPilot 验证开始 =="
Write-Host "仓库目录: $repoRoot"

Write-Host ""
Write-Host "== 运行 pytest =="
pytest
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "== 运行 ruff check . =="
$ruffCommand = Get-Command ruff -ErrorAction SilentlyContinue
if ($ruffCommand) {
    ruff check .
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
} else {
    Write-Warning "当前环境未找到 ruff，已跳过静态检查。安装 dev 依赖后请运行: ruff check ."
}

Write-Host ""
Write-Host "== RepoPilot 验证完成 =="
