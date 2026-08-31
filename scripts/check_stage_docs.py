"""Portable stage-document responsibility scan."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REQUIRED_FILES = (
    "AGENTS.md", "README.md", "docs/ARCHITECTURE.md", "docs/AGENT_RULES.md",
    "docs/PROGRESS.md", "docs/FEATURE_LIST.json", "HANDOFF_TO_NEXT_CHAT.md",
    ".harness/allowed_files.md", ".harness/review_checklist.md", ".harness/rules.md",
    "openspec/specs/README.md",
    "openspec/specs/harness-development-workflow/spec.md",
    ".codex/skills/repo-stage-workflow/SKILL.md",
)
STALE_PATTERNS = (
    "V25/backlog", "deferred to V25/backlog", "Verified Patch Promotion is deferred",
    "archive pending", "merge pending", "final review pending",
)
HANDOFF_LIVE_MARKERS = (
    "git status --short --branch",
    "git log -5 --oneline --decorate",
    "openspec list",
)
HANDOFF_VOLATILE_PATTERNS = (
    (
        r"(?im)^\s*(?:(?:active|current)\s+)?(?:branch|head|worktree|candidate|"
        r"remote(?:\s+parity)?|merge|push|openspec\s+change)\s*"
        r"(?:[:：=]|\bis\b)(?!\s*(?:(?:a\s+)?volatile\s+(?:fact|state)\b|"
        r"quer(?:y|ied)\s+(?:live|at\s+runtime)\b|resolved\s+live\b))"
    ),
    r"(?i)planning base",
    (
        r"(?im)^\s*(?:当前\s*)?(?:工作\s*分支|分支|HEAD|工作树|worktree|候选|"
        r"candidate|远端一致性|remote\s+parity|远端|remote|合并|merge|推送|push|"
        r"OpenSpec(?:\s+change|\s*变更))\s*(?:[:：=]|为|是)"
        r"(?!\s*(?:易变事实|通过(?:\s*(?:git|openspec)\b|命令|现场)))"
    ),
    r"当前只(?:在|剩)",
    r"尚未完成",
    r"/private/tmp/",
    r"\b[0-9a-f]{40}\b",
)
ARCHITECTURE_HEADINGS = (
    "## 系统上下文",
    "## 当前请求路由",
    "## 模块与代码映射",
    "## 状态与信任边界",
    "## 历史与规格入口",
)
PROGRESS_HEADINGS = (
    "## 当前状态",
    "## 剩余债务",
    "## 候选顺序",
    "## 阶段索引",
)
FEATURE_STAGE_NARRATION = re.compile(
    r"(?i)\b(?:active|pending|future|current[- ]stage)\b|当前阶段|进行中|待完成|尚未完成"
)
SPEC_INDEX_ENTRY = re.compile(
    r"(?m)^- \[([a-z0-9][a-z0-9-]*)\]\(([a-z0-9][a-z0-9-]*)/\)\s*$"
)


def _check_heading_order(
    content: str,
    headings: tuple[str, ...],
    relative: str,
    findings: list[str],
) -> None:
    offsets = [content.find(heading) for heading in headings]
    if all(offset >= 0 for offset in offsets) and offsets != sorted(offsets):
        findings.append(f"{relative} required headings are out of order")


def _handoff_volatile_view(content: str) -> str:
    lines: list[str] = []
    for line in content.splitlines():
        normalized = re.sub(
            r"^\s*(?:>\s*)?(?:(?:[-+*]|\d+[.)])\s+)?",
            "",
            line,
        )
        normalized = normalized.translate(
            str.maketrans("", "", "*_~" + chr(96))
        )
        lines.append(normalized)
    return "\n".join(lines)


def scan(project_root: Path) -> list[str]:
    root = project_root.resolve()
    findings: list[str] = []
    for relative in REQUIRED_FILES:
        if not (root / relative).is_file():
            findings.append(f"{relative} is missing")
    for spec in sorted((root / "openspec/specs").rglob("spec.md")):
        for number, line in enumerate(spec.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(
                r"TBD|TODO|created by archiving change", line, re.IGNORECASE
            ):
                findings.append(f"{spec.relative_to(root)}:{number} contains a generated Purpose placeholder")
    handoff_path = root / "HANDOFF_TO_NEXT_CHAT.md"
    handoff = handoff_path.read_text(encoding="utf-8") if handoff_path.is_file() else ""
    volatile_view = _handoff_volatile_view(handoff)
    for marker in HANDOFF_LIVE_MARKERS:
        if marker not in handoff:
            findings.append(f"HANDOFF_TO_NEXT_CHAT.md is missing current-context marker: {marker}")
    if re.search(r"(?m)^## V\d+", handoff, re.IGNORECASE):
        findings.append("HANDOFF_TO_NEXT_CHAT.md contains version-history sections; history belongs in docs/PROGRESS.md")
    for pattern in HANDOFF_VOLATILE_PATTERNS:
        if re.search(pattern, volatile_view):
            findings.append(
                "HANDOFF_TO_NEXT_CHAT.md contains volatile tracked state: "
                f"{pattern}"
            )

    architecture_path = root / "docs/ARCHITECTURE.md"
    architecture = (
        architecture_path.read_text(encoding="utf-8")
        if architecture_path.is_file()
        else ""
    )
    for heading in ARCHITECTURE_HEADINGS:
        if heading not in architecture:
            findings.append(f"docs/ARCHITECTURE.md is missing current-first heading: {heading}")
    _check_heading_order(
        architecture,
        ARCHITECTURE_HEADINGS,
        "docs/ARCHITECTURE.md",
        findings,
    )
    if re.search(r"(?m)^## V\d+", architecture):
        findings.append(
            "docs/ARCHITECTURE.md contains version-history headings; history belongs in archived OpenSpec"
        )

    feature_path = root / "docs/FEATURE_LIST.json"
    if feature_path.is_file():
        try:
            feature_items = json.loads(feature_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeError) as exc:
            findings.append(f"docs/FEATURE_LIST.json is invalid JSON: {exc}")
        else:
            if not isinstance(feature_items, list):
                findings.append("docs/FEATURE_LIST.json must contain a top-level array")
            else:
                for index, item in enumerate(feature_items):
                    if not isinstance(item, dict):
                        findings.append(
                            f"docs/FEATURE_LIST.json item {index} must be an object"
                        )
                        continue
                    note = item.get("notes")
                    if isinstance(note, str) and FEATURE_STAGE_NARRATION.search(note):
                        item_id = item.get("id", index)
                        findings.append(
                            "docs/FEATURE_LIST.json contains stage narration in notes: "
                            f"{item_id}"
                        )

    specs_root = root / "openspec/specs"
    specs_index_path = specs_root / "README.md"
    if specs_index_path.is_file():
        specs_index = specs_index_path.read_text(encoding="utf-8")
        indexed: set[str] = set()
        for label, target in SPEC_INDEX_ENTRY.findall(specs_index):
            if label != target:
                findings.append(
                    "openspec/specs/README.md entry label and target differ: "
                    f"{label} -> {target}"
                )
            indexed.add(target)
        actual = {
            path.parent.name
            for path in specs_root.glob("*/spec.md")
            if path.is_file()
        }
        for missing in sorted(actual - indexed):
            findings.append(
                f"openspec/specs/README.md is missing capability: {missing}"
            )
        for stale in sorted(indexed - actual):
            findings.append(
                f"openspec/specs/README.md contains unknown capability: {stale}"
            )
    workflow_path = root / "openspec/specs/harness-development-workflow/spec.md"
    workflow = workflow_path.read_text(encoding="utf-8") if workflow_path.is_file() else ""
    for requirement in ("Progress And Handoff Have Separate Ownership", "Stage Debt Sweep Is Focused And Checkable", "Stage Workflow Is Risk-Scaled", "External Review Seeks Independent Counterexamples", "Archive Freezes Reviewed Runtime"):
        if requirement not in workflow:
            findings.append(f"harness workflow spec is missing requirement: {requirement}")
    for relative in ("README.md", "docs/ARCHITECTURE.md", "docs/FEATURE_LIST.json", "HANDOFF_TO_NEXT_CHAT.md", ".harness/allowed_files.md", ".harness/review_checklist.md"):
        path = root / relative
        content = path.read_text(encoding="utf-8") if path.is_file() else ""
        for pattern in STALE_PATTERNS:
            if pattern in content:
                findings.append(f"{relative} contains stale current-stage wording: {pattern}")
    readme_path = root / "README.md"
    readme = readme_path.read_text(encoding="utf-8") if readme_path.is_file() else ""
    for heading in ("## 当前能力", "## 当前架构", "## 阶段历史", "## 路线图"):
        if heading in readme:
            findings.append(f"README.md contains duplicated deep-documentation heading: {heading}")
    progress_path = root / "docs/PROGRESS.md"
    progress = progress_path.read_text(encoding="utf-8") if progress_path.is_file() else ""
    for heading in PROGRESS_HEADINGS:
        if heading not in progress:
            findings.append(f"docs/PROGRESS.md is missing durable section: {heading}")
    _check_heading_order(progress, PROGRESS_HEADINGS, "docs/PROGRESS.md", findings)
    progress_current = progress.split("<details>", 1)[0]
    for pattern in STALE_PATTERNS:
        if pattern in progress_current:
            findings.append(f"docs/PROGRESS.md contains stale current wording: {pattern}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="RepoPilot stage docs responsibility scan")
    parser.add_argument("--project-root", type=Path)
    args = parser.parse_args()
    root = args.project_root or Path(__file__).resolve().parent.parent
    findings = scan(root)
    print("== RepoPilot stage docs responsibility scan ==")
    if findings:
        for finding in findings:
            print(f"- {finding}")
        return 1
    print("Stage documentation responsibilities are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
