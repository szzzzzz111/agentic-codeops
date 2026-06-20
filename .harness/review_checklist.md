# 当前 Review 清单

Archived change：`2026-06-20-fix-v11-v12-capability-truth`。风险级别：medium。

## Scope

- [x] V11 status 承认 V12 deterministic rewrite/rerank 与 V13 Memory。
- [x] V12 status 承认 V13 Memory。
- [x] 回答继续区分真实 LLM rewrite/rerank、向量 memory、自动总结、跨 repo 召回和 context compression。
- [x] 不修改路由、执行链、持久化、API contract 或历史阶段文档。
- [x] 不引入动态 capability registry，不创建 V24。

## TDD And Verification

- [x] RED：4 failed，证明 V11/V12 回答仍包含已失效 non-goal。
- [x] GREEN：Kernel/API 定向测试 4 passed。
- [x] OpenSpec strict/all validation：19 passed。
- [x] Full `scripts/verify.ps1`：292 passed、1 skipped；ruff 与流程检查通过。
- [x] `git diff --check` 通过。

## Review

- Gate marker: `formal_review_evidence_gate`
- Policy marker: `continuous_authorization_does_not_replace_formal_review`
- Timing marker: `formal_review_after_final_runtime_tests`
- [x] Internal plan review 已检查 proposal/design/spec/tasks、测试计划与 Harness 边界。
- [x] Formal implementation review 已晚于最终 runtime/test 变更。
- [x] Focused external review：OpenCode `opencode/deepseek-v4-flash-free` 找到 standalone V12
  覆盖缺口与 V11 Memory 表述不明确；remediation 后 re-review 确认均关闭，无剩余 finding。
- [x] `manual_stage_debt_sweep_completed`：复核 V11/V12/V13 constants、capability router、
  Kernel/API tests、统一 spec、历史 README/ARCHITECTURE 与 allowed files；无新增债务。
- [x] `formal_review_findings_closed`：内部 P2 测试分支错误与外部 P2/P3 均已修复并复验。

## 下一阶段

- [x] OpenSpec change 已归档，当前无 active change。
- [ ] `future_stage_only`：下一项工作必须独立规划。
