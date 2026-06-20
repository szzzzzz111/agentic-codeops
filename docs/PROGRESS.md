# 项目进度

## Capability / Provider Truth Fix（2026-06-20）

- Change `fix-capability-provider-truth` 已于 2026-06-20 归档至
  `openspec/changes/archive/2026-06-20-fix-capability-provider-truth/`；当前无 active change。
- 风险级别：medium。只修改用户可见 capability-status、对应 tests、provider 事实文档与长期 spec；
  不修改 patch/worktree/verification/audit 执行行为，不创建 V24。
- RED 已证明旧 patch capability-status 错误声称 Persistent Audit / Recovery 和 Worktree Isolation
  未实现；GREEN 已更新为 V16-V23 当前能力，并保留 Verified Patch Promotion、自动 commit/push、
  默认真实 diff generation 尚未实现的边界。
- Patch Authoring provider 事实已澄清：默认应用始终使用 fake provider；
  `ModelPatchAuthoringProvider` 目前只能通过依赖注入用于测试或自定义装配，现有 Model Provider
  环境变量不会把它接入默认 `AgentLoop`。
- 最终定向验证：Kernel/API/provider 装配 3 passed；full verify 为 291 passed、1 skipped，ruff、
  stage docs 与 skill checks 通过；OpenSpec all strict validation 为 19 passed。
- Formal internal review 修复了 capability-status 与 V19 trace envelope 的规格冲突，并补充默认
  provider 装配的 characterization test。Focused Stage Debt Sweep 另发现 `V11` / `V12`
  capability-status 仍保留已被 V12/V13 推翻的 query rewrite、rerank、memory 历史 non-goal；
  该相邻债务不在本 patch-status change 内扩 scope，后续应独立修正或统一能力事实来源。
- Focused external review 已由 OpenCode 免费 DeepSeek reviewer 只读执行，结论为
  `No in-scope findings`。其关于 archive 后 HANDOFF marker 的 residual concern 已判为
  `reject`：checker 要求的是稳定字段名，归档后可写 `Active OpenSpec change: none`。
- Implementation、internal/external review、Stage Debt Sweep、验证、archive 与 `main` integration
  均已完成；精确 remote 同步状态以 Git 查询为准。

## 开发工作流收束（2026-06-20）

- 本轮为独立 process-only maintenance，不创建 V24，不修改 runtime、tests、FEATURE_LIST 或
  `/chat` contract。
- 新增 repo-local `repo-stage-workflow`，统一编排 OpenSpec planning、TDD、verification、
  internal review、独立 external review、focused Stage Debt Sweep、archive、merge/push 和一次
  final handoff；现有 planning/review/handoff skills 已收束为单一职责。
- 阶段按 `low / medium / high` 风险分级。Git/subprocess、持久化、权限、patch 生命周期和公开
  API 属于高风险，要求独立对抗式 external review；低风险流程文档不再机械套用完整外部链路。
- External review 的目标改为寻找独立反例，finding 需说明 severity、位置、触发条件、后果和建议
  regression test；反馈按 `fix / clarify / reject / defer` 分类。
- Stage Debt Sweep 聚焦 changed paths 和直接依赖/共享状态的 older paths，记录实际范围和 disposition，
  不再以无目标全仓扫描或单一 marker 代表完成。
- Archive 冻结正式 review 过的 runtime/test 状态；archive 后再改 runtime/test 会使旧 review 证据失效。
- 文档职责已拆分：review checklist 记录 gate 证据，PROGRESS 记录长期事实，HANDOFF 只记录下一轮行动
  上下文，Git/OpenSpec 命令提供实时 branch、HEAD、remote 和 active-change 状态。
- 历史失败基线已写入 skill eval：V19 动态 hash 导致自失效 closeout 循环，V22 在已勾选任务和内部
  final review 后仍发现 late runtime debt，外部 review 若仅重复 tasks/tests 不构成独立证据。
- 正式 review 修复两项流程缺口：实现确认前缺少显式 internal plan review；Windows PowerShell 5.1
  无 BOM UTF-8 脚本中的中文字符串导致 checker 解析失败，现已将 checker 保持为 ASCII。
- 最终验证：四个相关 skill 的 official quick validation 通过；skill eval structure scan 通过；
  `openspec validate --all` 18 passed, 0 failed；stage docs responsibility scan 通过；
  `scripts/verify.ps1` 通过，pytest 289 passed, 1 skipped，ruff 通过；
  `scripts/check_stage_closeout.ps1` 与 `git diff --check` 通过。
- 人工 Stage Debt Sweep 覆盖本轮 `.codex/skills/**`、Harness rules/templates/checkers、workflow spec、
  PROGRESS 与 HANDOFF；未修改 runtime/tests，因此没有 runtime adjacent path 或剩余代码债。

## V23 当前状态（2026-06-15）

- merge 后正式 code review 发现的两个 P1 与一个 P2 已完成 remediation：
  - registry path mismatch 通过 scoped Git admin back-reference 精确识别并 fail closed。
  - 损坏 worktree/patch SQLite metadata 返回安全 `metadata_invalid`，并尝试写入 attempt audit。
  - Git metadata 非法 UTF-8 使用 strict decode 并 fail closed。
- 定向测试 34 passed；相邻 V20-V22、patch store、AgentLoop、audit/API 回归 163 passed。
- 正式 re-review 未发现新增 P0/P1/P2；额外修复 admin back-reference 与完整 registry 结果不一致时
  错误允许 `registry_missing` reconciliation 的相邻 fail-closed 缺口。
- remediation 最终 full verify 通过：`pytest` 289 passed, 1 skipped；ruff、stage docs drift 与
  skill eval structure 均通过；正式 review findings 已全部关闭。
- remediation commit `8cf5f51 Fix V23 review findings` 已 fast-forward 合并到 `main`；
  `feature/v23-review-remediation` fully merged 并按审计惯例保留。合并后 stage closeout 与
  full verify 再次通过，formal review evidence gate 明确通过。
- 本次流程事故已沉淀到 Agent rules、Harness rules/checklist、stage planning template、repo-local review
  skill/evals、长期 harness workflow spec 与 `check_stage_closeout.ps1`。连续执行授权今后只减少中间确认，
  不得替代正式 review；未关闭 P0/P1 将机械阻断 closeout。
- 流程沉淀的历史负向 gate 测试确认：`check_stage_closeout.ps1` 在未关闭正式 review/P1
  findings 时会按预期失败；关闭 findings 后 stage closeout 与 full verify 均通过。
- 最终独立 review 未发现新增 P0/P1/P2。人工 Stage Debt Sweep 额外识别两项相邻旧路径的
  非阻塞硬化债并记录到“已知剩余代码债”；脚本通过不替代该人工审查。
- 流程补强进一步统一为 `Manual Judgment Gates`：stage intent/scope、safety/architecture、
  test adequacy、review triage、semantic parity、archive/merge/handoff truth 均要求可见人工结论。
  planning/closeout templates、repo-local planning/review/handoff skills/evals、长期 workflow spec 与
  closeout evidence marker 已同步；此前仅存在于本地 exclude 的 `openspec-stage-planner` 及其
  planning reference 已显式纳入 Git；脚本仅验证证据存在，不替代语义判断。
- V23 runtime、archive、review remediation、Stage Debt Sweep 与 `Manual Judgment Gates`
  流程补强已推送到 `agentic-codeops/main` through `887da54`。本地
  `feature/v23-worktree-disposal-reconciliation` 与 `feature/v23-review-remediation` 均 fully merged，
  按审计惯例保留。

- V23 runtime/archive merge 基线：`ffc691c`；后续 remediation 与 handoff closeout commits
  已进入 `main` / remote 历史。
- 当前工作分支：`main`
- 当前 active OpenSpec change：无
- 当前状态：runtime、tests、内部 review、archive 与 merge 已完成，等待下一阶段规划。
- 已创建 stage planning、proposal、design、tasks 与 spec deltas，并同步 harness 与
  `docs/FEATURE_LIST.json`（V23 `passes: true`）。
- 规划锁定 exact confirmed discard/reconcile、V23-before-V22 routing、受限 reconciliation、
  lifecycle transition table、strict ordered failure behavior 和 scoped persistent audit。
- Shared Git metadata runner timeout 与读取前硬上限被列为 blocking；patch store 规划新增 true
  no-create lookup 与 scoped status update，并保留 legacy `mark_status`。
- 内部 plan review 补强 exact linked-worktree ownership attestation、destructive action 前的
  scoped patch existence/status gate、true no-create patch store，以及按实际步骤表达的部分失败终态。
- Planning validation：strict V23 change validation 通过；`openspec validate --all` 18 passed；
  `scripts/check_stage_docs.ps1` 与 `git diff --check` 通过。
- TDD 与相关回归已覆盖 parser、scope、store、Git metadata hardening、normal disposal、
  reconciliation、idempotency、Harness、audit 与 `/chat` contract；相关回归 168 passed。
- 内部 review 修复 audit related-id 误分类、非终态 patch terminal gate、scoped worktree
  update 确认、V22 控制流插入回归，以及 cleanup/store partial-failure 步骤表达；当前无未记录阻断项。
- merge 后 full verify 通过：`pytest` 283 passed, 1 skipped；`ruff check .`、
  stage docs drift scan 与 skill eval structure scan 均通过；`openspec validate --all`
  18 passed, 0 failed；`git diff --check` 通过。
- implementation commit：`3991d4a Implement V23 worktree disposal reconciliation`。
- V23 已归档到
  `openspec/changes/archive/2026-06-15-v23-worktree-disposal-reconciliation/`，长期 specs 已同步。
- V23 已以 fast-forward 合并到 `main`；archive 后与 merge 后 stage closeout 均通过。

## V22 当前状态（2026-06-14）

- 当前基线分支：`main`（V22 archive merge 为 `6da406b`，后续 merge handoff closeout 为 `2843dda`）
- 当前工作分支：`main`
- 当前 active OpenSpec change：无
- 当前阶段：V22 Worktree Re-verification 已实现、review、归档、合并并推送；等待下一阶段规划。
- 已锁定明确命令、现有 `pytest`/`ruff`/`verify` 白名单、`user_id + repo_key` scope、
  fail-closed directory/registry/path/HEAD preflight、worktree-only execution、既有 lifecycle、
  patch `applied_in_worktree` 不变和逐次脱敏 persistent audit。
- 已确认 preflight failure 不覆盖原 lifecycle；rerun 次数由 scoped matching audit event
  count 表达，不新增 worktree/audit schema。
- 内部 plan review 已补强 malformed/unsafe re-verification-like 请求的路由拒绝语义：
  必须由 V22 整体拒绝，不得滑落到 standalone verification 或 repo search。
- 规划验证：`openspec validate v22-worktree-re-verification --strict` 通过；
  `openspec validate --all` 17 passed, 0 failed；`scripts/check_stage_docs.ps1` 与
  `git diff --check` 通过。
- 已实现严格 re-verification parser/routing、scoped fail-closed preflight、worktree-only
  verification 执行、既有 lifecycle 更新和 related redacted persistent audit。
- V22 targeted tests：`pytest tests/test_worktree_reverification.py -q`，30 passed。
- 相关回归：V22/V21/V20/Verification Runner/Persistent Audit/AgentLoop/Chat API，158 passed。
- full verification：`scripts/verify.ps1` 通过，`pytest` 254 passed, 1 skipped，ruff、
  stage docs drift 与 skill eval structure gate 均通过；`openspec validate --all` 18 passed。
- internal final review 修复了 V22 related audit 对既有 verification event 的无意扩面；
  修复后 audit/AgentLoop/API 回归 115 passed。
- 最终 review 进一步修复非法但已识别 re-verification attempt 丢失安全 worktree
  `related_id` 的审计缺口，并统一 archive-sync 所需的 worktree-isolation requirement header。
- 初次 Stage Debt Sweep 已扫描 current docs、harness、active OpenSpec、long-term specs、changed
  runtime paths 与 adjacent tests；post-merge 独立复核随后发现并修复 malformed Git registry
  output 夹带 expected path 时仍继续 HEAD 检查的 fail-closed 缺口，以及 durable docs parity 债。
- implementation commit：`30ae5a6 Add V22 worktree re-verification`。
- archive：`openspec/changes/archive/2026-06-14-v22-worktree-re-verification/`；archive 后
  OpenSpec 17 passed、stage closeout check 通过、full verify 254 passed / 1 skipped。
