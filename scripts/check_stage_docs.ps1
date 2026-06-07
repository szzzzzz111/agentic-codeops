$ErrorActionPreference = "Stop"

function U($escaped) {
    return [regex]::Unescape($escaped)
}

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$durableTargets = @(
    "README.md",
    "docs/ARCHITECTURE.md",
    "docs/PROGRESS.md",
    "docs/FEATURE_LIST.json",
    "HANDOFF_TO_NEXT_CHAT.md",
    ".harness/allowed_files.md",
    ".harness/review_checklist.md",
    "openspec/README.md",
    "openspec/changes/README.md",
    "openspec/specs/README.md"
)

$specTargets = @()
if (Test-Path -LiteralPath "openspec/specs") {
    $specTargets = Get-ChildItem -LiteralPath "openspec/specs" -Recurse -File -Filter "spec.md" |
        ForEach-Object { $_.FullName }
}

$targets = @($durableTargets + $specTargets)

$pendingFinalReview = U "\u5f85\u6700\u7ec8 review"
$pendingFinalVerify = U "\u5f85\u6700\u7ec8\u9a8c\u8bc1"
$pendingCommitArchive = U "\u5f85\u63d0\u4ea4\u548c\u5f52\u6863"
$pendingArchive = U "\u5f85\u5f52\u6863"
$currentWorkBranch = U "\u5f53\u524d\u5de5\u4f5c\u5206\u652f\uff1a`?feature/v18-patch-verify-loop`?"
$archiveCloseout = U "archive \u540e\u9a8c\u8bc1 / closeout \u4e2d"
$v18MergePushDecision = U "\u5b8c\u6210 V18 archive \u540e\u9a8c\u8bc1\u548c closeout gate \u540e\uff0c\u518d\u8fdb\u5165 merge / push \u51b3\u7b56"
$continueV18Closeout = U "\u7ee7\u7eed V18 closeout"
$archivedThroughV18 = U "\u5df2\u5f52\u6863\u81f3 V18"
$v1ThroughV18ActiveArchived = "V1-V18 active changes"
$v19CurrentlyImplementing = U "V19 \u5f53\u524d\u5b9e\u73b0"
$completeV19AsFuture = U "\u5b8c\u6210 V19 Persistent Audit / Recovery"
$tracePersistenceStillRoadmap = U "trace \u6301\u4e45\u5316\u5ba1\u8ba1"
$generatedPurpose = "TBD|TODO|created by archiving change"
$currentDefaultRealLlm = U "\u5f53\u524d\u9ed8\u8ba4\u63a5\u5165\u771f\u5b9e LLM|\u5df2\u9ed8\u8ba4\u63a5\u5165\u771f\u5b9e LLM"
$currentDefaultMilvus = U "\u5f53\u524d\u9ed8\u8ba4\u63a5\u5165 Milvus|\u5df2\u9ed8\u8ba4\u63a5\u5165 Milvus"
$currentDefaultEs = U "\u5f53\u524d\u9ed8\u8ba4\u63a5\u5165 Elasticsearch|\u5df2\u9ed8\u8ba4\u63a5\u5165 Elasticsearch"
$currentDefaultPgVector = U "\u5f53\u524d\u9ed8\u8ba4\u63a5\u5165 PgVector|\u5df2\u9ed8\u8ba4\u63a5\u5165 PgVector"
$currentDefaultQdrant = U "\u5f53\u524d\u9ed8\u8ba4\u63a5\u5165 Qdrant|\u5df2\u9ed8\u8ba4\u63a5\u5165 Qdrant"

