# 当前 Review 清单

Archived change：`2026-06-20-fix-capability-provider-truth`。风险级别：medium。

## Scope

- [x] Patch capability-status 不再声称 Persistent Audit / Worktree Isolation 未实现。
- [x] 回答准确概括 V16-V23 已实现边界，并继续明确 promotion/commit/push 未实现。
- [x] 默认 fake Patch Authoring provider 仍不生成真实 diff。
- [x] 文档/spec 明确 `ModelPatchAuthoringProvider` 仅是可注入边界，默认应用装配未通过环境配置启用。
- [x] 不新增 provider wiring、API、schema、权限、存储或执行行为。
- [x] 不修改 V24 或其他产品路线。
- [x] Stage docs checker 不再强制保留上一轮 process-only handoff 文案。

## TDD And Verification

- [x] RED：旧 capability-status 回答无法满足 V19-V23 真实状态。
- [x] GREEN：Kernel/API/provider 装配定向测试 3 passed。
- [x] OpenSpec strict validation 通过。
- [x] OpenSpec all validation：19 passed。
- [x] Full `scripts/verify.ps1`：291 passed、1 skipped；ruff 与流程检查通过。
- [x] `git diff --check` 通过。

## Review

- Gate marker: `formal_review_evidence_gate`
- Policy marker: `continuous_authorization_does_not_replace_formal_review`
- Timing marker: `formal_review_after_final_runtime_tests`
- [x] Internal plan review 已检查 proposal/design/spec/tasks 一致性。
- [x] Formal implementation review 已晚于最终 runtime/test 变更。
- [x] Focused external review：OpenCode `opencode/deepseek-v4-flash-free` 独立只读审查，
  结论 `No in-scope findings`；已核对 capability truth、provider 装配、V19 audit 例外、
  tests 与 allowed files。
- [x] `manual_stage_debt_sweep_completed`：复核 capability constants/router/audit/tests、provider
  默认装配与 docs/spec；V11/V12 同类漂移已记录为独立后续债务。
- [x] `formal_review_findings_closed`：已修正 V19 audit 规格冲突、补 provider 装配测试并纠正
  shared provider 文档；无本 change 内剩余 P0/P1/P2。
- [x] External residual triage：关于 archive 后 `Active OpenSpec change` marker 失效的顾虑判为
  `reject`；checker 只要求稳定字段名，归档后可明确写为 `none`。

## 下一阶段

- [x] OpenSpec change 已归档，当前无 active change。
- [ ] `future_stage_only`：下一项 Portfolio Readiness hardening 必须独立规划。