- V22 已 fast-forward 合并并推送到 `agentic-codeops/main` at `6da406b`；本地
  `feature/v22-worktree-re-verification` fully merged 且暂按审计惯例保留。
- V22 post-merge debt remediation：严格解析 `git worktree list --porcelain -z` record，
  malformed/unknown field 即使夹带 expected path 也在 registry preflight 立即 fail closed；
  同步修正 README/ARCHITECTURE/HANDOFF 当前链路遗漏 `WorktreeManager` / `worktree_create`、
  README V21 历史段落的 current-branch 措辞、PROGRESS 的 stale archive 范围和 baseline 表述。
- 非阻塞相邻硬化债：V21/V22 Git metadata subprocess 尚无独立 timeout，且 metadata
  output 上限在读取/capture 后判定；后续 worktree hardening 阶段应统一处理，不在本次
  post-merge remediation 中扩展执行模型。
- V22 post-merge debt remediation 验证：新增 RED/GREEN regression 1 passed；V22 targeted
  31 passed；V20/V21/V22/Verification Runner/Persistent Audit/AgentLoop/Chat API 相关回归
  161 passed；`scripts/verify.ps1` 通过，`pytest` 255 passed, 1 skipped；ruff、stage docs
  drift 与 skill eval structure gate 通过；`scripts/check_stage_closeout.ps1` 与 OpenSpec
  17/17 通过。
- V22 post-merge debt remediation commit `454d145 Fix V22 closeout debt` 已 fast-forward
  合并并推送到 `main`；本地 remediation feature branch fully merged 且按审计惯例保留。

### V22 External Plan Review Follow-up（2026-06-14）

- P1 路由顺序已由现有实现与规格确认满足：re-verification 位于 inventory/inspection 之后、Patch + Verify 与 standalone verification 之前。
- 修复遗漏的 lifecycle eligibility preflight：只允许 `patch_applied`、`verification_failed`、`verification_succeeded`，其他状态在 Git inspection 前 fail closed。
- Specs 已明确可区分 answer、mandatory `attempt_kind=worktree_reverification` / related worktree audit，以及 `execution_repo_path` 从 trusted repo root、固定 managed root 与 scoped worktree id 动态重建且不存 DB。
- Follow-up 验证：targeted 30 passed，相关回归 158 passed，full verify 254 passed / 1 skipped，OpenSpec 18 passed。

## V21 当前状态（2026-06-09）

- 当前工作分支：`main`
- 当前 active OpenSpec change：无
- 当前阶段：V21 Worktree Inventory / Inspection 已合并并推送，等待下一阶段规划。
- 已创建 stage planning、proposal、design、tasks 与 spec deltas，并同步 V21 harness
  写入边界和 review checklist。
- 已锁定纯只读/no-create 语义、Git-derived preview paths、untracked count-only、
  bounded safe preview 和 `worktree_inventory` / `worktree_inspection` audit skip。
- 内部 plan review 已修正 raw patch / hunk 输出可能被无界捕获的问题：patch body 与
  aggregate hunk count 必须流式消费，metadata Git 输出必须有显式上限。
- 规划验证：`openspec validate v21-worktree-inventory-inspection --strict` 通过；
  `openspec validate --all` 16 passed, 0 failed；`git diff --check` 通过。
- 已实现 scoped latest-20 inventory、详细 consistency inspection、Git-derived
  diffstat/hunk count、untracked count-only 与 bounded redacted preview。
- V20 `worktree_status` request-local event 已由 `worktree_inspection` 替代；
  inventory / inspection 保留安全 request-local trace，同时通过统一 audit wrapper
  的 skip predicate 禁止 persistent audit 写入。
- 内部实现 review 修复 metadata 路径穿越/revision option 注入、Git 启动失败安全降级，
  以及失败 per-file diff 的部分 preview 不应被保留等 fail-safe 问题。
- 当前 targeted regression：132 passed；implementation commit 前当前工作区默认
  `scripts/verify.ps1` 通过，pytest 为 224 passed, 1 skipped，ruff、stage docs drift
  与 skill structure gates 均通过；`openspec validate --all` 为 17 passed, 0 failed。
- Stage Debt Sweep 已覆盖 current docs、harness、active OpenSpec、长期 specs、changed
  runtime 与 adjacent tests；修复无界 metadata drain、异常超长 diff 单行和
  `_is_binary_file()` 全文件读取等邻接流式内存债，未发现未记录阻塞项。
- V21 internal final review 已完成并修复四类有效 findings：public metadata/tracked-path
  摘要未统一限长脱敏、preview 未脱敏 state/DB 路径且空 preview 不报告 counters、
  Git/SQLite 读取未显式关闭 optional writes、verification/metadata consistency 摘要
  不完整。损坏 worktree store 现安全降级，不打断 `/chat`。
- V21 external review 已完成，用户确认无阻塞 findings；当前进入最终 closeout gates，
  implementation commit 为 `ca8e299 Add V21 worktree inventory inspection`；尚未
  merge 或 push。
- V21 archive 首次因长期 specs 已在 implementation commit 中同步而安全中止，未修改
  文件；随后使用 `openspec archive v21-worktree-inventory-inspection --skip-specs -y`
  成功归档到 `openspec/changes/archive/2026-06-09-v21-worktree-inventory-inspection/`。
- V21 archive-after 验证：`openspec list` 为 No active changes found；
  `openspec validate --all` 为 16 passed, 0 failed；默认 `scripts/verify.ps1` 通过，
  pytest 为 224 passed, 1 skipped；`scripts/check_stage_closeout.ps1` 与
  `git diff --check` 通过。验证中发现并修复 README 必须同时保留 V20 历史归档 marker
  与 V21 最新归档 marker 的 parity 回归。
- `feature/v21-worktree-inventory-inspection` 已 fast-forward 合并到 `main` 并推送到
  `agentic-codeops/main` at `60c2dc2a8f7fb73e3f1c5fac90c99c54f3b7d106`；本地
  feature branch 按审计惯例保留。
- Merge 后默认 `scripts/verify.ps1` 通过，pytest 为 224 passed, 1 skipped；
  `scripts/check_stage_closeout.ps1`、`openspec validate --all` 与 `git diff --check`
  通过。

## V20 当前状态（2026-06-07）

- 当前工作分支：`main`
- 当前 active OpenSpec change：无
- 已实现受控 `worktree_create`、detached/locked Git worktree、内部
  `execution_repo_path` 传播、`applied_in_worktree` patch 状态、worktree 生命周期
  SQLite、持久审计事件和只读状态查询。
- standalone patch 与组合 Patch + Verify 均在隔离 worktree 内执行；standalone
  verification 保持主工作区语义。
- 真实 Git 端到端测试确认主工作区文件不变，worktree 内 patch 已应用。
- 当前 archive-after 验证：V20 worktree targeted 为 14 passed；`pytest -q` 为
  206 passed, 1 skipped；`openspec validate --all` 为 15 passed, 0 failed；
  默认 `scripts/verify.ps1` 与 `scripts/check_stage_closeout.ps1` 通过；
  `git diff --check` 通过。
- Stage Debt Sweep 已扫描 current docs、harness docs、active OpenSpec、long-term
  specs、changed runtime paths 和 adjacent runtime paths；长期 specs 未发现
  `TBD`、`TODO` 或 archive placeholder Purpose。
- 内部 final review 已修复两项 runtime P1：metadata 持久化失败时 locked worktree
  未完整回滚，以及 worktree id 冲突时可能误删既有 worktree；同时修复 README
  当前态冲突、design interface 偏差，并补齐创建失败的 AgentLoop 回归测试。
- external review 已完成，用户确认无阻塞 findings；implementation commit：
  `8be9b37 Add V20 worktree isolation`。
- V20 已归档到 `openspec/changes/archive/2026-06-07-v20-worktree-isolation/`，
  7 个新增 requirements 已同步到长期 specs。
- `feature/v20-worktree-isolation` 已 fast-forward 合并到 `main` 并推送到
  `agentic-codeops/main` at `35f9ecc7c1b19a317e5c461a436f7805c09a7743`；本地
  feature 分支按审计惯例保留。
- merge 后 `scripts/verify.ps1` 通过，`pytest` 为 206 passed, 1 skipped；
  `scripts/check_stage_closeout.ps1` 通过。

RepoPilot 当前定位为面向代码仓库分析任务的可控 Code Agent Harness。它不试图替代通用 AI IDE，而是围绕 Agent 工具调用边界、只读安全工具、执行追踪、可验证测试、review checklist 和 handoff 机制，构建可审计、可扩展的代码智能体执行框架。

## 当前状态

- 当前基线分支：`main`
- 当前工作分支：`main`
- 当前阶段：V22 Worktree Re-verification 已实现、归档、合并并推送；等待下一阶段规划
- 当前主流程：`/chat` 已通过 `CodeAgent -> AgentLoop -> AuditManager -> MemoryManager -> LongTaskManager -> AssistantControlSurface -> PatchManager -> WorktreeManager -> PatchVerifyLoop -> VerificationRunner -> QueryUnderstanding/SearchPlan -> QueryRewriteProvider -> ToolRegistry -> PermissionPolicy -> ApprovalGate -> ToolExecutor(repo_rag / worktree_create / patch_apply / verification_run) -> HybridRepoRetriever -> Reranker -> EvidencePack/ContextBudget -> GroundedAnswerGenerator -> ModelProvider` 使用 repo-local SQLite-backed Memory、repo-local Long Task 状态、repo-local Persistent Audit、只读 Assistant Control Surface、Safe Patch Authoring、Worktree Isolation、Patch + Verify Loop、Verification Runner、只读 hybrid repo RAG、deterministic rewrite/rerank、内部证据预算层和 grounded answer 边界；`/chat` 顶层响应结构保持不变
- 当前文件工具层：`list_files`、`read_file`、`search_code` 已实现；当前检索链路通过 `ToolExecutor(repo_rag) -> HybridRepoRetriever` 复用安全文件工具读取 repo 文本 chunk，且保留 `LexicalRepoRetriever` 作为一等检索通道
- Skill 相关状态：V4/V5 已实现 Skill Metadata Loader、Skill Content Loader；skill-aware loop 仅作为历史 draft/偏差记录，不作为当前主线；仍不执行 skill
- 当前 OpenSpec 状态：长期规格入口为 `openspec/specs/`；active change 为无；V10-V23 changes 已归档；不安装 Codex 全局 prompts；不保留 `.github` OpenSpec 生成物

## 流程偏差记录

- 2026-05-17，用户要求“先进行一个项目的状态理解，然后再进行 v6 的阶段开发”。本轮应先输出项目状态理解、提出 V6 阶段规划和边界，并等待用户确认后再进入实现。
- 实际执行中，Codex 直接从状态理解推进到 V6 OpenSpec、测试、代码实现、文档更新和验证，越过了用户确认门。
- 历史 V6 skill-aware 空 draft 已清理；V6 Kernel 变更已在用户 review 后保留、改造、提交并归档。
- 后续同类请求中，如果用户要求“先理解状态”或“先规划”，Codex 必须停在总结/方案确认点，不得自动进入实现。
- 2026-05-17，用户确认“V6 得重新开发”后，Codex 再次把该确认理解为可直接写代码，已创建 `v6-agent-harness-kernel` OpenSpec、harness 边界、测试和部分运行时代码。这再次越过了“先给 plan 审查，再实现”的确认门。
- 二次偏差处理：用户已在 review plan 后确认“没问题就进行开发，按计划来”，当前 `v6-agent-harness-kernel` 草稿改为保留并按计划改造。后续硬规则仍保留：凡是阶段重做/重新开发请求，Codex 只能先产出阶段 plan、OpenSpec/harness 边界和审查摘要；除非用户明确说“开始实现/写代码/按这个计划开发”，不得修改运行时代码或测试。
- 2026-05-27，V12 收口中 Codex 曾把“进入下一流程”误解为可直接 commit/archive，越过了最终 self-review 和人工判断点；已纠正。后续外部 review 无阻塞后，必须先做最终 self-review 并列出需用户亲自判断的阶段级事项，再执行 commit、archive、merge 或 push。

## 路线重定向：加速但保持轻量工程化