$rules = @(
    @{
        Pattern = "$pendingFinalReview|$pendingFinalVerify|$pendingCommitArchive|$pendingArchive"
        Reason = "completed stage is still described as pending review, verification, commit, or archive"
    },
    @{
        Pattern = "$currentWorkBranch|$archiveCloseout|$v18MergePushDecision|$continueV18Closeout"
        Reason = "V18 has been merged and pushed, but docs still describe the pre-merge closeout state"
    },
    @{
        Pattern = "$archivedThroughV18|$v1ThroughV18ActiveArchived|$v19CurrentlyImplementing|$completeV19AsFuture|$tracePersistenceStillRoadmap"
        Reason = "V19 has completed, but durable docs still describe V18/V19 or persistent audit as incomplete"
    },
    @{
        Pattern = $generatedPurpose
        Reason = "long-term specs contain generated placeholder debt"
        SpecOnly = $true
    },
    @{
        Pattern = "$currentDefaultRealLlm|$currentDefaultMilvus|$currentDefaultEs|$currentDefaultPgVector|$currentDefaultQdrant"
        Reason = "default capability should not claim real LLM or heavyweight retrieval infrastructure"
    }
)

$requiredMatches = @(
    @{
        Target = "README.md"
        Pattern = "^### Persistent Audit / Recovery$"
        Reason = "README current capabilities must include Persistent Audit / Recovery"
    },
    @{
        Target = "README.md"
        Pattern = "^### Verification Runner$"
        Reason = "README current capabilities must include Verification Runner"
    },
    @{
        Target = "README.md"
        Pattern = "^### V19\uff1aPersistent Audit / Recovery$"
        Reason = "README stage history must include V19"
    },
    @{
        Target = "README.md"
        Pattern = U "\u5df2\u5f52\u6863\u81f3 V19"
        Reason = "README roadmap must state that V19 is archived"
    },
    @{
        Target = "README.md"
        Pattern = "^## V20 Worktree Isolation$"
        Reason = "README current capabilities must include V20 Worktree Isolation"
    },
    @{
        Target = "docs/ARCHITECTURE.md"
        Pattern = "^## V20 Worktree Isolation \u67b6\u6784\u8865\u5145$"
        Reason = "architecture must include V20 Worktree Isolation"
    },
    @{
        Target = "docs/PROGRESS.md"
        Pattern = "v20-worktree-isolation"
        Reason = "progress must identify the active V20 change"
    },
    @{
        Target = "HANDOFF_TO_NEXT_CHAT.md"
        Pattern = "current active OpenSpec change|v20-worktree-isolation"
        Reason = "handoff must identify the active V20 change"
    }
)

$findings = @()

foreach ($target in $targets) {
    if (-not (Test-Path -LiteralPath $target)) {
        $findings += [pscustomobject]@{
            File = $target
            Line = 0
            Rule = "missing_target"
            Text = "Expected stage document is missing."
        }
        continue
    }

    foreach ($rule in $rules) {
        if ($rule.SpecOnly -and ($target -notmatch "openspec[\\/]specs")) {
            continue
        }
        $matches = Select-String -LiteralPath $target -Pattern $rule.Pattern
        foreach ($match in $matches) {
            $findings += [pscustomobject]@{
                File = $target
                Line = $match.LineNumber
                Rule = $rule.Reason
                Text = $match.Line.Trim()
            }
        }
    }
}

foreach ($required in $requiredMatches) {
    $matches = Select-String -LiteralPath $required.Target -Pattern $required.Pattern
    if (-not $matches) {
        $findings += [pscustomobject]@{
            File = $required.Target
            Line = 0
            Rule = $required.Reason
            Text = "Required stage parity marker is missing."
        }
    }
}

Write-Host "== RepoPilot stage docs drift scan =="
Write-Host "Scanned files: $($targets.Count)"

if ($findings.Count -gt 0) {
    Write-Host ""
    Write-Host "Potential stage documentation drift found:" -ForegroundColor Red
    foreach ($finding in $findings) {
        Write-Host "- $($finding.File):$($finding.Line) $($finding.Rule)" -ForegroundColor Red
        Write-Host "  $($finding.Text)"
    }
    exit 1
}

Write-Host "No stage documentation drift found."
