"""Portable skill-eval structure scan."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

SKILLS = (".codex/skills/repo-stage-workflow", ".codex/skills/repo-stage-handoff", ".codex/skills/repo-stage-review-loop", ".codex/skills/openspec-archive-change")
REQUIRED_SECTIONS = ("## Positive", "## Negative", "## Edge", "## Failure Traps")


def scan(project_root: Path) -> list[str]:
    root = project_root.resolve()
    findings: list[str] = []
    for relative in SKILLS:
        skill_path = root / relative / "SKILL.md"
        eval_path = root / relative / "references/evals.md"
        if not skill_path.is_file():
            findings.append(f"{skill_path.relative_to(root)} is missing")
            continue
        if not eval_path.is_file():
            findings.append(f"{eval_path.relative_to(root)} is missing")
            continue
        skill_text = skill_path.read_text(encoding="utf-8")
        eval_text = eval_path.read_text(encoding="utf-8")
        match = re.search(r"(?m)^description:\s*(.+)$", skill_text)
        if match is None:
            findings.append(f"{skill_path.relative_to(root)} has no single-line description")
        else:
            description = match.group(1).strip()
            if not re.match(r"^(Use|Load) when\b", description, re.IGNORECASE):
                findings.append(f"{skill_path.relative_to(root)} description must start with 'Use when' or 'Load when'")
            if len(description.split()) > 50:
                findings.append(f"{skill_path.relative_to(root)} description exceeds 50 words ({len(description.split())})")
        if "references/evals.md" not in skill_text.casefold():
            findings.append(f"{skill_path.relative_to(root)} does not reference references/evals.md")
        for section in REQUIRED_SECTIONS:
            if (
                re.search(
                    rf"(?m)^{re.escape(section)}\r?$", eval_text, re.IGNORECASE
                )
                is None
            ):
                findings.append(f"{eval_path.relative_to(root)} is missing {section}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="RepoPilot skill eval structure scan")
    parser.add_argument("--project-root", type=Path)
    args = parser.parse_args()
    root = args.project_root or Path(__file__).resolve().parent.parent
    findings = scan(root)
    print("== RepoPilot skill eval structure scan ==")
    if findings:
        for finding in findings:
            print(f"- {finding}")
        return 1
    print("Skill eval structure is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
