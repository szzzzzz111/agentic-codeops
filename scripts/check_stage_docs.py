"""Portable stage-document responsibility scan."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

REQUIRED_FILES = (
    "AGENTS.md", "README.md", "docs/ARCHITECTURE.md", "docs/AGENT_RULES.md",
    "docs/PROGRESS.md", "docs/FEATURE_LIST.json", "HANDOFF_TO_NEXT_CHAT.md",
    ".harness/allowed_files.md", ".harness/review_checklist.md", ".harness/rules.md",
    "openspec/specs/harness-development-workflow/spec.md",
    ".codex/skills/repo-stage-workflow/SKILL.md",
)
STALE_PATTERNS = (
    "V25/backlog", "deferred to V25/backlog", "Verified Patch Promotion is deferred",
    "archive pending", "merge pending", "final review pending",
)


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
    for marker in ("git status --short --branch", "git log -5 --oneline --decorate", "openspec list", "Active OpenSpec change"):
        if marker not in handoff:
            findings.append(f"HANDOFF_TO_NEXT_CHAT.md is missing current-context marker: {marker}")
    if re.search(r"(?m)^## V\d+", handoff, re.IGNORECASE):
        findings.append("HANDOFF_TO_NEXT_CHAT.md contains version-history sections; history belongs in docs/PROGRESS.md")
    if re.search(r"(?i)current HEAD.{0,30}\b[0-9a-f]{7,40}\b", handoff):
        findings.append("HANDOFF_TO_NEXT_CHAT.md contains a self-invalidating current-HEAD claim")
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
    marker = "## 下一步建议"
    start = progress.find(marker)
    if start < 0:
        findings.append("docs/PROGRESS.md is missing next-step guidance section")
    else:
        section = progress[start:]
        next_heading = section.find("\n## ", 1)
        if next_heading > 0:
            section = section[:next_heading]
        for pattern in STALE_PATTERNS:
            if pattern in section:
                findings.append(f"docs/PROGRESS.md next-step guidance contains stale wording: {pattern}")
        if "V24 `polish-demo-cli-capability-surface`" in section or "V24 CLI surface" in section:
            findings.append("docs/PROGRESS.md next-step guidance still describes V24 as the current stage")
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