用户希望 RepoPilot 后续不只是玩具项目，而是更偏工程化的 Agent Harness；同时由于主要由个人使用 AI 开发，不能走重型企业平台路线。后续路线应采用 lightweight industrial harness：不堆中间件、不堆概念，但也不能停留在 demo 接口或假执行；工程化优先体现在真实可用闭环、权限审批、审计、可恢复状态、验证、隔离和交接文档。

原则：

- 工程化但轻量：先用内存、JSON、SQLite 或简单文件存储打通接口，只有在阶段需要时才引入 PostgreSQL、Milvus、Elasticsearch、Kafka 等外部依赖。
- 纵向切片优先：每个阶段都交付一条可运行闭环，而不是只堆抽象层。
- 真实闭环优先：后续阶段要逐步交付可确认 patch、受控验证、失败恢复和隔离执行，而不是继续只增加接口骨架。
- Harness 边界优先：Provider、Router、AgentLoop、ToolRegistry、ToolExecutor、Memory、RAG、Skill、Trace 分层明确。
- 可审计优先：model/tool/skill/memory 调用都要有结构化摘要和脱敏策略。
- 可验证优先：每个阶段都要有最小测试和默认验证命令。
- 可进化 Skill：skill 不是一次性 prompt 文件，后续应逐步支持 metadata、content、selection、tool limits、version、review 和演进记录。
- 检索 grep-first：RepoPilot adopts a grep-first, RAG-assisted retrieval stance；lexical/path/symbol/exact match 是代码仓库分析的主要可审计基线，embedding/hybrid retrieval 只作为语义召回辅助。

建议后续路线：

- V6：Agent Harness Kernel + Router Kernel。已建立 `RequestRouter`、`ToolRegistry`、`AgentLoop` 和 `TraceEvent` 四个最小运行时骨架；`ProviderAdapter`、`ContextBuilder`、`SkillRegistry` 和 `SessionStore` 留到后续阶段，不在 V6 写运行时代码。历史 `v6-skill-aware-agent-loop` draft 只作为流程偏差记录和 skill 子能力参考。
- V7：Permission + Approval Gate。已引入确定性 allow/deny/ask 策略和最小审批占位；高风险动作真实确认仍留到后续阶段。
- V8：Query Understanding + Lexical Repo RAG。已将旧“大 Repo RAG Engineering”收窄为 deterministic 检索前理解、repo-local chunk、lexical scoring 和 citation。
- V9：Embedding Retrieval + Hybrid Search。补 embedding provider、可替换检索接口和 hybrid fusion；Milvus/ES 暂不默认引入。
- V10：Evidence Pack + Context Budget。先把检索结果整理为可审计证据包和上下文预算边界，不做回答生成。
- V11：Grounded Answer / Model Provider Boundary。已引入回答生成边界、证据约束策略、默认 fake provider 和可选 OpenAI-compatible provider。
- V12：Query Rewrite + Rerank。已引入默认 deterministic multi-query rewrite、before-Evidence rerank 和内部 audit 边界；真实 LLM rewrite/rerank 留作后续独立阶段。
- V13：Memory。已实现 repo-local SQLite-backed PREF/LTM、进程内 STM、明确 memory 指令和内部 memory audit；不做向量 memory 或自动模型总结。
- V14：Long Task / ReAct Skeleton。已加入 repo-local Long Task control plane、任务状态、pause/resume、scratch 摘要、quota/archive 和摘要级 ReAct trace；真实 subagents、worktree automation 和后台任务仍为非目标。
- V15：Assistant Control Surface。已实现并归档；把 `/chat`、Memory、Long Task 和 RAG 组织成更好用的助手入口，并提供轻量只读状态聚合；不写代码、不执行 shell、不后台运行。
- V16：Safe Patch Authoring。已实现并归档；基于 repo evidence 生成 patch proposal / diff，用户明确确认后才通过受控 `patch_apply` apply；不执行测试、不自动 commit、不创建 worktree。
- V17：Verification Runner。通过白名单验证命令执行 `pytest`、`ruff check .` 或 `scripts/verify.ps1` 等受控验证，并经过权限和审批边界。
- V18：Patch + Verify Loop。串联明确确认下的 pending patch apply 与白名单 verify，返回组合结果、失败摘要和下一步建议；不自动生成或再次 apply patch，持久恢复由 V19 提供。
- V19：Persistent Audit / Recovery。用轻量 SQLite 持久化关键 trace、patch attempt、verification result 和 task event，支持跨 session 恢复。
- V20：Worktree Isolation。在 patch/verify 成熟后引入受控 git worktree，隔离改动和验证，避免污染主工作区。
- V21（计划候选）：Worktree Inventory / Inspection。保持纯只读，提供 scoped
  inventory、diffstat、changed files、限长脱敏 diff preview、验证摘要和一致性检查。
- V22（已完成）：Worktree Re-verification。明确触发白名单验证重跑，复用现有
  verification 状态，patch 保持 `applied_in_worktree`，每次结果进入脱敏 audit。
- V23（计划候选）：Worktree Disposal / Reconciliation。明确确认后幂等清理并协调
  Git registry、目录和 metadata；discard 后使用独立终态，不回退为 `pending`。
- V24（计划候选）：Verified Patch Promotion。仅提升验证成功且内容完整性校验通过的
  原始受控 patch；要求主工作区干净且 `HEAD == base_commit`，不自动 commit/push。
- V24 完成后重新评估 Operator Control、Durable Execution、Background Worker、
  subagents、connectors、notifications、heartbeat/cron 和 always-on assistant，
  不提前锁定后续顺序或公开 API。

LLMGateway 设计备忘：

- 当前 RepoPilot 已有的是 V11 Model Provider Boundary，不是完整工业 LLMGateway。
- 对项目有用的方向是轻量稳定性控制面：模型调用统一入口、环境变量密钥边界、timeout、错误 fallback、citation validation、脱敏 provider audit、必要时的小次数 retry 和简单模型路由。
- 参考资料：JavaGuide《大模型 API 调用工程实践：流式输出、重试、限流与结构化返回》（`https://javaguide.cn/ai/llm-basis/llm-api-engineering.html`）可作为 V16+ 规划参考；吸收流式输出取消/超时、结构化返回 schema/fallback、provider request audit、重试/幂等和解析失败处理等轻量工程实践。
- 暂不追求全局限流、熔断集群、多租户成本账单、供应商竞价、复杂控制台或分布式日志系统；这些只有在多 provider、长任务或 always-on 场景真实出现后再单独规划。
- 后续增强真实模型调用时，必须继续保护 Evidence Pack、Grounded Answer citation validation、`/chat` contract 和默认离线验证。

## 已完成

### V1：Agent 服务入口和可追踪请求结构

- FastAPI 应用可启动。
- `POST /chat` 接收 `user_id`、`session_id`、`message`、`repo_path`。
- 每次请求生成唯一 `trace_id`。
- 返回 `answer`、`related_files`、`tool_calls`。
- V1 建立 Agent 服务入口和可追踪响应结构，`related_files`、`tool_calls` 作为后续审计字段保留。
- pytest 覆盖 `/chat` 基础行为和 `trace_id` 不重复。

### V2：安全只读仓库工具层

- `list_files(repo_path)`：列出仓库内允许访问的文本文件。
- `read_file(repo_path, file_path, max_chars=12000)`：读取仓库内文本文件并限制长度。
- `search_code(repo_path, keyword, max_results=20)`：搜索关键词并限制结果数。
- 文件工具限制访问在 `repo_path` 内。
- 提供路径逃逸防护，跳过敏感文件、隐藏目录、忽略目录和二进制文件。
- V2 工具只读，不写文件、不删文件、不执行 shell。
- 新增 `tests/test_file_tools.py`。

### Harness V0

- 新增 `AGENTS.md` 作为 Agent 入口地图。
- 新增 `docs/ARCHITECTURE.md` 记录架构边界。
- 新增 `docs/AGENT_RULES.md` 记录 Agent 工作规则。
- 新增 `docs/FEATURE_LIST.json` 记录可验收功能清单。
- 新增 `HANDOFF_TO_NEXT_CHAT.md` 作为跨 session 交接文档。
- 新增 `scripts/verify.ps1` 作为本地验证入口。

### V3：统一工具执行边界和最小 Agent Loop

- V3 legacy specs 已迁移到 `openspec/specs/agent-loop-tool-execution/spec.md`。
- 新增轻量 `ToolExecutor`，当前只包装 `search_code`。
- `CodeAgent` 使用最小确定性规则提取关键词，并通过 `ToolExecutor` 调用只读搜索。
- `/chat` 返回真实 `related_files` 和 `tool_calls` 摘要。
- V3 的意义是把工具调用统一收口，给后续权限、审批、沙箱、trace audit、eval 和 reflection 留扩展点，不是让 Agent 变成通用 AI 编程助手。
- 新增 `UNIQUE_BUG_TOKEN` 命中、无命中、敏感文件不泄露和错误摘要脱敏测试。

## 最近验证

