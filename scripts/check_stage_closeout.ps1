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
Write-Host "== formal review evidence gate =="
$reviewChecklist = Get-Content -LiteralPath ".harness/review_checklist.md" -Raw -Encoding UTF8
$requiredReviewMarkers = @(
    "formal_review_evidence_gate",
    "continuous_authorization_does_not_replace_formal_review",
    "formal_review_after_final_runtime_tests"
)
foreach ($marker in $requiredReviewMarkers) {
    if ($reviewChecklist -notmatch [regex]::Escape($marker)) {
        Write-Host "Missing formal review evidence marker: $marker" -ForegroundColor Red
        exit 1
    }
}
$blockingReviewItems = Select-String -LiteralPath ".harness/review_checklist.md" -Pattern '^- \[ \].*(formal_review|P0_|P1_|P2_|final_review|review_remediation)'
if ($blockingReviewItems) {
    Write-Host "Unresolved formal review blockers remain:" -ForegroundColor Red
    $blockingReviewItems | ForEach-Object { Write-Host "- $($_.Line.Trim())" -ForegroundColor Red }
    exit 1
}
Write-Host "Formal review evidence gate passed."

Write-Host ""
Write-Host "== git diff --check =="
git diff --check
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Stage closeout check passed."
