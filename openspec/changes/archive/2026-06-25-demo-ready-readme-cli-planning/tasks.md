## 1. Planning And Harness

- [x] 1.1 Read AGENTS.md, required docs, OpenSpec workflow, current harness files, current branch/worktree, recent commits, and active OpenSpec state.
- [x] 1.2 Decide stage shape: one non-V24 change for README facade plus CLI planning, with no runtime implementation.
- [x] 1.3 Create OpenSpec proposal, design, tasks, and spec deltas.
- [x] 1.4 Synchronize `.harness/allowed_files.md` and `.harness/review_checklist.md` before README edits or any implementation.
- [x] 1.5 Run internal plan review and OpenSpec validation.
- [x] 1.6 Stop for explicit user confirmation before editing README content.

## 2. README Facade After Confirmation

- [x] 2.1 Rewrite README first viewport around concise project positioning, current capabilities, architecture flow, quick start, and detailed docs links.
- [x] 2.2 Move or condense recent stage closeout notes so the top does not read like a development log.
- [x] 2.3 Verify README does not claim roadmap or planned CLI behavior as implemented.

## 3. CLI Planning Scope

- [x] 3.1 Keep CLI as planning-only in this change; do not create runtime entrypoint, package metadata, tests, or command implementation.
- [x] 3.2 Preserve explicit boundaries: no AgentLoop rewrite, no `/chat` contract change, no default CI change, no network dependency, no provider/runtime/prompt/profile changes, no default Patch wiring changes, and no V24.
- [x] 3.3 Document current vs planned claims so README and future demo script do not overstate existing behavior.

## 4. Validation

- [x] 4.1 Run `openspec validate demo-ready-readme-cli-planning --strict`.
- [x] 4.2 Run `openspec validate --all`.
- [x] 4.3 Run `git diff --check`.
- [x] 4.4 Summarize implementation decisions and verification evidence.
