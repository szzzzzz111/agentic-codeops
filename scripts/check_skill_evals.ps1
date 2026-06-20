$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$skills = @(
    ".codex/skills/repo-stage-workflow",
    ".codex/skills/repo-stage-handoff",
    ".codex/skills/repo-stage-review-loop",
    ".codex/skills/openspec-archive-change"
)

$requiredSections = @(
    "## Positive",
    "## Negative",
    "## Edge",
    "## Failure Traps"
)

$findings = @()

foreach ($skillDir in $skills) {
    $skillPath = Join-Path $skillDir "SKILL.md"
    $evalPath = Join-Path $skillDir "references/evals.md"

    if (-not (Test-Path -LiteralPath $skillPath)) {
        $findings += "$skillPath is missing"
        continue
    }
    if (-not (Test-Path -LiteralPath $evalPath)) {
        $findings += "$evalPath is missing"
        continue
    }

    $skillText = Get-Content -Raw -Encoding UTF8 -LiteralPath $skillPath
    $evalText = Get-Content -Raw -Encoding UTF8 -LiteralPath $evalPath
    $descriptionMatch = [regex]::Match(
        $skillText,
        "(?m)^description:\s*(?<description>.+)$"
    )

    if (-not $descriptionMatch.Success) {
        $findings += "$skillPath has no single-line description"
    } else {
        $description = $descriptionMatch.Groups["description"].Value.Trim()
        $wordCount = ($description -split "\s+" | Where-Object { $_ }).Count
        if ($description -notmatch "^(Use|Load) when\b") {
            $findings += "$skillPath description must start with 'Use when' or 'Load when'"
        }
        if ($wordCount -gt 50) {
            $findings += "$skillPath description exceeds 50 words ($wordCount)"
        }
    }

    if ($skillText -notmatch [regex]::Escape("references/evals.md")) {
        $findings += "$skillPath does not reference references/evals.md"
    }

    foreach ($section in $requiredSections) {
        if ($evalText -notmatch "(?m)^$([regex]::Escape($section))$") {
            $findings += "$evalPath is missing $section"
        }
    }
}

Write-Host "== RepoPilot skill eval structure scan =="
Write-Host "Scanned skills: $($skills.Count)"

if ($findings.Count -gt 0) {
    Write-Host ""
    Write-Host "Skill eval structure findings:" -ForegroundColor Red
    foreach ($finding in $findings) {
        Write-Host "- $finding" -ForegroundColor Red
    }
    exit 1
}

Write-Host "Skill eval structure is valid."
Write-Host "Note: this structural gate does not replace model-level routing evals."
