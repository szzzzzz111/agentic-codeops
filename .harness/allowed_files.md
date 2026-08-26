# 当前 Harness 写入边界

Active OpenSpec change：none。`restore-deterministic-verification-baseline` 已归档，当前只进行受控 closeout。

该已归档阶段只恢复可重复、fail-closed 的验证核心：修复三个已复现 pytest failure，固定
Verification Runner 与仓库验证入口使用当前 Python 解释器，并修正上一阶段 final review packet
的当前事实。首次基线的 96 项 Ruff 分布在 56 个文件，超出本阶段窄行为修复范围；它们必须在紧随其后的
独立机械阶段清零。在两个阶段都完成前，不得声称 full repository verification baseline 已恢复，
也不得进入 model patch authoring。

Risk：`high / L3`。理由：本阶段改变 provider 结构化输出的 fail-closed 条件、Verification Runner
白名单 argv 和统一验证入口的失败语义；错误实现可能接受不受控深度 JSON、误报验证成功或在工具缺失时
静默跳过。

## 已冻结的语义 subject 精确路径

下列路径是本阶段相对 planning base 的穷尽 scope，不再代表 final post-archive review 后仍可继续编辑：

- `.harness/allowed_files.md`
- `.harness/review_checklist.md`
- `.harness/test_commands.md`
- `HANDOFF_TO_NEXT_CHAT.md`
- `README.md`
- `app/providers/model_provider.py`
- `app/verification/runner.py`
- `docs/AGENT_RULES.md`
- `docs/ARCHITECTURE.md`
- `docs/FEATURE_LIST.json`
- `docs/PROGRESS.md`
- `openspec/specs/grounded-answer-model-provider/spec.md`
- `openspec/specs/verification-runner/spec.md`
- `scripts/check_skill_evals.py`
- `scripts/check_skill_evals.ps1`
- `scripts/check_stage_docs.py`
- `scripts/check_stage_docs.ps1`
- `scripts/verify.py`
- `scripts/verify.ps1`
- `tests/test_model_provider.py`
- `tests/test_verification_runner.py`
- `tests/test_verify_scripts.py`

## 已冻结的语义 subject 目录前缀

- `.harness/authority/restore-deterministic-verification-baseline/`
- `.harness/reviews/restore-deterministic-verification-baseline/`
- `openspec/changes/restore-deterministic-verification-baseline/`
- `openspec/changes/archive/2026-08-26-restore-deterministic-verification-baseline/`

除以上 exact/prefix 路径外一律不写。当前 same-slot remediation 完成并冻结 final post-archive packet 后，
普通 runtime、tests、docs、specs、archived change 和 Harness semantic subjects 全部停止写入；只允许追加或更新
schema-valid 的 `.harness/reviews/restore-deterministic-verification-baseline/implementation/review-set.json` 与
`.harness/authority/restore-deterministic-verification-baseline/delivery-binding.json` 两个 evidence-tail 文件。
任何其他写入都会使 final review 失效。若必须扩大路径，立即停止并重新冻结 scope/authority，不以“顺手修复”继续。

## 明确 non-goals

- 本阶段不清理跨 56 个文件的 Ruff 96 项，不加全局 ignore，也不降低 Ruff 规则；另建机械阶段处理。
- 不实现或启用真实 model patch provider，不改变默认 fake/offline 行为。
- 不自动 apply、verify、promote、commit、merge、push patch proposal。
- 不激活 stage change replay v2；`provider_neutral.stage_state_cas/v1` 仍缺失。
- 不实现持久化 Operator approval、真实人工 authority、background/durable/subagent/connectors。
- 不处理 Verification Runner 进程树 containment；该项留给验证基线恢复后的独立窄阶段。
- 不把启动 RepoPilot 的当前解释器 site/package installation 视为 hostile supply-chain boundary；不实现 `-S`
  bootstrap、distribution 签名或 hostile `.pth` containment。
- 不修改依赖、公开 API、持久化 schema、网络默认值或原脏 worktree。

## 冻结事实与停止条件

- Planning base / authorized remote tip：`2c0d0d4e749e16e43d867931c58c6a82be56cf13`。
- Target：`origin/main`；当前 feature branch：`codex/restore-deterministic-verification-baseline`。
- Fetch/push endpoint 在首次网络接触前已本地证明唯一、相等；URL SHA-256 均为
  `775bee2fb56e792fc9057a93c77c948cdd627c0cc4afa23497d41f7c6276d16c`。
- 原生基线：Python 3.12.13、pytest 9.1.1、Ruff 0.16.0；`916 passed, 3 failed`；Ruff
  `96 errors / 56 files`。
- scope、risk、base、endpoint、branch、authorized tip 或 non-goal 漂移时立即停止并重新冻结。
- 实施前必须完成 internal plan review、两个 `fork_turns="none"` 独立 plan review slot、mechanical
  receipt validation 与 direct-user implementation confirmation/已冻结 host authority envelope。
- 当前 stage 保持 pre-change v1 cohort，action ceiling 收窄为 `archive`：v1 ordinal 中它同时允许较早的
  `implement`/`commit` 与 archive gate，但阻断 `merge`/`push`。本 stage 只形成 post-archive local reviewed
  candidate，不 merge/push。后继 Ruff stage 必须重新规划/授权；只有 full pytest、full Ruff 与 canonical
  verify 全绿后，才把两阶段 commit 一起 ff-only merge 并 lease push。
- implementation review 的 P0/P1 未清零时不得 archive 或 commit；整体 baseline 未全绿时不得 merge/push。
