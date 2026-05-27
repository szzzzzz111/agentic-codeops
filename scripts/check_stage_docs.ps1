$ErrorActionPreference = "Stop"

function U($escaped) {
    return [regex]::Unescape($escaped)
}

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$targets = @(
    "README.md",
    "docs/ARCHITECTURE.md",
    "docs/PROGRESS.md",
    "docs/FEATURE_LIST.json",
    "HANDOFF_TO_NEXT_CHAT.md",
    ".harness/allowed_files.md",
    ".harness/review_checklist.md"
)

$pendingFinalReview = U "\u5f85\u6700\u7ec8 review"
$pendingFinalVerify = U "\u5f85\u6700\u7ec8\u9a8c\u8bc1"
$pendingCommitArchive = U "\u5f85\u63d0\u4ea4\u548c\u5f52\u6863"
$pendingArchive = U "\u5f85\u5f52\u6863"
$activeChange = U "\u5f53\u524d\u6d3b\u8dc3 OpenSpec change\uff1av11-grounded-answer-model-provider-boundary"
$activeChangePath = U "V11 active change \u4f4d\u4e8e openspec/changes/v11-grounded-answer-model-provider-boundary/"
$oldRoadmap = U "\u5f53\u524d\u8def\u7ebf\u56fe\u5df2\u66f4\u65b0\u4e3a\u201c\u5df2\u5b8c\u6210\u81f3 V10\uff0c\u540e\u7eed\u4ece V11 \u5f00\u59cb\u201d"
$readmeV10Roadmap = U "\u5df2\u5b8c\u6210\u81f3 V10\uff1aEvidence Pack \+ Context Budget\u3002\u540e\u7eed\u8def\u7ebf"
$v13Implemented = U "V13 \u5df2\u5b9e\u73b0|\u5df2\u5b8c\u6210\u81f3 V13|V13 \u5df2\u5b8c\u6210"
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
        Pattern = "$activeChange|$activeChangePath"
        Reason = "V11 is archived but still described as an active change"
    },
    @{
        Pattern = $oldRoadmap
        Reason = "roadmap is still using the old V10-to-V11 wording"
    },
    @{
        Pattern = $readmeV10Roadmap
        Reason = "README roadmap should not stop at V10"
    },
    @{
        Pattern = $v13Implemented
        Reason = "V13 should be planned, not described as implemented"
    },
    @{
        Pattern = "$currentDefaultRealLlm|$currentDefaultMilvus|$currentDefaultEs|$currentDefaultPgVector|$currentDefaultQdrant"
        Reason = "default capability should not claim real LLM or heavyweight retrieval infrastructure"
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
