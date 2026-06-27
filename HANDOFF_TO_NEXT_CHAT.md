# 交接给下一轮 Chat

## 当前基线（2026-06-27，V25 merged）

- 当前集成分支：`main`。
- Active OpenSpec change：无。
- 最近完成阶段：V25 `add-verified-patch-promotion`，已归档到 `openspec/changes/archive/2026-06-27-add-verified-patch-promotion/` 并 fast-forward 合入 `main`。
- 阶段目标已完成：Verified Patch Promotion 仅允许用户精确确认后，将当前 scope 内 verified retained worktree 的 stored controlled patch 通过 approval-gated `patch_apply` 提升到主工作区。
- V25 不实现 commit、merge、push、branch/PR、后台任务、runtime subagent、connector、notification、自动 retry/repair、删除 retained worktree 或 `git worktree prune`。

## 验证与 Review

- Focused promotion：`pytest -q tests/test_verified_patch_promotion.py` -> 28 passed。
- Adjacent focused suite：172 passed；promotion + adjacent total 200 passed。
- Archive 后 `openspec list` -> No active changes found。
- Archive 后 `openspec validate --all` -> 21 passed，0 failed。
- Merge 后 full `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` -> pytest 469 passed、1 skipped；ruff、stage docs scan、skill eval structure scan passed。
- `git diff --check` -> passed，仅 CRLF normalization warnings。
- Final review：internal、Codex independent、OpenCode independent review 均完成；所有 findings 已按 `fix / clarify / reject / defer` triage，无剩余 P0/P1/P2。
- 残余 P3：无全局 repo lock 下的极窄跨进程 HEAD/file mutation race，后续可独立 hardening。

## 下一步

开始新阶段前先查询 live state：

```powershell
git status --short --branch
git log -5 --oneline --decorate
git branch --contains HEAD
openspec list
openspec validate --all
```

若需要继续新阶段，先按 `AGENTS.md` 读取必读文档、创建新的 OpenSpec change，并同步 `.harness/allowed_files.md` 与 `.harness/review_checklist.md`。