- 2026-05-31，V16 OpenSpec 计划验证：`openspec validate v16-safe-patch-authoring`：通过。
- 2026-05-31，V16 targeted RED：`pytest tests\test_patch_authoring.py tests\test_agent_harness_kernel.py::test_permission_policy_allows_patch_apply_only_via_confirmation_context tests\test_agent_harness_kernel.py::test_agent_loop_handles_patch_confirm_before_repo_search tests\test_agent_harness_kernel.py::test_agent_loop_reports_v16_patch_capability_without_repo_search tests\test_chat_api.py::test_chat_endpoint_patch_proposal_keeps_contract_and_does_not_write tests\test_chat_api.py::test_chat_endpoint_confirm_patch_applies_without_running_verification -q`：预期失败，缺少 `ToolInvocationContext` 和 patching runtime。
- 2026-05-31，V16 targeted GREEN：同一 targeted 命令：11 passed。
- 2026-05-31，V16 相关回归：`pytest tests\test_patch_authoring.py tests\test_agent_harness_kernel.py tests\test_chat_api.py -q`：72 passed。
- 2026-05-31，V16 self-review follow-up RED：新增 provider unsafe diff 不得创建 pending patch 测试；`pytest tests\test_patch_authoring.py::test_patch_manager_rejects_unsafe_diff_before_creating_pending_patch -q` 先失败，暴露 unsafe `.env` diff 会进入 `.repopilot/patches.sqlite3`。
- 2026-05-31，V16 self-review follow-up 修复：Patch proposal 创建 pending patch 前执行 unified diff 只读 preflight，校验 repo 内相对路径、安全文件、二进制、context 和 `target_files` 一致性。
- 2026-05-31，V16 self-review follow-up 验证：`pytest tests\test_patch_authoring.py -q`：7 passed；`pytest tests\test_patch_authoring.py tests\test_agent_harness_kernel.py tests\test_chat_api.py -q`：73 passed。
- 2026-05-31，V16 external review follow-up RED：新增 provider summary 本机绝对路径不得进入 `/chat.answer` 测试；`pytest tests\test_patch_authoring.py -q` 先失败，暴露 patch proposal answer 会原样拼接 `patch.summary`。
- 2026-05-31，V16 external review follow-up 修复：patch proposal answer 在公开展示前对 provider summary 执行本机绝对路径脱敏；复核 `__pycache__` / `.pyc` 未被 git 跟踪且已由 `.gitignore` 忽略，并清理本地 `app\patching\__pycache__`、`app\providers\__pycache__` 生成目录。
- 2026-05-31，V16 external review follow-up targeted 验证：`pytest tests\test_patch_authoring.py -q`：8 passed。
- 2026-05-31，V16 external review follow-up 相关回归：`pytest tests\test_patch_authoring.py tests\test_agent_harness_kernel.py tests\test_chat_api.py -q`：74 passed。
- 2026-05-31，V16 final stage debt sweep：已复核 active OpenSpec、harness、README、ARCHITECTURE、PROGRESS、FEATURE_LIST、HANDOFF 和长期 specs；修正 handoff 中残留的旧 “no active change” harness 状态，并补齐 V15 `assistant-control-surface` 长期 spec Purpose；未发现新的阶段内 P0/P1/P2。
- 2026-05-31，V16 OpenSpec 全量验证：`openspec validate --all`：11 passed, 0 failed。
- 2026-05-31，V16 默认验证：`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 158 passed, 1 skipped；`ruff check .` All checks passed；stage docs drift scan 无漂移。
- 2026-05-31，V16 diff 验证：`git diff --check`：通过，仅有 CRLF 换行提示。
- 2026-05-31，V16 implementation commit：`d32a367 Add V16 safe patch authoring`。
- 2026-05-31，V16 archive：`openspec archive v16-safe-patch-authoring -y` 已完成，归档到 `openspec/changes/archive/2026-05-31-v16-safe-patch-authoring/`；长期 specs 已同步，新增 `openspec/specs/safe-patch-authoring/spec.md`。
- 2026-05-31，V16 archive 后 OpenSpec 全量验证：`openspec validate --all`：11 passed, 0 failed。
- 2026-05-31，V16 archive 后默认验证：`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 158 passed, 1 skipped；`ruff check .` All checks passed；stage docs drift scan 无漂移。
- 2026-05-31，V16 archive closeout：`powershell -ExecutionPolicy Bypass -File scripts\check_stage_closeout.ps1`：通过；包含 no active changes、OpenSpec 全量验证、stage docs drift scan 和 `git diff --check`。
- 2026-05-31，V16 merge：已 fast-forward 合并 `feature/v16-safe-patch-authoring` 到 `main`；merge 后 `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1` 通过，`pytest` 158 passed, 1 skipped，`ruff check .` All checks passed；`powershell -ExecutionPolicy Bypass -File scripts\check_stage_closeout.ps1` 通过。
- 2026-06-03，V17 planning：已在 `feature/v17-verification-runner` 创建 active OpenSpec change `v17-verification-runner`，包含 `stage_planning.md`、proposal、design、tasks，以及 `verification-runner` / `agent-loop-tool-execution` / `chat-api` / `harness-development-workflow` spec delta；已同步 `.harness/allowed_files.md` 和 `.harness/review_checklist.md`；`openspec validate v17-verification-runner` 通过。
- 2026-06-03，V17 implementation RED：新增 verification runner、PermissionPolicy / ApprovalGate、AgentLoop 和 `/chat` contract 测试；targeted RED 按预期失败，缺少 `app.verification`、`ToolInvocationContext.command_label`、`ToolExecutor.verification_run` 和 AgentLoop verification 分支。
- 2026-06-03，V17 targeted GREEN：`pytest tests/test_verification_runner.py tests/test_agent_harness_kernel.py::test_permission_policy_allows_verification_run_only_via_context tests/test_agent_harness_kernel.py::test_agent_loop_runs_verification_after_patch_and_before_repo_search tests/test_agent_harness_kernel.py::test_agent_loop_rejects_unsafe_verification_syntax_before_repo_search tests/test_chat_api.py::test_chat_endpoint_verification_keeps_contract_and_redacts_output tests/test_chat_api.py::test_chat_endpoint_verification_rejects_arbitrary_shell_without_repo_rag -q`：11 passed。
- 2026-06-03，V17 相关回归：`pytest tests/test_verification_runner.py tests/test_agent_harness_kernel.py tests/test_chat_api.py -q`：78 passed。
- 2026-06-03，V17 OpenSpec 验证：`openspec validate v17-verification-runner` 通过；`openspec validate --all`：12 passed, 0 failed。
- 2026-06-03，V17 默认验证：`powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` 通过；`pytest` 170 passed, 1 skipped；`ruff check .` All checks passed；stage docs drift scan 无漂移。
- 2026-06-03，V17 diff 验证：`git diff --check` 通过，仅有 CRLF 换行提示。
- 2026-06-03，V17 外部 review：已覆盖 verification runner、AgentLoop integration、ToolExecutor boundary、tests 和 OpenSpec change set，未发现 P0/P1/P2 问题。
- 2026-06-03，V17 implementation commit：已创建 `8fe1fde Add V17 verification runner`。
- 2026-06-03，V17 archive：`openspec archive v17-verification-runner -y` 已完成；长期 specs 已同步，新增 `openspec/specs/verification-runner/spec.md`；归档路径为 `openspec/changes/archive/2026-06-03-v17-verification-runner/`。
- 2026-06-03，V17 merge：已 fast-forward 合并 `feature/v17-verification-runner` 到 `main`；merge 后 `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` 通过，`pytest` 170 passed, 1 skipped，`ruff check .` All checks passed；`powershell -ExecutionPolicy Bypass -File scripts/check_stage_closeout.ps1` 通过。
- 2026-06-04，V18 planning：已在 `feature/v18-patch-verify-loop` 创建 active OpenSpec change `v18-patch-verify-loop`，包含 `stage_planning.md`、proposal、design、tasks，以及 `patch-verify-loop` / `safe-patch-authoring` / `verification-runner` / `agent-loop-tool-execution` / `chat-api` / `harness-development-workflow` spec delta；已同步 `.harness/allowed_files.md` 和 `.harness/review_checklist.md`；`openspec validate v18-patch-verify-loop` 通过。
- 2026-06-04，V18 targeted RED：新增组合确认 parser、verification label、AgentLoop 和 `/chat` contract 测试；targeted RED 按预期失败，缺少 `parse_patch_verify_confirmation` 和 `parse_verification_label`。
- 2026-06-04，V18 targeted GREEN：`pytest tests/test_patch_authoring.py::test_parse_patch_verify_confirmation_requires_patch_id_and_label tests/test_patch_authoring.py::test_parse_patch_verify_confirmation_rejects_half_parse_without_apply tests/test_verification_runner.py::test_patch_verify_label_parser_uses_same_whitelist_boundaries tests/test_agent_harness_kernel.py::test_agent_loop_patch_verify_combination_applies_then_runs_verification tests/test_agent_harness_kernel.py::test_agent_loop_patch_verify_invalid_label_rejects_without_apply tests/test_agent_harness_kernel.py::test_agent_loop_patch_verify_does_not_run_verification_when_apply_fails tests/test_chat_api.py::test_chat_endpoint_patch_verify_loop_keeps_contract tests/test_chat_api.py::test_chat_endpoint_patch_verify_rejects_invalid_label_without_tool_calls -q`：8 passed。
- 2026-06-04，V18 相关回归：`pytest tests/test_patch_authoring.py tests/test_verification_runner.py tests/test_agent_harness_kernel.py tests/test_chat_api.py -q`：94 passed。
- 2026-06-04，V18 OpenSpec 全量验证：`openspec validate --all`：13 passed, 0 failed。
- 2026-06-04，V18 默认验证：`powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`：通过；`pytest` 178 passed, 1 skipped；`ruff check .` All checks passed；stage docs drift scan 无漂移。
- 2026-06-04，V18 外部 review：已处理外部 P2 反馈；确认 spec delta 实际存在，补齐 README 和 HANDOFF 当前链路中的 `PatchManager -> PatchVerifyLoop -> VerificationRunner`；外部 review 随后确认无阻塞问题。
- 2026-06-04，V18 implementation commit：已创建 `e76807d Add V18 patch verify loop`。
- 2026-06-04，V18 archive：`openspec archive v18-patch-verify-loop -y` 已完成；长期 specs 已同步，新增 `openspec/specs/patch-verify-loop/spec.md`；归档路径为 `openspec/changes/archive/2026-06-04-v18-patch-verify-loop/`。
- 2026-06-04，V18 archive 后 OpenSpec 全量验证：`openspec validate --all`：13 passed, 0 failed。
- 2026-06-04，V18 archive 后默认验证：`powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`：通过；`pytest` 178 passed, 1 skipped；`ruff check .` All checks passed；stage docs drift scan 无漂移。
- 2026-06-04，V18 archive closeout：`powershell -ExecutionPolicy Bypass -File scripts/check_stage_closeout.ps1`：通过；包含 no active changes、OpenSpec 全量验证、stage docs drift scan 和 `git diff --check`。
- 2026-06-05，V18 archive merge/push audit：当时 `main`、`agentic-codeops/main` 和本地 `feature/v18-patch-verify-loop` 均指向 `3c7a8b3955bbcb0848ad56f0b074c70d1a506107`（`Archive V18 patch verify loop`），确认 V18 archive 已进入远端主线；该记录随后由 V18 closeout debt remediation commit `8b93330` supersede，当前真实 V19 基线为 `8b93330`。
- 2026-06-05，V18 post-merge/handoff audit 发现流程债：`README.md`、`docs/PROGRESS.md` 和 `HANDOFF_TO_NEXT_CHAT.md` 仍残留 V18 closeout / merge-push 决策前状态；`openspec/specs/patch-verify-loop/spec.md`、`openspec/specs/verification-runner/spec.md` 和 `openspec/specs/safe-patch-authoring/spec.md` 仍残留 archive 自动生成的 Purpose 占位；`scripts/check_stage_docs.ps1` 当时通过但未拦截上述问题。
- 2026-06-05，V18 closeout debt remediation：已补齐长期 spec Purpose，更新 durable docs 为真实 main/remote 状态，强化 stage docs drift scan 覆盖 long-term specs、stale V18 closeout wording 和 archive Purpose 占位，并清理本地未跟踪 `__pycache__` 生成目录。
- 2026-06-05，branch retention：本地 `feature/v18-patch-verify-loop` 已 fully merged，且与 `main` 同 hash；按本仓库历史惯例暂保留已合并 feature 分支，不做自动删除。若后续需要清理，应单独执行分支清理并记录。
- 2026-06-05，V18 closeout debt remediation 验证：`openspec validate --all`：13 passed, 0 failed；`powershell -ExecutionPolicy Bypass -File scripts/check_stage_docs.ps1`：通过，扫描 23 个文件；`powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`：通过，`pytest` 178 passed, 1 skipped，`ruff check .` All checks passed，stage docs drift scan 无漂移；`git diff --check` 通过，仅有 CRLF 换行提示。
- 2026-06-05，V18 closeout debt remediation commit/merge/push：`8b93330 chore: close v18 post-merge debt` 已 fast-forward 合并到 `main` 并推送到 `agentic-codeops/main`；V18 closeout debt branch 按审计惯例保留，不在 V19 中自动删除。
- 2026-06-05，V19 OpenSpec/harness：已创建 `openspec/changes/v19-persistent-audit-recovery/`，新增长期 `openspec/specs/persistent-audit-recovery/spec.md`，并同步 `.harness/allowed_files.md` 与 `.harness/review_checklist.md` 到 V19 边界；`openspec validate v19-persistent-audit-recovery --strict` 通过，`openspec validate --all` 15 passed, 0 failed。
- 2026-06-05，V19 targeted implementation 验证：`pytest tests/test_persistent_audit.py -q`：9 passed；`pytest tests/test_agent_harness_kernel.py tests/test_chat_api.py tests/test_persistent_audit.py -q`：85 passed；`ruff check app/audit app/harness/kernel.py tests/test_persistent_audit.py tests/test_agent_harness_kernel.py tests/test_chat_api.py`：All checks passed。
- 2026-06-05，V19 full verification：`powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` 通过，`pytest` 187 passed, 1 skipped，`ruff check .` All checks passed，stage docs drift scan 无漂移；`openspec validate --all` 15 passed, 0 failed；`git diff --check` 通过，仅有 CRLF 换行提示。
- 2026-06-05，V19 Stage Debt Sweep：已扫描 current docs、harness docs、active OpenSpec、long-term specs、changed runtime paths 和 adjacent older runtime paths；修复额外发现的 `docs/FEATURE_LIST.json` JSON 结构债、V19 passes 状态、V18 archive hash 历史表述和 checklist evidence；长期 specs 未发现 `TBD`、`TODO`、`created by archiving change` Purpose 占位。
- 2026-06-05，V19 external review follow-up：runtime/tests 无 P0/P1/P2；已修复文档 P2，将 `AuditManager(persistent redacted audit / read-only recovery)` 补入 `HANDOFF_TO_NEXT_CHAT.md` 与 `README.md` 当前主链路图，使其与 `docs/ARCHITECTURE.md` 一致。
- 2026-06-05，V19 archive：`openspec archive v19-persistent-audit-recovery -y` 已完成；长期 specs 已同步，归档路径为 `openspec/changes/archive/2026-06-05-v19-persistent-audit-recovery/`；archive 后 `openspec validate --all` 14 passed, 0 failed，`scripts/check_stage_docs.ps1` 扫描 24 files 无 drift，long-term specs 未发现 Purpose 占位。
- 2026-06-05，V19 archive 后 full verification：`powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` 通过，`pytest` 187 passed, 1 skipped，`ruff check .` All checks passed，stage docs drift scan 无漂移；`git diff --check` 通过，仅有 CRLF 换行提示。
- 2026-06-05，V19 merge/push closeout：`feature/v19-persistent-audit-recovery` 已 fast-forward 合并到 `main` 并推送到 `agentic-codeops/main` at `add702d62bcf737925b6418d3c9b9fb258e7ff35`；随后 post-merge handoff docs closeout commits 已推送到 `main`/remote；本地 feature branch 已 fully merged 并保留在 `add702d62bcf737925b6418d3c9b9fb258e7ff35`，按本仓库审计惯例不自动删除。
- 2026-06-05，V19 post-merge docs verification：durable docs 已更新真实 main/remote 状态、commit hash、验证结果和 branch retention 决策；stale phrase 与 long-term Purpose 扫描无命中；`openspec validate --all` 14 passed, 0 failed；`scripts/check_stage_docs.ps1` 扫描 24 files 无 drift；`powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` 通过，`pytest` 187 passed, 1 skipped，`ruff check .` All checks passed；`git diff --check` 通过，仅有 CRLF 换行提示。
- 2026-06-06，V19 post-closeout documentation parity audit：用户发现 README 未完整同步 V19。复核确认 README 缺少 V19 当前能力专章和阶段历史，路线图仍停在 V18，当前非目标误把已实现 persistent audit 列为未来项；PROGRESS/ARCHITECTURE/HANDOFF 也有同类 stale wording。现已修复 durable docs，并强化 `scripts/check_stage_docs.ps1`，要求 README 必须包含 V19 当前能力、V19 阶段历史和已归档至 V19 的路线图标记，同时拦截 V19 未完成及 persistent audit 仍属 Roadmap 的 stale wording。
- 2026-06-06，V19 documentation parity audit 验证与测试债修复：首次 full verify 发现 `tests/test_chat_api.py::test_docs_keep_stage_route_map_consistent` 仍强制要求旧 V18 archived marker，说明旧测试锁定了陈旧路线图。已将测试更新为正向验证 README 的 V19 当前能力、V19 阶段历史和已归档至 V19 路线图，并显式拒绝旧 V18 marker；targeted test 1 passed，最终 `scripts/verify.ps1` 187 passed, 1 skipped，ruff 与 stage docs drift scan 通过。
- 2026-06-06，post-closeout semantic parity follow-up：继续复核发现 README 当前能力缺少 Verification Runner 专章及 `app/verification/` 模块说明，ARCHITECTURE 当前能力总览漏写 Patch + Verify Loop / Persistent Audit，PROGRESS 对 V18 过度描述为会再次 patch 的可恢复闭环，HANDOFF 末尾仍使用 V19 未来规划时态。现已修复，并扩展 stage docs checker 与 parity test 覆盖 Verification Runner 当前能力。
- 2026-06-06，post-closeout semantic parity follow-up 验证：`scripts/check_stage_closeout.ps1` 通过，无 active OpenSpec change，14 specs valid，stage docs 无 drift，diff check 通过；`scripts/verify.ps1` 通过，`pytest` 187 passed, 1 skipped，`ruff check .` All checks passed。
- 2026-06-07，process skill follow-up：复盘 V19 closeout 暴露的流程错误并沉淀到 repo-local skills。`openspec-archive-change` 新增 archive 前 delta `ADDED/MODIFIED/REMOVED` header 对齐检查；`repo-stage-review-loop` 新增 archive-syncable delta gate、positive README parity 和 stale-test gate；`repo-stage-handoff` 新增 README 分职责 parity、测试锁定陈旧文档检查、full verify 和稳定 post-merge hash 表述；stale-state checklist 同步上述检查。Skill 改动仅属于开发流程纪律，不是 RepoPilot runtime 能力。
- 2026-06-07，process skill follow-up 验证：原先被 `.git/info/exclude` 排除的 repo-stage-handoff / repo-stage-review-loop / stale-state checklist 已显式加入 Git，确保改进会随仓库持久化；通用 `quick_validate.py` 因当前 bundled Python 缺少 `PyYAML` 无法运行，已人工核对 skill frontmatter，并通过 `scripts/check_stage_closeout.ps1`、`scripts/verify.ps1`（187 passed, 1 skipped）、ruff、stage docs drift scan 和 staged diff check。
- 2026-06-07，skill authoring follow-up：吸收外部 skill 编写经验中适合本仓库的部分，将 repo-stage-handoff、repo-stage-review-loop、openspec-archive-change 的 description 收窄为加载时机/用户意图，并分别新增 `references/evals.md`，覆盖 positive、negative、edge 和 failure traps。未引入当前仓库没有执行环境的多模型 eval 平台、`depends` 或 `config.json`。
- 2026-06-07，skill authoring follow-up 验证：轻量 eval 结构检查确认三个关键 skill 均包含 Positive/Negative/Edge/Failure Traps；首次检查发现 archive eval 缺少独立 Failure Traps 并已补齐；`scripts/check_stage_closeout.ps1` 与 `scripts/verify.ps1` 通过，`pytest` 187 passed, 1 skipped，ruff 和 stage docs drift scan 通过。
- 2026-06-07，skill eval structure gate：新增 `scripts/check_skill_evals.ps1` 并接入 `scripts/verify.ps1` 与 `scripts/check_stage_closeout.ps1`，确定性检查关键流程 skill 的触发式 description、50-word 上限、eval reference 以及 Positive/Negative/Edge/Failure Traps 四类结构。该结构 gate 不替代未来真实多模型 routing eval。
- 2026-06-07，skill eval structure gate 验证：独立结构扫描通过，`scripts/check_stage_closeout.ps1` 通过，`scripts/verify.ps1` 通过（`pytest` 187 passed, 1 skipped；ruff、stage docs drift、skill eval structure scan 均通过）。
- 2026-05-31，V15 OpenSpec 计划验证：`openspec validate v15-assistant-control-surface`：通过。
- 2026-05-31，V15 Assistant Control Surface targeted TDD 验证：`pytest tests/test_assistant_control_surface.py tests/test_agent_harness_kernel.py::test_agent_loop_answers_assistant_status_without_repo_rag tests/test_agent_harness_kernel.py::test_agent_loop_memory_command_still_precedes_assistant_status tests/test_agent_harness_kernel.py::test_agent_loop_long_task_command_still_precedes_assistant_status tests/test_chat_api.py::test_chat_endpoint_assistant_status_keeps_contract_and_does_not_create_state -q`：10 passed。
- 2026-05-31，V15 OpenSpec 全量验证：`openspec validate --all`：10 passed, 0 failed。
- 2026-05-31，V15 默认验证：`powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`：通过；`pytest` 144 passed, 1 skipped；`ruff check .` All checks passed；stage docs drift scan 无漂移。
- 2026-05-31，V15 diff 验证：`git diff --check`：通过，仅有 CRLF 换行提示。
- 2026-05-31，V15 external review follow-up RED：新增控制面 Long Task title / next step title 绝对路径脱敏测试；`pytest tests/test_assistant_control_surface.py::test_status_answer_redacts_absolute_paths_from_recent_long_tasks -q` 先失败，暴露 `answer` 泄露 `C:\Users\...\app.py`。
- 2026-05-31，V15 external review follow-up 修复：`_recent_tasks_readonly` 对任务标题和下一步标题进行绝对路径脱敏；阶段文档补齐 `openspec validate --all`、默认 verify 和 diff check 记录，保持 tasks 完成状态有验证证据。
- 2026-05-31，V15 external review follow-up targeted 验证：`pytest tests/test_assistant_control_surface.py::test_status_answer_redacts_absolute_paths_from_recent_long_tasks -q`：1 passed；`pytest tests/test_assistant_control_surface.py tests/test_agent_harness_kernel.py::test_agent_loop_answers_assistant_status_without_repo_rag tests/test_agent_harness_kernel.py::test_agent_loop_memory_command_still_precedes_assistant_status tests/test_agent_harness_kernel.py::test_agent_loop_long_task_command_still_precedes_assistant_status tests/test_chat_api.py::test_chat_endpoint_assistant_status_keeps_contract_and_does_not_create_state -q`：11 passed。
- 2026-05-31，V15 external review follow-up OpenSpec 验证：`openspec validate v15-assistant-control-surface`：通过；`openspec validate --all`：10 passed, 0 failed。
- 2026-05-31，V15 external review follow-up 默认验证：`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 145 passed, 1 skipped；`ruff check .` All checks passed；stage docs drift scan 无漂移。
- 2026-05-31，V15 external review follow-up diff 验证：`git diff --check`：通过，仅有 CRLF 换行提示。
- 2026-05-31，V15 external review close：用户确认外部 review 没问题；final stage debt sweep 已执行，未发现新的 P0/P1/P2 或需记录的阶段内剩余债务。
- 2026-05-31，V15 implementation commit：`86d175a Add V15 assistant control surface`。
- 2026-05-31，V15 archive：`openspec archive v15-assistant-control-surface -y` 已完成，归档到 `openspec/changes/archive/2026-05-31-v15-assistant-control-surface/`；长期 specs 已同步，新增 `openspec/specs/assistant-control-surface/spec.md`。
- 2026-05-31，V15 archive 后 OpenSpec 全量验证：`openspec validate --all`：10 passed, 0 failed。
- 2026-05-31，V15 archive 后默认验证：`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 145 passed, 1 skipped；`ruff check .` All checks passed；stage docs drift scan 无漂移。
- 2026-05-31，V15 archive closeout：`powershell -ExecutionPolicy Bypass -File scripts\check_stage_closeout.ps1`：通过；包含 no active changes、OpenSpec 全量验证、stage docs drift scan 和 `git diff --check`。
- 2026-05-31，V15 archive diff 验证：`git diff --check`：通过，仅有 CRLF 换行提示。
- 2026-05-29，V14 OpenSpec 计划验证：`openspec validate v14-long-task-react-subagents`：通过。
- 2026-05-29，V14 Long Task 小切片 TDD RED：`pytest tests\test_long_task.py tests\test_agent_harness_kernel.py::test_agent_loop_handles_long_task_command_before_router_keyword tests\test_chat_api.py::test_chat_endpoint_long_task_create_keeps_contract_and_does_not_search -q`：预期失败，`ModuleNotFoundError: No module named 'app.longtask'`。
- 2026-05-29，V14 Long Task 目标验证：`pytest tests\test_long_task.py tests\test_agent_harness_kernel.py::test_agent_loop_handles_long_task_command_before_router_keyword tests\test_agent_harness_kernel.py::test_agent_loop_resumes_one_long_task_step_through_repo_rag tests\test_agent_harness_kernel.py::test_agent_loop_blocks_long_task_when_resume_has_no_results tests\test_chat_api.py::test_chat_endpoint_long_task_create_keeps_contract_and_does_not_search tests\test_chat_api.py::test_chat_endpoint_long_task_resume_returns_repo_rag_tool_call -q`：9 passed。
- 2026-05-29，V14 Long Task / AgentLoop / API 相关验证：`pytest tests\test_long_task.py tests\test_agent_harness_kernel.py tests\test_chat_api.py -q`：60 passed。
- 2026-05-29，V14 self-review follow-up：补充直接 `task_id` 访问的 `user_id + repo_key` 隔离，避免跨用户查看任务；`pytest tests\test_long_task.py::test_manager_rejects_cross_user_task_id_access -q` 先失败后修复。
- 2026-05-29，V14 follow-up 相关验证：`pytest tests\test_long_task.py::test_manager_rejects_cross_user_task_id_access tests\test_long_task.py tests\test_agent_harness_kernel.py tests\test_chat_api.py -q`：62 passed。
- 2026-05-30，V14 review follow-up RED：新增 completion 阶段跨用户隔离与 provider JSON planning schema 测试；`pytest tests\test_long_task.py::test_planner_sends_json_schema_prompt_for_provider_enhancement tests\test_long_task.py::test_manager_rejects_cross_user_tool_completion -q`：预期失败，分别表现为 `deterministic_fallback` 和缺少 `user_id` 参数。
- 2026-05-30，V14 review follow-up 修复：`complete_tool_action` 增加 `user_id + repo_key` 作用域校验；provider planning prompt 明确 JSON-only schema 和不可改变 step/action 边界。
- 2026-05-30，V14 review follow-up 验证：`pytest tests\test_long_task.py::test_planner_sends_json_schema_prompt_for_provider_enhancement tests\test_long_task.py::test_manager_rejects_cross_user_tool_completion -q`：2 passed。
- 2026-05-30，V14 review follow-up 相关验证：`pytest tests\test_long_task.py tests\test_agent_harness_kernel.py tests\test_chat_api.py -q`：63 passed。
- 2026-05-30，V14 review follow-up lint：`ruff check app\longtask app\harness\kernel.py tests\test_long_task.py tests\test_agent_harness_kernel.py tests\test_chat_api.py`：All checks passed。
- 2026-05-30，V14 OpenSpec change 验证：`openspec validate v14-long-task-react-subagents`：通过。
- 2026-05-30，V14 diff 验证：`git diff --check`：通过，仅有 CRLF 换行提示。
- 2026-05-30，V14 review follow-up 默认验证：`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 132 passed, 1 skipped；`ruff check .` All checks passed；stage docs drift scan 无漂移。
- 2026-05-30，V14 review follow-up OpenSpec 全量验证：`openspec validate --all`：9 passed, 0 failed。
- 2026-05-30，V14 external review triage：修复 Memory/Long Task 前置顺序、Long Task result summary 绝对路径脱敏，并清理 `app/longtask/__pycache__` 生成物；新增 targeted tests 先失败后修复。
- 2026-05-30，V14 external review targeted 验证：`pytest tests\test_agent_harness_kernel.py::test_agent_loop_handles_memory_command_before_router_and_long_task tests\test_agent_harness_kernel.py::test_agent_loop_memory_command_confirms_without_repo_rag tests\test_long_task.py::test_manager_tool_completion_summary_redacts_absolute_paths -q`：3 passed。
- 2026-05-30，V14 external review 相关验证：`pytest tests\test_long_task.py tests\test_agent_harness_kernel.py tests\test_chat_api.py -q`：65 passed。
- 2026-05-30，V14 external review lint：`ruff check app\longtask app\harness\kernel.py tests\test_long_task.py tests\test_agent_harness_kernel.py tests\test_chat_api.py`：All checks passed。
- 2026-05-30，V14 external review OpenSpec 验证：`openspec validate v14-long-task-react-subagents` 通过；`openspec validate --all`：9 passed, 0 failed。
- 2026-05-30，V14 external review 默认验证：`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 134 passed, 1 skipped；`ruff check .` All checks passed；stage docs drift scan 无漂移。
- 2026-05-30，V14 external review close：外部 review 确认无新增 P0/P1/P2；剩余 P3 `app/longtask/__pycache__` 已复核，文件系统和 git tracked files 均无 pyc。
- 2026-05-30，V14 implementation commit：`ed48fa9 Add V14 long task control plane`。
- 2026-05-30，V14 merge/push：`feature/v14-long-task-react-subagents` 已 fast-forward 合并到 `main` 并推送到 `agentic-codeops/main`。
- 2026-05-30，V14 archive：`openspec archive v14-long-task-react-subagents -y` 已完成，归档到 `openspec/changes/archive/2026-05-30-v14-long-task-react-subagents/`；长期 specs 已同步，新增 `openspec/specs/long-task-agent-execution/spec.md`。
- 2026-05-30，V14 archive 后 OpenSpec 全量验证：`openspec validate --all`：9 passed, 0 failed。
- 2026-05-30，V14 archive 后默认验证：`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 134 passed, 1 skipped；`ruff check .` All checks passed；stage docs drift scan 无漂移。
- 2026-05-30，V14 archive closeout：`powershell -ExecutionPolicy Bypass -File scripts\check_stage_closeout.ps1`：通过；包含 no active changes、OpenSpec 全量验证、stage docs drift scan 和 `git diff --check`。
- 2026-05-30，V14 archive diff 验证：`git diff --check`：通过，仅有 CRLF 换行提示。
- 2026-05-29，V14 OpenSpec 全量验证：`openspec validate --all`：9 passed, 0 failed。
- 2026-05-29，V14 局部 lint：`ruff check app\longtask app\harness\kernel.py tests\test_long_task.py tests\test_agent_harness_kernel.py tests\test_chat_api.py`：All checks passed。
- 2026-05-29，V14 默认验证：`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 130 passed, 1 skipped；`ruff check .` All checks passed；stage docs drift scan 无漂移。
- 2026-05-29，V14 diff 验证：`git diff --check`：通过，仅有 CRLF 换行提示。
- 2026-05-28，V13 OpenSpec 计划验证：`openspec validate v13-memory`：通过。
- 2026-05-28，V13 memory 单元验证：`pytest tests\test_memory.py -q`：5 passed。
- 2026-05-28，V13 memory/AgentLoop/API 小切片验证：`pytest tests\test_memory.py tests\test_agent_harness_kernel.py tests\test_chat_api.py -q`：57 passed。
- 2026-05-28，V13 全量 OpenSpec 验证：`openspec validate --all`：9 passed, 0 failed。
- 2026-05-28，V13 默认验证：`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 120 passed, 1 skipped；`ruff check .` All checks passed；stage docs drift scan 无漂移。
- 2026-05-28，V13 diff 验证：`git diff --check`：通过，仅有 CRLF 换行提示。
- 2026-05-28，V13 implementation commit：`1b5696d Add V13 memory`。
- 2026-05-28，V13 archive：`openspec archive v13-memory --skip-specs -y` 已完成，归档到 `openspec/changes/archive/2026-05-28-v13-memory/`；长期 specs 已在 archive 前同步。
- 2026-05-28，V13 archive 后 OpenSpec 验证：`openspec list` 显示 No active changes found；`openspec validate --all`：8 passed, 0 failed。
- 2026-05-28，V13 archive closeout 验证：`powershell -ExecutionPolicy Bypass -File scripts/check_stage_closeout.ps1`：通过；包含 no active changes、OpenSpec 全量验证、stage docs drift scan 和 `git diff --check`。
- 2026-05-28，V13 archive 后默认验证：`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 120 passed, 1 skipped；`ruff check .` All checks passed；stage docs drift scan 无漂移。
- 2026-05-27，V12 OpenSpec 计划验证：`openspec validate v12-query-rewrite-rerank`：通过。
- 2026-05-27，V12 rewrite/rerank 目标验证：`pytest tests/test_query_rewrite.py tests/test_repo_rerank.py tests/test_agent_harness_kernel.py -q`：41 passed。
- 2026-05-27，V12 相关链路验证：`pytest tests/test_query_rewrite.py tests/test_repo_rerank.py tests/test_repo_rag.py tests/test_agent_harness_kernel.py tests/test_chat_api.py tests/test_evidence_pack.py tests/test_grounded_answer.py -q`：72 passed。
- 2026-05-27，V12 全量 OpenSpec 验证：`openspec validate --all`：8 passed, 0 failed。
- 2026-05-27，V12 默认验证：`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 104 passed, 1 skipped；`ruff check .` All checks passed；stage docs drift scan 无漂移。
- 2026-05-27，V12 diff 验证：`git diff --check`：通过，仅有 CRLF 换行提示。
- 2026-05-27，V12 外部 review follow-up：修正 original variant 为空时跳过 rewrite-only variants 的召回问题；variant 去重改为按 `query_text`、`keywords`、`symbols`、`path_hints` 分字段归一化；symbol/path 查询加入 lexical anchor，避免 rewrite 模板词产生 embedding-only 误召回。
- 2026-05-27，V12 follow-up 目标验证：`pytest tests/test_chat_api.py::test_chat_endpoint_returns_empty_related_files_when_keyword_is_missing tests/test_repo_rag.py tests/test_query_rewrite.py tests/test_tool_executor.py tests/test_repo_rerank.py -q`：19 passed。
- 2026-05-27，V12 follow-up OpenSpec 验证：`openspec validate v12-query-rewrite-rerank`：通过；`openspec validate --all`：8 passed, 0 failed。
- 2026-05-27，V12 follow-up 默认验证：`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 108 passed, 1 skipped；`ruff check .` All checks passed；stage docs drift scan 无漂移。
- 2026-05-27，V12 implementation commit：`aaddad2 Add V12 query rewrite rerank`。
- 2026-05-27，V12 follow-up commit：`4553b11 Fix V12 review follow-ups`。
- 2026-05-27，V12 archive：`openspec archive v12-query-rewrite-rerank --skip-specs -y` 已完成，归档到 `openspec/changes/archive/2026-05-27-v12-query-rewrite-rerank/`；长期 specs 已在 archive 前同步。
- 2026-05-28，V12 archive 后 OpenSpec 验证：`openspec list` 显示 No active changes found；`openspec validate --all`：7 passed, 0 failed。
- 2026-05-28，V12 archive closeout 验证：`powershell -ExecutionPolicy Bypass -File scripts/check_stage_closeout.ps1`：通过；包含 no active changes、OpenSpec 全量验证、stage docs drift scan 和 `git diff --check`。
- 2026-05-28，V12 archive 后默认验证：`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 108 passed, 1 skipped；`ruff check .` All checks passed；stage docs drift scan 无漂移。
- 2026-05-26，V11 OpenSpec 计划验证：`openspec validate v11-grounded-answer-model-provider-boundary`：通过。
- 2026-05-26，V11 provider / grounded answer 小切片验证：`pytest tests\test_model_provider.py tests\test_grounded_answer.py tests\test_agent_harness_kernel.py tests\test_chat_api.py`：54 passed。
- 2026-05-26，V11 dependency 变更：`httpx>=0.27.0` 已从 dev dependency 提升为 `[project].dependencies` 运行时依赖，用于可选 OpenAI-compatible provider；默认验证仍不调用真实网络。
- 2026-05-26，V11 全量 OpenSpec 验证：`openspec validate --all`：8 passed, 0 failed。
- 2026-05-26，V11 默认验证：`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 96 passed, 1 skipped；`ruff check .` All checks passed。
- 2026-05-26，V11 外部 review follow-up：确认 `httpx>=0.27.0` 已在 `[project].dependencies`，并补充 PROGRESS 依赖记录；修正 citation 校验 allowed 集合，使其只接受实际传给 provider 的 included 且非空 snippet evidence；`pytest tests\test_grounded_answer.py`：9 passed。
- 2026-05-26，V11 外部 review follow-up 验证：`openspec validate --all`：8 passed, 0 failed；`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 97 passed, 1 skipped；`ruff check .` All checks passed；`git diff --check`：通过，仅有 CRLF 换行提示。
- 2026-05-26，V11 diff 验证：`git diff --check`：通过，仅有 CRLF 换行提示。
- 2026-05-26，V11 review 前新增设计观察：RepoPilot 采用 grep-first, RAG-assisted 检索立场；V11 Grounded Answer 应优先基于可审计的 deterministic lexical/path/symbol evidence，V12 Query Rewrite / Rerank 应服务于该基线，不默认转向重型向量库或 embedding cache。
- 2026-05-26，V11 archive：`openspec archive v11-grounded-answer-model-provider-boundary --skip-specs -y` 已完成，归档到 `openspec/changes/archive/2026-05-26-v11-grounded-answer-model-provider-boundary/`；长期 specs 已在 archive 前同步。
- 2026-05-26，V11 archive 后验证：`openspec validate --all`：7 passed, 0 failed；`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 97 passed, 1 skipped；`ruff check .` All checks passed；`git diff --check`：通过，仅有 CRLF 换行提示。
- 2026-05-26，V12 前 harness 流程瘦身：新增 `scripts/check_stage_docs.ps1` 阶段文档漂移扫描、`scripts/check_stage_closeout.ps1` 归档收口检查、`.harness/templates/stage_closeout.md` closeout 模板和 `.harness/templates/stage_planning.md` 规划模板，并将 drift scan 接入 `scripts/verify.ps1`。

