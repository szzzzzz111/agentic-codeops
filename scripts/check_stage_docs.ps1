$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$requiredFiles = @(
    "AGENTS.md",
    "README.md",
    "docs/ARCHITECTURE.md",
    "docs/AGENT_RULES.md",
    "docs/PROGRESS.md",
    "docs/FEATURE_LIST.json",
    "HANDOFF_TO_NEXT_CHAT.md",
    ".harness/allowed_files.md",
    ".harness/review_checklist.md",
    ".harness/rules.md",
    "openspec/specs/harness-development-workflow/spec.md",
    ".codex/skills/repo-stage-workflow/SKILL.md"
)

$findings = @()

foreach ($path in $requiredFiles) {
    if (-not (Test-Path -LiteralPath $path)) {
        $findings += "$path is missing"
    }
}

$specFiles = Get-ChildItem -LiteralPath "openspec/specs" -Recurse -File -Filter "spec.md"
foreach ($spec in $specFiles) {
    $matches = Select-String -LiteralPath $spec.FullName -Pattern "TBD|TODO|created by archiving change"
    foreach ($match in $matches) {
        $relative = $spec.FullName.Substring($repoRoot.Length + 1)
        $findings += "$relative`:$($match.LineNumber) contains a generated Purpose placeholder"
    }
}

$handoff = Get-Content -Raw -Encoding UTF8 -LiteralPath "HANDOFF_TO_NEXT_CHAT.md"
$requiredHandoffMarkers = @(
    "git status --short --branch",
    "git log -5 --oneline --decorate",
    "openspec list",
    "process-only workflow maintenance",
    "PROGRESS"
)
foreach ($required in $requiredHandoffMarkers) {
    if (-not $handoff.Contains($required)) {
        $findings += "HANDOFF_TO_NEXT_CHAT.md is missing current-context marker: $required"
    }
}
if ($handoff -match "(?m)^## V\d+") {
    $findings += "HANDOFF_TO_NEXT_CHAT.md contains version-history sections; history belongs in docs/PROGRESS.md"
}
if ($handoff -match "(?i)current HEAD.{0,30}\b[0-9a-f]{7,40}\b") {
    $findings += "HANDOFF_TO_NEXT_CHAT.md contains a self-invalidating current-HEAD claim"
}

$workflowSpec = Get-Content -Raw -Encoding UTF8 -LiteralPath "openspec/specs/harness-development-workflow/spec.md"
$requiredWorkflowRequirements = @(
    "Progress And Handoff Have Separate Ownership",
    "Stage Debt Sweep Is Focused And Checkable",
    "Stage Workflow Is Risk-Scaled",
    "External Review Seeks Independent Counterexamples",
    "Archive Freezes Reviewed Runtime"
)
foreach ($required in $requiredWorkflowRequirements) {
    if (-not $workflowSpec.Contains($required)) {
        $findings += "harness workflow spec is missing requirement: $required"
    }
}

Write-Host "== RepoPilot stage docs responsibility scan =="
Write-Host "Required files: $($requiredFiles.Count)"
Write-Host "Long-term specs: $($specFiles.Count)"

if ($findings.Count -gt 0) {
    Write-Host ""
    Write-Host "Stage documentation findings:" -ForegroundColor Red
    foreach ($finding in $findings) {
        Write-Host "- $finding" -ForegroundColor Red
    }
    exit 1
}

Write-Host "Stage documentation responsibilities are valid."
