# 当前 Review 清单

当前活跃阶段：V10 `v10-evidence-pack-context-budget`（implementation）。

## Plan / OpenSpec Review

- [ ] OpenSpec proposal、design、tasks 和 spec delta 均已创建在 `openspec/changes/v10-evidence-pack-context-budget/`。
- [ ] `openspec validate v10-evidence-pack-context-budget` 通过。
- [ ] Proposal 的 capability 列表与 spec delta 路径一致。
- [ ] Design 明确 V10 只做 Evidence Pack + Context Budget，不做 grounded answer、model provider、query rewrite、rerank、memory 或 context compression。
- [ ] Spec delta 使用 `SHALL` / `MUST`，每个 requirement 至少有一个 `#### Scenario`。
- [ ] Tasks 保留 plan/review 停止点记录；本轮实现已由用户明确 `PLEASE IMPLEMENT THIS PLAN` 放行。
- [ ] `.harness/allowed_files.md` 与本阶段范围一致。
- [ ] README、ARCHITECTURE、PROGRESS、FEATURE_LIST 和 HANDOFF 不再遗漏 V9 已完成能力或把 V9 写成未来阶段。
- [ ] 长期 specs 不得与当前 V9/V10 主链路冲突；`agent-loop-tool-execution` 允许 repo-local deterministic hybrid RAG，但仍禁止真实外部 embedding 服务、外部向量库和 LLM rerank。
- [ ] `docs/PROGRESS.md`、`docs/FEATURE_LIST.json` 和 `HANDOFF_TO_NEXT_CHAT.md` 反映 V10 当前为 implementation review；`passes` 只在确定性验证通过后标记为 `true`。

## Implementation Review

- [ ] 先写失败测试，再写实现。
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

- [ ] `openspec validate v10-evidence-pack-context-budget` 通过。
- [ ] `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` 通过，或说明无法运行的原因。
- [ ] `git diff --check` 通过。
- [ ] `git status --short --branch` 和 `git diff --name-only` 未显示阶段外文件。
- [ ] 内部 self-review 已完成；外部/user review 未完成前不得声明 archive-ready。
