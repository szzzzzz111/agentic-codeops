## 1. Harness And OpenSpec

- [x] 1.1 Create V16 OpenSpec proposal, design, spec deltas, and tasks.
- [x] 1.2 Update `.harness/allowed_files.md` for the V16 writable boundary.
- [x] 1.3 Update `.harness/review_checklist.md` for patch routing, provider schema, pending store, confirmation, permission context, safe apply, redaction, contract, and non-goal gates.
- [x] 1.4 Run `openspec validate v16-safe-patch-authoring`.

## 2. Tests

- [x] 2.1 Add failing patch authoring unit tests for confirmation parsing, provider schema validation, pending store isolation/TTL, unified diff safety, and multi-file preflight.
- [x] 2.2 Add failing PermissionPolicy / ApprovalGate tests for `ToolInvocationContext`, `patch_apply` write risk, `ask -> pass` confirmation, and normal `ask` blocking.
- [x] 2.3 Add failing AgentLoop tests proving V16 priority: Memory, Long Task, Assistant Control Surface, Patch, capability-status, repo_search/chat_only.
- [x] 2.4 Add failing `/chat` contract tests proving patch proposal and confirm apply keep top-level fields, proposal does not write files, answer does not expose full diff, and confirm apply does not run tests/commit/worktree.

## 3. Implementation

- [x] 3.1 Add patching package with confirmation parser, provider result schema, unified diff parser/applicator, pending patch store, and patch manager.
- [x] 3.2 Add Patch Authoring provider boundary with deterministic fake fallback and optional OpenAI-compatible structured diff path.
- [x] 3.3 Add `ToolInvocationContext`, register `patch_apply`, and update PermissionPolicy / ApprovalGate without adding new permission statuses.
- [x] 3.4 Add `ToolExecutor.patch_apply(...)` as the only runtime write path and enforce repo-local path, sensitive file, binary file, preflight and rollback boundaries.
- [x] 3.5 Integrate Patch command / Patch intent into AgentLoop with the fixed priority after Assistant Control Surface and before capability-status/repo_search.
- [x] 3.6 Add V16 capability-status wording while keeping V17+ as non-goals.

## 4. Docs And Verification

- [x] 4.1 Update README, ARCHITECTURE, PROGRESS, FEATURE_LIST, and HANDOFF for V16 behavior and non-goals.
- [x] 4.2 Run `openspec validate v16-safe-patch-authoring`.
- [x] 4.3 Run `openspec validate --all`.
- [x] 4.4 Run `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`.
- [x] 4.5 Run `git diff --check`.
- [x] 4.6 Complete implementation self-review before external review or archive.
