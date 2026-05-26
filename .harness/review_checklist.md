# 当前 Review 清单

当前活跃阶段：无。V10 `v10-evidence-pack-context-budget` 已实现、提交并归档。

## Archive Review

- [ ] V10 active change 已移动到 `openspec/changes/archive/2026-05-26-v10-evidence-pack-context-budget/`。
- [ ] `openspec/specs/repo-query-understanding-rag/spec.md` 已同步 V10 Evidence Pack + Context Budget requirements。
- [ ] 长期 specs 与当前 V9/V10 主链路一致；`min_fused_score` 使用当前代码默认值 `0.35`。
- [ ] `docs/PROGRESS.md` 和 `HANDOFF_TO_NEXT_CHAT.md` 反映 V10 已归档，且不再把 active change 写成仍在 `openspec/changes/v10-evidence-pack-context-budget/`。
- [ ] `.harness/allowed_files.md` 与归档收尾范围一致。

## Completed V10 Contract

- [ ] Evidence Pack item shape 明确包含稳定 `evidence_id`、相对 `file_path`、1-based 行号、score、snippet 和 source summary。
- [ ] Evidence Pack item shape 明确包含 `included` 和 `truncated`。
- [ ] Context Budget 使用 deterministic character budget，并记录 included / omitted / truncated / budget used 字段。
- [ ] Audit summary 固定包含 `evidence_items`、`included_count`、`omitted_count`、`truncated_count`、`budget_used_chars` 和 `max_context_chars`。
- [ ] `ToolExecutionResult.evidence_pack` 不进入 `call_summary()`、`tool_calls` 或 `/chat` 顶层响应。
- [ ] Evidence Pack 不包含本机绝对路径或完整文件内容。
- [ ] Evidence Pack builder 不直接读仓库、不调用 shell、不绕过安全文件工具和 retrieval 边界。
- [ ] Context Budget 不执行 LLM rerank、query rewrite、semantic merge 或 context compression。
- [ ] 内部 trace / audit summary 记录 Evidence Pack 摘要，但 `/chat` 顶层响应仍只要求 `trace_id`、`answer`、`related_files`、`tool_calls`。
- [ ] 权限、审批和 `ToolExecutor(repo_rag)` 边界保持不变。
- [ ] `docs/FEATURE_LIST.json` 中 V10 条目只有在确定性验证通过后才可标记 `passes: true`。

## Verification

- [ ] `openspec validate --all` 通过。
- [ ] `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` 通过，或说明无法运行的原因。
- [ ] `git diff --check` 通过。
- [ ] `git status --short --branch` 和 `git diff --name-only` 未显示归档收尾外文件。
- [ ] 内部 self-review、外部 review、提交和 archive 均已完成后，才能把 V10 视为阶段完成。
