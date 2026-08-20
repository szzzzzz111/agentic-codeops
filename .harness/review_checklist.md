# 当前 Review 清单

Active OpenSpec change：`generalize-independent-review-provider`。

Risk：`low` / process-only。理由：只调整开发流程文档、长期 workflow spec、本地 skills 和
结构断言；不修改 runtime、公开 API、权限、持久化、Git/subprocess 执行或默认 CI。

## Planning Gate

- [x] proposal/design/tasks/spec delta 完整定义两个独立评审席位，且不降低既有 review 数量。
- [x] 首轮 Codex 替代评审要求空上下文任务或不继承父对话的子智能体。
- [x] 明确继承实现上下文、看到其他首轮 reviewer 结论或直接修改被审对象的实例不算独立评审。
- [x] 明确 remediation re-review 可以复用原 reviewer 会话以关闭既有 finding。
- [x] 明确 remediation 后每个 required slot 的最终 receipt 都绑定同一个最终 baseline；旧 baseline 结论不能继续计数。
- [x] 明确 OpenCode 是可选适配器，且 provider/model 多样性是风险信息，不是唯一独立性证明。
- [x] internal plan review 完成；未发现 planning artifact 间的 scope/contract/task 冲突。
- [x] 用户要求的空上下文 Codex independent plan review 完成；8 个 findings 均按 `fix` 处理并经 same-slot re-review 关闭，无新增 blocker。
- [x] 本 change 的 plan review 使用变更前 manual independent-review contract；最终 packet hashes、reviewer identity/context、findings 和 dispositions 已写入 `openspec/changes/generalize-independent-review-provider/plan-review.md`，且未声称 validator 已运行。
- [x] `openspec validate generalize-independent-review-provider --strict` 通过（OpenSpec CLI 1.3.1，telemetry disabled）。

## Implementation Gate

- [x] 先新增/修改结构测试并观察旧规则下的预期失败：workflow/OpenCode 结构断言失败，validator 模块缺失导致收集失败。
- [x] `docs/AGENT_RULES.md` 与 `.harness/rules.md` 改为 provider-neutral 独立评审合同。
- [x] repo-stage workflow/planner/review-loop skills 与 workflow-contract 保持同一语义。
- [x] OpenCode adapter 区分首轮隔离会话与 remediation re-review 会话复用。
- [x] 独立评审 receipt template、validator 和负样本覆盖 reviewer/implementer 重合、重复 reviewer、继承/未知上下文、cross-review visibility、baseline mismatch 和 stale re-review。
- [x] workflow/planner/review-loop 明确：未运行 validator、receipt 缺失或 validator 非零退出时，独立评审席位不得计数。
- [x] Validator claim ceiling 固定为 `mechanical_consistency_only`/`gate_ready=false`；宿主 dispatch provenance 与 pre-change-authority activation sequence 均保留为 required external checks。
- [x] Remediation lineage 解析 content-hashed original first-round receipt 的同一 slot/reviewer/finding IDs；final conclusion 拒绝矛盾或未关闭 findings。
- [x] 新 validator 只在脚本、template、负样本和 workflow wiring 全部完成后激活；激活后约束本阶段 final review 和后续阶段，不追溯替代本阶段 pre-implementation manual plan review。
- [x] 长期 `harness-development-workflow` spec 与 active delta 一致。
- [x] OpenCode 专用 adapter 说明仍保留，历史 archive/progress 事实未被改写。
- [x] 文档明确 development subagent 不等于 RepoPilot runtime subagent。

## Verification And Review Gate

- [x] focused structural tests 通过：32 passed（含独立 review remediation 的完整 history receipt、exact finding closure、clean-slot empty-set refresh 正样本及 claim-ceiling/path/conclusion/risk-count 负样本）。
- [x] 当前主机无 `powershell`/`pwsh`，未直接运行 `scripts/check_stage_docs.ps1` 与 `scripts/check_skill_evals.ps1`；翻译后的 stage-doc/skill-eval 结构检查退出 0。
- [x] 当前主机无 PowerShell，未运行 full `scripts/verify.ps1`；等价全仓 pytest 为 537 passed、3 failed（均在未修改路径），全仓 Ruff 有 97 个既有问题；changed Python files Ruff PASS，未宣称 full verify PASS。
- [x] `openspec validate generalize-independent-review-provider --strict` 和 `openspec validate --all` 通过（all：23 passed、0 failed）。
- [x] `git diff --check` 通过。
- [x] 本 low-risk 阶段按用户要求完成一个空上下文 Codex final review；未来 medium/high 阶段的 final review 数量仍由风险合同决定，每个 required slot 均满足同一独立性合同。
- [x] 空上下文 Codex final review first round 完成：packet `44d2dbd713a00442785b221bf8ec1a15729fe37f1cbb8204cf8186417184d234`，22/22 hashes 匹配；4 个 P1、3 个 P2 全部按 `fix`。第一次 same-slot re-review packet `53aa7428c4305d71587e8e8ed06f85dc4f7f8a78dd1913eec929476c19e3d17e` 通过 25/25 hashes；第二次 packet `48fac0b0d1247c448eda37d7667a66e18eeb999b3c95584be3a59064d6c814d1` 通过 26/26 hashes并关闭原 7 项，但新增 clean-slot empty-set refresh P1；第三次同 slot packet `dba6e6103f77f1791cec62aa4b2e40127a001b30a40a73afe393c295ecc08af4` 通过 27/27 hashes，关闭新增项且 `NO_FINDINGS`，无新 finding。
- [x] 实际 final receipt set 已写入 `.harness/reviews/generalize-independent-review-provider/implementation/review-set.json`；validator `--expected-phase implementation --required-slots 1` 零退出，1/1 slot、无 errors、packet hash 匹配。其 claim 仍限定为 `mechanical_consistency_only`/`gate_ready=false`；宿主控制器另行核对了 `fork_turns="none"` dispatch，pre-change process authority 另行核对了 activation sequence。
- [x] Focused Stage Debt Sweep 已覆盖 changed workflow/spec/skills/tests、direct rules/template/validator/receipt；未发现 `app/**`、runtime capability、归档历史、provider branding gate 或跨阶段 scope 泄漏。
- [x] 未执行 archive/commit/merge/push；原 `/Users/chelaile/agentic-codeops` dirty storage-refactor worktree 保持在 `feature/bootstrap-refactor-harness`，本阶段所有写入均位于隔离 worktree `codex/independent-review-provider`。
