# 当前 Review 清单

Archived change：`2026-06-22-harden-model-provider-contract`。风险级别：high。

## Scope

- [x] 共享 Provider 使用向后兼容的 text / JSON object 请求契约。
- [x] Provider 不按 `question_type` 推断业务 schema。
- [x] Planner/Patch 删除重复 JSON instruction，并保留业务校验职责。
- [x] Planner 在解析前检查 provider status。
- [x] StructuredOutputInstruction 在 HTTP 前完成完整基础校验，失败时零 HTTP 调用。
- [x] Metrics 保持 response-local、脱敏且不进入公开或持久化 contract。
- [x] 默认 fake provider、Patch wiring、API、存储、权限和默认离线验证保持不变。
- [x] 不执行 live eval，不创建 V24。

## TDD And Verification

- [x] RED：兼容默认值、非法 request、JSON 分层、Planner status、thinking、metrics 和 finish reason。
- [x] GREEN：focused provider/Planner/Patch/Grounded Answer/persistent audit 75 passed。
- [x] AgentLoop/API/persistent audit 回归通过；review remediation 后相关 focused regression
  165 passed。
- [x] 实现完成时 OpenSpec strict/all validation：19 passed；归档后长期 specs validation：
  18 passed。
- [x] Full `scripts/verify.ps1`：331 passed、1 skipped；ruff、stage docs、skill checks 通过。
- [x] `git diff --check` 通过。

## Review

- Gate marker: `formal_review_evidence_gate`
- Policy marker: `continuous_authorization_does_not_replace_formal_review`
- Timing marker: `formal_review_after_final_runtime_tests`
- [x] Internal plan review 已检查 proposal/design/spec/tasks、测试计划与 Harness 边界；确认
  Change 1 不包含 live eval，JSON instruction 单一来源，Provider/业务校验分层，非法配置零 HTTP
  调用，metrics 不穿透业务/public/persistent contract。
- [x] Formal implementation review 晚于最终 runtime/test 变更；内部 review 额外收紧 instruction
  name 为 1–64 字符安全标识符。
- [x] 独立 adversarial external review 使用 `opencode/deepseek-v4-flash-free` 检查 request/response
  兼容、JSON 分层、fail-closed 配置、metrics 泄漏和默认 wiring；初审 0 P0/P1、3 P2，修复
  `json_example` 4096 字符上限与递归 fail-closed，补 malformed evidence 和 JSON missing-finish
  回归；re-review 确认无剩余 P0/P1/P2。
- [x] `manual_stage_debt_sweep_completed`：检查 changed provider/Planner/Patch/tests，以及直接依赖的
  Grounded Answer、AgentLoop、API、persistent audit、所有 `ModelProviderRequest/Response`
  调用点和 JSON instruction 残留；无新增具体债务。
- [x] `formal_review_findings_closed`：所有 P0/P1/P2 已关闭；P3 分别判为重复覆盖、错误判断或当前
  contract 外的非阻断残余不确定性。

## Closeout

- [x] Change 1 已完成 review、验证与归档，当前无 active OpenSpec change，已满足 integration gate。
- [ ] `future_stage_only`：`add-live-model-provider-eval` 仅在本 change 归档合并后独立创建。
