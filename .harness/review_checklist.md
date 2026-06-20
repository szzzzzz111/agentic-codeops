# 当前 Review 清单

当前无 active product development stage。low-risk、process-only workflow maintenance 已完成、
验证并本地合并到 `main`；不包含 runtime、tests、公开 API 或 V24。

## Process-Only Workflow Maintenance

- [x] 新增 `repo-stage-workflow` 总编排 skill，并引用 planning/apply/review/archive/handoff skills。
- [x] planning、internal review、external review、Stage Debt Sweep、handoff 职责无整套重复。
- [x] 风险分级决定 review 深度，高风险 Git/subprocess/persistence/API 变更保留完整链路。
- [x] External review 契约要求独立反例、触发条件、后果、位置和建议测试。
- [x] Stage Debt Sweep 记录 changed paths、直接依赖 older paths、finding 和 disposition。
- [x] Archive 后 runtime/test 变更会重新打开 verification/review gate。
- [x] PROGRESS、HANDOFF、review checklist 与 Git/OpenSpec 实时状态职责已分离。
- [x] Merge/push 后只做一次 final handoff，不复制动态 HEAD/remote hash。
- [x] HANDOFF 已移除历史版本堆叠；PROGRESS 保留长期演进事实。
- [x] Skill eval 覆盖 V19 hash 循环、V22 late debt、重复 external review 和连续执行授权。
- [x] `app/**`、`tests/**`、FEATURE_LIST、runtime capability specs 和 `/chat` contract 未修改。

## 正式 Review 证据门

- Gate marker: `formal_review_evidence_gate`
- Policy marker: `continuous_authorization_does_not_replace_formal_review`
- Timing marker: `formal_review_after_final_runtime_tests`
- [x] 本轮 final review 已检查 scope、职责重叠、文档所有权、checker 约束和 diff。
- [x] 本轮无 runtime/tests 变更，因此无需 runtime re-review 或完整外部 review。
- [x] `manual_stage_debt_sweep_completed`：已复核 `.codex/skills/**`、Harness rules/templates/checkers、
  workflow spec、PROGRESS 与 HANDOFF；无 runtime/test adjacent path。
- [x] `formal_review_findings_closed`：已修复 plan review 缺口和 Windows PowerShell UTF-8 checker
  解析问题，无剩余 P0/P1/P2。

## 验证

- [x] 四个相关 skill 的 official quick validation 通过。
- [x] `scripts/check_skill_evals.ps1` 通过。
- [x] `openspec validate --all`：18 passed, 0 failed。
- [x] `scripts/check_stage_docs.ps1` 通过。
- [x] `scripts/verify.ps1`：289 passed, 1 skipped；ruff 与流程检查通过。
- [x] `git diff --check` 通过。

## 下一阶段

- [ ] `future_stage_create_openspec_change`：开始产品阶段前创建 OpenSpec change。
- [ ] `future_stage_sync_harness`：开始产品阶段前重新同步 allowed files 和 review checklist。