- 2026-05-25，V10 Evidence Pack + Context Budget 实现验证：`openspec validate v10-evidence-pack-context-budget`：通过。
- 2026-05-25，V10 Evidence Pack + Context Budget 实现验证：`pytest tests\test_evidence_pack.py tests\test_agent_harness_kernel.py tests\test_chat_api.py`：40 passed。
- 2026-05-25，V10 Evidence Pack + Context Budget 实现验证：`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 75 passed, 1 skipped；`ruff check .` All checks passed。
- 2026-05-25，V10 Evidence Pack + Context Budget 实现验证：`git diff --check`：通过，仅有 CRLF 换行提示。
- 2026-05-25，V10 review follow-up 验证：`pytest tests\test_chat_api.py`：9 passed。
- 2026-05-25，V10 review follow-up 验证：`openspec validate --all`：7 passed, 0 failed。
- 2026-05-25，V10 review follow-up 验证：`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 76 passed, 1 skipped；`ruff check .` All checks passed。
- 2026-05-25，V10 review follow-up 验证：`git diff --check`：通过，仅有 CRLF 换行提示。
- 2026-05-25，V10 计划债务扫描修复验证：`pytest tests\test_agent_harness_kernel.py tests\test_chat_api.py tests\test_evidence_pack.py`：42 passed。
- 2026-05-25，V10 计划债务扫描修复验证：`openspec validate v10-evidence-pack-context-budget`：通过。
- 2026-05-25，V10 计划债务扫描修复验证：`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 77 passed, 1 skipped；`ruff check .` All checks passed。
- 2026-05-25，V10 计划债务扫描修复验证：`git diff --check`：通过，仅有 CRLF 换行提示。
- 2026-05-25，非 V10 历史代码债修复验证：`pytest tests\test_repo_rag.py tests\test_agent_harness_kernel.py tests\test_chat_api.py`：50 passed。
- 2026-05-25，非 V10 历史代码债修复验证：`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 81 passed, 1 skipped；`ruff check .` All checks passed。
- 2026-05-25，非 V10 历史代码债修复验证：`openspec validate --all`：7 passed, 0 failed；`git diff --check`：通过，仅有 CRLF 换行提示。
- 2026-05-25，V9 文档漂移修正 / V10 plan 历史验证：`openspec validate --all`：7 passed, 0 failed
- 2026-05-25，V9 文档漂移修正 / V10 plan 历史验证：`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 67 passed, 1 skipped；`ruff check .` All checks passed
- 2026-05-25，V9 文档漂移修正 / V10 plan 历史验证：`git diff --check`：通过，仅有 CRLF 换行提示
- 2026-05-26，V10 implementation self-review：未发现 P0/P1 阻塞；P2 文档历史措辞债已修正。
- 2026-05-26，V10 外部 review：用户反馈外部 review 显示没问题，无阻塞发现。
- 2026-05-26，V10 外部 review 后 full verify：`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 81 passed, 1 skipped；`ruff check .` All checks passed。
- 2026-05-26，V10 archive 前长期 spec 同步验证：`openspec validate --all`：7 passed, 0 failed。
- 2026-05-26，V10 archive 后验证：`openspec validate --all`：6 passed, 0 failed；`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 81 passed, 1 skipped；`ruff check .` All checks passed；`git diff --check`：通过，仅有 CRLF 换行提示。
- 2026-05-12：`powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`：通过
- `pytest`：24 passed
- `ruff check .`：All checks passed
- 2026-05-12：`openspec validate retire-legacy-specs`：通过
- 2026-05-12：`openspec validate --all`：5 passed
- 2026-05-12：`git diff --check`：通过，仅有 CRLF 换行提示
- 2026-05-12，V5 实现验证：`powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`：通过
- 2026-05-12，V5 实现验证：`pytest`：30 passed, 1 skipped
- 2026-05-12，V5 实现验证：`ruff check .`：All checks passed
- 2026-05-12，V5 归档验证：`openspec validate --all`：通过
- 2026-05-17，V6 规格验证：`openspec validate v6-skill-aware-agent-loop`：通过
- 2026-05-17，V6 实现验证：`pytest tests/test_chat_api.py`：8 passed
- 2026-05-17，V6 全量验证：`powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`：通过
- 2026-05-17，V6 全量验证：`pytest`：32 passed, 1 skipped
- 2026-05-17，V6 全量验证：`ruff check .`：All checks passed
- 2026-05-17，V6 diff 验证：`git diff --check`：通过，仅有 CRLF 换行提示
- 2026-05-18，V6 Kernel plan 验证：`openspec validate v6-agent-harness-kernel`：通过
- 2026-05-18，V6 Kernel 小切片验证：`pytest tests/test_agent_harness_kernel.py`：9 passed
- 2026-05-18，V6 `/chat` 回归验证：`pytest tests/test_chat_api.py`：6 passed
- 2026-05-18，V6 局部 lint：`ruff check app/harness app/agents/code_agent.py tests/test_agent_harness_kernel.py`：All checks passed
- 2026-05-18，V6 全量验证：`powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`：通过；`pytest` 39 passed, 1 skipped；`ruff check .` All checks passed
- 2026-05-18，V6 diff 验证：`git diff --check`：通过，仅有 CRLF 换行提示
- 2026-05-18，V6 最终全量验证：`powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`：通过；`pytest` 42 passed, 1 skipped；`ruff check .` All checks passed
- 2026-05-18，V6 归档验证：`openspec validate --all`：5 passed
- 2026-05-19，V7 规格验证：`openspec validate v7-permission-approval-gate`：通过
- 2026-05-19，V7 Kernel 验证：`pytest tests/test_agent_harness_kernel.py`：16 passed
- 2026-05-19，V7 `/chat` 回归验证：`pytest tests/test_chat_api.py`：6 passed
- 2026-05-19，V7 全量验证：`powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`：通过；`pytest` 46 passed, 1 skipped；`ruff check .` All checks passed
- 2026-05-19，V7 diff 验证：`git diff --check`：通过，仅有 CRLF 换行提示
- 2026-05-19，V7 归档验证：`openspec validate --all`：通过

## OpenSpec 项目级工作流

- 新增项目内 OpenSpec 目录说明：
  - `openspec/README.md`
  - `openspec/changes/README.md`
  - `openspec/changes/archive/README.md`
  - `openspec/specs/README.md`
- 保留项目内 `.codex/skills`，用于 Codex 在本仓库理解 OpenSpec 工作流。
- 保留项目内 `.opencode`，用于 OpenCode OpenSpec commands 和 skills。
- 不保留 `.github` OpenSpec prompts/skills；Copilot 对接不通过仓库内 `.github` 生成物维护。
- 不安装 Codex 全局 prompts，不要求写入 `C:\Users\...\ .codex\prompts`。
- OpenSpec 只作为本仓库开发流程，不是 RepoPilot runtime 功能。
- 不因为 OpenSpec 接入而引入 MCP server、plugin runtime、skill 执行、动态工具注册或 `/chat` 决策变更。

## Legacy Specs OpenSpec 迁移与归档

- 新增 OpenSpec change：`migrate-legacy-specs-to-openspec`。
- 迁移规划目标是把 legacy `specs/00x-*` 的已验收 V1-V4 行为映射为长期 OpenSpec capabilities。
- 已归档 `migrate-legacy-specs-to-openspec`，并生成长期 `openspec/specs/`。
- 旧 `specs/00x-*` 已退役并删除；历史迁移记录保留在 `openspec/changes/archive/2026-05-11-migrate-legacy-specs-to-openspec/`。
- 已归档 `retire-legacy-specs` 到 `openspec/changes/archive/2026-05-12-retire-legacy-specs/`，并在 `harness-development-workflow` 记录 `openspec/specs/` 是长期规格入口。
- `openspec/specs/<capability>/` 作为长期规格入口仅保留当前 capability 的 `spec.md`；活跃 change 的 `proposal.md`、`design.md`、`tasks.md` 和 spec delta 保留在 `openspec/changes/<change-name>/`，归档后再进入 `openspec/changes/archive/`。
- OpenSpec 正文优先使用中文；capability 目录名、命令、函数名和字段名保持英文工程约定；规范句保留 `SHALL` / `MUST` / `MUST NOT` 关键词以通过 OpenSpec 校验。
- 新增 capabilities：
  - `chat-api`
  - `safe-repository-file-tools`
  - `agent-loop-tool-execution`
  - `skill-metadata-loader`
  - `harness-development-workflow`
- `openspec validate migrate-legacy-specs-to-openspec`：通过。
- `openspec list`：No active changes found。
- `openspec list --specs`：显示 5 个 capabilities。

## V4：Skill Metadata Loader

- V4 legacy specs 已迁移到 `openspec/specs/skill-metadata-loader/spec.md`。
- 新增 `app/tools/skill_loader.py`，发现 `.agents/skills/*/SKILL.md`，解析 `name`、`description` 和相对仓库 `path`。
- 新增 `tests/test_skill_loader.py`，覆盖 metadata 命中、无 skills 目录、多技能稳定排序、不返回完整正文、不泄露本机绝对路径、缺失 metadata、非法 frontmatter 行和异常 frontmatter 读取限制。
- V4 不执行 skill，不读取完整 skill 正文，不做 progressive disclosure，不接入 `/chat` 决策。
- V4 当前对坏 `SKILL.md` 采用 fail fast 策略；后续有日志、trace audit 或 skill audit 后，可调整为记录日志并跳过坏 skill。
- V4 仍不接真实 LLM、不自动修改代码、不执行 shell、不做 RAG、Memory、Reflection、eval 或复杂多 Agent。

## V5：Skill Content Loader / progressive disclosure

- V5 开发分支：`feature/v5-skill-content-loader`。
- 已创建 OpenSpec change：`openspec/changes/v5-skill-content-loader/`。
- 已完成 OpenSpec artifacts：`proposal.md`、`design.md`、`specs/skill-metadata-loader/spec.md`、`tasks.md`。
- 已实现 `load_skill_content(repo_path, skill_path)`，在 metadata-first 之后按需读取完整 `SKILL.md`。
- Content Loader 返回 `{"path": "...", "content": "..."}`。
- Content Loader 只允许读取 `.agents/skills/<skill>/SKILL.md`，拒绝路径逃逸、非 skill 文件、缺失文件和符号链接目录绕过。
- Content Loader 有明确内容读取上限，超限 fail fast。
- Content Loader 不解析 frontmatter，不验证 `name` / `description`。
- V5 仍不接入 `/chat` 决策，不执行 skill，不接真实 LLM，不自动把 skill 内容注入 prompt。
- 已同步本阶段 `.harness/allowed_files.md` 和 `.harness/review_checklist.md`。
- `docs/FEATURE_LIST.json` 中 V5 条目已标记 `passes: true`。
- 已归档 `v5-skill-content-loader` 到 `openspec/changes/archive/2026-05-12-v5-skill-content-loader/`，并同步长期规格 `openspec/specs/skill-metadata-loader/spec.md`。

## V6：Agent Harness Kernel + Router Kernel（已提交并归档）

- V6 开发分支：`feature/v6-agent-harness-kernel`。
- 已提交：`b1d6b03 Add V6 agent harness kernel`。
- 已归档 OpenSpec change：`openspec/changes/archive/2026-05-18-v6-agent-harness-kernel/`。
- 用户当时已接受 V6 阶段实现；V6 阶段结束时暂无活跃 OpenSpec change。
- V6 阶段主线已从 `v6-skill-aware-agent-loop` 切换为 Agent Harness Kernel + Router Kernel。
- `v6-skill-aware-agent-loop` 是历史 draft/流程偏差记录，不作为当前阶段主线，不应继续作为实现入口；其空 active change 目录已清理。
- 当前小切片已建立四个最小运行时骨架：
  - `RequestRouter`：对输入请求做确定性路由，先只支持现有仓库搜索路径。
  - `ToolRegistry`：登记只读低风险工具元数据，并在调用前校验工具存在、只读和风险等级；不负责 dispatch。
  - `AgentLoop`：包装现有确定性搜索闭环，不引入真实 LLM 或复杂规划。
  - `TraceEvent`：记录最小结构化事件，支撑后续审计。
- 已固化最小 contract：`AgentLoopRequest`、`RouteDecision`、`ToolSpec`、`TraceEvent`、内部 `AgentLoopResult`。
- V6 不实现 `ProviderAdapter`、`ContextBuilder`、`SkillRegistry`、`SessionStore` 运行时代码；这些只作为后续阶段扩展方向。
- V6 不接 RAG、Memory、Reflection、eval、PermissionPolicy、ApprovalGate、SandboxRunner、subagents、长期任务或真实 LLM。

## V7：Permission + Approval Gate（已提交并归档）

- 已提交：`7f1fc86 Add V7 permission approval gate`。
- 已合并到 `main`：`Merge V7 permission approval gate`。
- 已归档 OpenSpec change：`openspec/changes/archive/2026-05-19-v7-permission-approval-gate/`。
- 已同步 V7 阶段 harness：
  - `.harness/allowed_files.md`
  - `.harness/review_checklist.md`
- 已实现最小运行时边界：
  - `ToolSpec.requires_approval`：标记低风险只读工具是否需要审批。
  - `PermissionDecision`：记录工具名、权限状态和稳定原因。
  - `PermissionPolicy`：唯一产出 `allow`、`deny`、`ask` 的权限状态。
  - `ApprovalGate`：消费权限结果；遇到 `ask` 阻止工具执行，不做真实交互审批。
- `ToolRegistry` 在 V7 只登记和读取 `ToolSpec`，不保留独立 allow/deny gate；权限状态和拒绝原因统一由 `PermissionPolicy` 产出。
- 权限优先级固定为：未注册、非只读或非 `low` 风险 -> `deny`；否则 `requires_approval=True` -> `ask`；否则 -> `allow`。
- `deny` 和 `ask` 分支不调用 executor，`related_files=[]` 且 `tool_calls=[]`。
- `related_files` 只返回相对仓库路径；若上游异常返回本机绝对路径，Kernel 会跳过该路径。
- 权限和审批审计仅记录在内部 `trace_events_internal`，不通过 `/chat` 暴露。
- `chat_only` 不进入 permission/approval 链路，不记录 `permission_checked`。
- V7 不实现真实审批 UI、审批持久化、写文件工具、shell 工具、SandboxRunner、LLM、RAG、Memory、Reflection、skill execution、eval 或复杂多 Agent。

## 当前注意事项

- V2 工具只读，不写文件、不删文件、不执行 shell。
- V3 只做最小确定性关键词提取，测试使用 `UNIQUE_BUG_TOKEN`。
- 当前链路通过 `ToolExecutor(repo_rag)` 调用只读 hybrid repo RAG；V9 会读取安全文件工具允许访问的仓库文本文件小段 chunk，但不返回完整文件内容。
- 当前不接真实 LLM、不自动修改代码、不执行 shell、不做 Reflection、eval、真实外部 embedding 服务、外部向量库、向量 Memory、自动 memory 总结或复杂多 Agent；V16 仅允许用户明确确认后的受控 patch apply。
- `PermissionPolicy`、最小 `ApprovalGate` 和 V19 脱敏持久审计摘要已实现；真实审批流程、SandboxRunner、完整 raw trace replay、Skill 执行、eval 和 Reflection 仍是 Roadmap，不能写成已实现。
- 后续接入真实审批、沙箱或高风险工具时，应通过当前权限/审批边界和 `ToolExecutor` 增量加入。
- 缓存文件已从 git 跟踪中移除，并由 `.gitignore` 忽略。
- V14 Memory command 与 Long Task 控制命令必须在 `RequestRouter` / keyword 路由前处理，顺序为 Memory command 先识别、Long Task command 后识别；除显式 resume/run 当前 step 外，不得调用 `repo_rag`。
- V14 Long Task 只写 repo-local `.repopilot/tasks.sqlite3`；不得修改被分析仓库代码文件。
- V14 只预留 subagent/worktree handoff metadata；不得执行真实 subagent 调度、后台任务、git branch/worktree 操作、shell 或自动代码修改。

## 已知剩余代码债

- `app/worktrees/inspection.py`：V21 流式 hunk count / preview 仍使用直接 `Popen` 并在流消费后
  无 timeout 等待；恶意或异常 Git 进程可能让只读 inspection 长时间挂起。应在独立 hardening
  阶段设计可中止的 bounded streaming runner，并保持 preview 限长与脱敏语义。
- `app/worktrees/manager.py`：V20 create、workspace preflight 与 rollback 的 Git subprocess
  尚无独立 timeout，capture output 也无读取前硬上限。应在独立 worktree-create hardening
  阶段统一固定 argv、timeout、bounded output 与失败/rollback 语义。
- `app/rag/evidence.py`：空 `snippet` 当前会被计为 `included=True` 且预算消耗为 `0`。真实 retriever 通常不会产空 chunk，但后续可改为空 snippet 直接 omitted 或跳过，以让 audit summary 更清晰。
- `app/harness/kernel.py`：capability-status 识别仍是字符串规则集合；当前已支持中英文常见问法并独立 route，后续能力项增多时可抽成小型 capability classifier。
- `app/rag/repo_rag.py`：hybrid fusion 的权重和 `min_fused_score` 仍是硬编码常量；当前 symbol/path 查询已要求 lexical anchor，后续如需更细粒度召回策略或审计，应把权重、阈值和 anchor 策略显式参数化。
- tests：仍有少量历史阶段命名测试保留，用于表达旧阶段边界；后续做测试命名清理时可统一改成阶段无关的 repo_rag / hybrid_repo_rag 命名。
- V15 Assistant Control Surface 触发词当前保持小而明确；后续如要支持更自然的状态问法，应单独扩展 parser，避免误吞 capability-status 或 repo_search 问题。

## 下一步建议

下一步建议：

- 长期规格入口已切换为 `openspec/specs/`。
- 后续新阶段继续使用 OpenSpec change；不要恢复旧 `specs/00x-*` 作为规格入口。
- 当前建议：V23 已完成 implementation、review remediation、archive 与 merge；开始下一阶段前先按
  OpenSpec stage planning 流程重新同步 harness 边界。
- 近期路线：V21 inspection、V22 re-verification 与 V23 disposal/reconciliation 已完成；
  下一阶段推荐规划 V24 verified promotion。
- V24 完成后重新评估 Operator Control、Durable Execution、Background Worker、
  subagents、connectors、notifications、heartbeat/cron 和 always-on assistant；
  不要写成当前 runtime 已实现能力，也不要提前锁定公开 API。
- 继续保持不执行 skill，除非后续阶段明确开放。

## V8：Query Understanding + Lexical Repo RAG（已实现）

- V8 合并后基线：`main`（V8 已由 `codex/v8-query-understanding-repo-rag` 合并进入）
- OpenSpec change：已归档到 `openspec/changes/archive/2026-05-20-v8-query-understanding-repo-rag/`
- V8 将旧路线里的“大 Repo RAG Engineering”收窄为 deterministic query understanding + 非向量化 lexical repo RAG。
- 已新增 `app/rag/query_understanding.py`，生成 `SearchPlan`，识别代码定位、实现解释、调用关系、测试/验证、文件摘要和未知泛问。
- 已新增 `app/rag/repo_rag.py`，提供 repo chunk、lexical scorer、dedup 和 citation。
- `AgentLoop` 已接入 query understanding 和 lexical repo RAG，并继续保留 V7 的 ToolRegistry、PermissionPolicy、ApprovalGate 边界。
- `/chat` contract 保持不变：`trace_id`、`answer`、`related_files`、`tool_calls`。
- V8 明确不实现 embedding、Milvus、Elasticsearch、PgVector、Qdrant、LLM rewrite、rerank、memory 或 context compression。

参考项目已写入 V8 design，只作为后续规划资料，不作为 RepoPilot runtime dependency：`ragent`、`agentic-rag-for-dummies`、`mem0`、`AGI-assistant`、`openai-cs-agents-demo`、`learn-claude-code`、`build-your-own-openclaw`、`agents-from-scratch`、`DeepAgents`、`DeerFlow`、`Clawd-Code`。

## V9：Embedding Retrieval + Hybrid Search（已提交并归档）

- V9 开发分支：`codex/v9-embedding-hybrid-search`
- OpenSpec change：已归档到 `openspec/changes/archive/2026-05-22-v9-embedding-hybrid-search/`
- 已提交：
  - `61a7963 Add V9 embedding hybrid search`
  - `24d4d6e Fix V9 review follow-ups`
  - `d31e83e Document V9 implementation review recovery`
  - `9479a0c Address final V9 review findings`
  - `e5e5fa0 Archive V9 embedding hybrid search`
- 已创建：
  - `proposal.md`
  - `design.md`
  - `specs/repo-query-understanding-rag/spec.md`
  - `tasks.md`
- 已同步 V9 阶段 harness：
  - `.harness/allowed_files.md`
  - `.harness/review_checklist.md`
- 已同步长期 spec：`openspec/specs/repo-query-understanding-rag/spec.md`
- 已验证：归档后 `openspec validate --all` 通过。
- 已实现：
  - `DeterministicEmbeddingProvider`：本地确定性 embedding provider，固定维度、稳定向量格式，不调用外部服务。
  - `EmbeddingRepoRetriever`：复用安全 repo chunk 和 citation 约束执行 embedding retrieval。
  - `HybridRepoRetriever` / `hybrid_fuse`：合并 lexical 与 embedding retrieval，保留路径、文件名、符号和 exact token 命中的优势。
  - `ToolExecutor(repo_rag)` 和 `AgentLoop` 默认使用 `retrieval_mode=hybrid`，但 `/chat` 顶层 contract 不变。
- 局部验证：
  - `pytest tests/test_repo_rag.py`：7 passed
  - `pytest tests/test_query_understanding.py tests/test_agent_harness_kernel.py tests/test_chat_api.py`：33 passed
- 全量验证：
  - `openspec validate --all`：6 passed, 0 failed
  - `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`：通过；`pytest` 67 passed, 1 skipped；`ruff check .` All checks passed
  - `git diff --check`：通过，仅有 CRLF 换行提示

V9 补充 embedding provider 边界、轻量默认实现、repo-local embedding retrieval 和 hybrid fusion，同时保留 V8 lexical repo RAG 作为一等通道。V9 不默认引入 Milvus、Elasticsearch、PgVector、Qdrant、真实外部 embedding 服务或模型下载。

路线重排：V9 为 Embedding Retrieval + Hybrid Search；V10 为 Evidence Pack + Context Budget；V11 为 Grounded Answer / Model Provider Boundary；V12 为 Query Rewrite + Rerank；V13 为 Memory；V14 为 Long Task / ReAct Skeleton；V15 为 Assistant Control Surface；V16 为 Safe Patch Authoring；V17 为 Verification Runner；V18 为 Patch + Verify Loop；V19 为 Persistent Audit / Recovery；V20 为 Worktree Isolation。

说明：V8 archive 中保留的是当时路线记录；后续已由 V9/V10 路线重排 supersede，当前长期 docs/specs 以 V10 Evidence Pack + Context Budget、V11 Grounded Answer / Model Provider Boundary、V12 Query Rewrite + Rerank 为准。

## V10：Evidence Pack + Context Budget（已提交并归档）

- 当前分支：`codex/v10-evidence-pack-context-budget`
- OpenSpec change：已归档到 `openspec/changes/archive/2026-05-26-v10-evidence-pack-context-budget/`
- 已提交：`c5ec1ff Add V10 evidence pack context budget`
- 已创建：
  - `proposal.md`
  - `design.md`
  - `specs/repo-query-understanding-rag/spec.md`
  - `tasks.md`
- 已同步 V10 implementation harness：
  - `.harness/allowed_files.md`
  - `.harness/review_checklist.md`
- 已实现：
  - `app/rag/evidence.py`：Evidence Pack、Evidence item 和 Context Budget 结构。
  - `ToolExecutionResult.evidence_pack`：仅内部持有，不进入 `call_summary()`。
  - `ToolExecutor.search_repo_rag`：在 successful hybrid retrieval 后生成 Evidence Pack。
  - `AgentLoop`：把 Evidence Pack audit summary 记录为内部 trace，不改变 `/chat` contract。
  - tests 覆盖 evidence item shape、预算裁剪、错误/空结果、contract boundary 和路线图旧口径扫描。
- 当前非目标：不实现 grounded answer、model provider、LLM prompt assembly、query rewrite、rerank、memory、context compression、SandboxRunner、skill execution 或多 agent orchestration。
- 当前状态：实现已完成、内部 self-review 和外部 review 均无阻塞发现，并已提交归档。
- 已同步长期 `openspec/specs/repo-query-understanding-rag/spec.md`：补入 V10 Evidence Pack / Context Budget requirements，并修正 `min_fused_score=0.35` 长期规格口径。
- 文档同步补充：已补齐 README 的 V9 阶段历史和路线图状态，修正 ARCHITECTURE 中 V8 当前态措辞，并在 HANDOFF 中补充 V9 完整摘要。
