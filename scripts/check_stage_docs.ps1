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

function Join-Codepoints {
    param([int[]]$Codes)
    return -join ($Codes | ForEach-Object { [char]$_ })
}

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
    "Active OpenSpec change"
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

$currentFactFiles = @(
    "README.md",
    "docs/ARCHITECTURE.md",
    "docs/FEATURE_LIST.json",
    "HANDOFF_TO_NEXT_CHAT.md",
    ".harness/allowed_files.md",
    ".harness/review_checklist.md"
)
$staleCurrentFactPatterns = @(
    "V25/backlog",
    "deferred to V25/backlog",
    "Verified Patch Promotion is deferred",
    "archive pending",
    "merge pending",
    "final review pending"
)
foreach ($path in $currentFactFiles) {
    $content = Get-Content -Raw -Encoding UTF8 -LiteralPath $path
    foreach ($pattern in $staleCurrentFactPatterns) {
        if ($content.Contains($pattern)) {
            $findings += "$path contains stale current-stage wording: $pattern"
        }
    }
}

$readme = Get-Content -Raw -Encoding UTF8 -LiteralPath "README.md"
$readmeDuplicatedHeadings = @(
    "## $(Join-Codepoints @(0x5F53, 0x524D, 0x80FD, 0x529B))",
    "## $(Join-Codepoints @(0x5F53, 0x524D, 0x67B6, 0x6784))",
    "## $(Join-Codepoints @(0x9636, 0x6BB5, 0x5386, 0x53F2))",
    "## $(Join-Codepoints @(0x8DEF, 0x7EBF, 0x56FE))"
)
foreach ($heading in $readmeDuplicatedHeadings) {
    if ($readme.Contains($heading)) {
        $findings += "README.md contains duplicated deep-documentation heading: $heading"
    }
}

$progress = Get-Content -Raw -Encoding UTF8 -LiteralPath "docs/PROGRESS.md"
$nextStepsHeading = "## $(Join-Codepoints @(0x4E0B, 0x4E00, 0x6B65, 0x5EFA, 0x8BAE))"
$nextStepsStart = $progress.IndexOf($nextStepsHeading)
if ($nextStepsStart -ge 0) {
    $nextSteps = $progress.Substring($nextStepsStart)
    $nextHeading = $nextSteps.IndexOf("`n## ", 1)
    if ($nextHeading -gt 0) {
        $nextSteps = $nextSteps.Substring(0, $nextHeading)
    }
    foreach ($pattern in $staleCurrentFactPatterns) {
        if ($nextSteps.Contains($pattern)) {
            $findings += "docs/PROGRESS.md next-step guidance contains stale wording: $pattern"
        }
    }
    if ($nextSteps.Contains('V24 `polish-demo-cli-capability-surface`') -or $nextSteps.Contains("V24 CLI surface")) {
        $findings += "docs/PROGRESS.md next-step guidance still describes V24 as the current stage"
    }
} else {
    $findings += "docs/PROGRESS.md is missing next-step guidance section"
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
