# 项目进度

本文件顶部只记录可跨 session 复用的 durable status、未清债务和候选顺序。Branch、HEAD、worktree、
active change、candidate、merge/push 与 remote parity 必须通过 live Git/OpenSpec/controller state 查询。
下面的历史详细记录只保存当时证据，不是当前状态来源。

## 当前状态

- RepoPilot 的 V1–V25 runtime capability 已形成长期 OpenSpec specs；当前产品仍定位为本地、可控、
  可审计的 Coding Agent Harness，而不是通用 AI IDE。
- Runtime 主干包括 repo-local hybrid RAG、grounded answer、Memory、Long Task、Assistant Control Surface、
  controlled patch proposal/apply、Verification Runner、persistent audit 和 retained worktree lifecycle。
- 最近完成的 verification baseline 修复与 repository Ruff cleanup 已证明 full pytest、full Ruff、canonical
  `python -I scripts/verify.py`、stage-doc/skill scanners 和 OpenSpec validation 可在同一受控解释器下全绿。
- Stage-change replay 仍是 repository development workflow 中的 dormant、`mechanical_consistency_only`
  接口；缺少 external host CAS/restart/dispatch evidence 时不激活 v2，也不成为 runtime capability。
- OpenSpec、Harness、Codex/OpenCode skills、MCP 和 plugins 仍属于开发流程或外部协作面，不自动成为产品能力。

## 剩余债务

- Documentation drift 仍是持续维护风险：scanner 只证明明确的结构约束，不能替代对 runtime/docs 语义一致性
  的 internal review；新增 capability 或 closeout 流程时必须同步检查 current architecture、acceptance inventory
  和 OpenSpec index ownership。
- `VerificationRunner` 的 process-tree containment 应作为独立安全阶段评估，不与文档或模型 patch authoring 混合。
- Request-supplied `user_id` 和 context-only `ApprovalGate` 不能证明持久化 Operator authority；真实人工 authority
  需要独立设计，不能从当前 repository records 或 runtime context 推导。
- 外部 host CAS、durable/background execution、runtime subagents、connectors、notifications 和产品内自动
  commit/merge/push 均没有进入当前 runtime contract。

## 候选顺序

以下是候选顺序，不表示已经 active 或获准实施；开始任何一项前重新运行 `openspec list` 并冻结新 stage：

1. `enable-opt-in-model-patch-authoring`：仅显式 opt-in 生成 pending patch proposal，默认继续 fake/offline；
   不自动 apply、verify、promote、commit、merge 或 push。
2. `add-pending-patch-inspection-and-rejection`：允许查看、拒绝或继续处理 pending patch。
3. 把既有 worktree lifecycle 暴露为前台 CLI 流程，同时保持当前权限、审计和明确确认边界。
4. 独立评估 VerificationRunner process-tree containment。

暂缓 replay v2 activation、持久化 Operator approval、background/durable/subagent/connectors 扩张，以及产品内
自动 Git delivery。候选之间一次只启动一个 OpenSpec stage。

## 阶段索引

详细 proposal、design、tasks、spec deltas 和当时验证证据以
[`openspec/changes/archive/`](../openspec/changes/archive/) 为准；长期合同以
[`openspec/specs/`](../openspec/specs/) 为准。

| 能力组 | 代表阶段 | 历史入口 |
|---|---|---|
| Agent/API/Tools | V1–V7 基础入口、工具和权限边界 | `2026-05-11-*` 至 `2026-05-19-*` archives |
| Retrieval/Answering | V8–V12 repo RAG、Evidence Pack、provider boundary | `2026-05-20-*` 至 `2026-05-27-*` archives |
| Memory/Long Task/Control | V13–V15 | `2026-05-28-*` 至 `2026-05-31-*` archives |
| Patch/Verify/Audit | V16–V19 | `2026-05-31-*` 至 `2026-06-05-*` archives |
| Worktree lifecycle | V20–V25 | `2026-06-07-*` 至 `2026-06-27-*` archives |
| Workflow authority/replay | authority binding、independent review、stage replay | `2026-08-20-*` 至 `2026-08-21-*` archives |
| Verification baseline | deterministic verification、repository Ruff cleanup | `2026-08-26-*` archives |

<details>
<summary>历史详细记录（只作当时证据，不作为 current guidance）</summary>

## Clear Repository Ruff Baseline（archived，2026-08-26）

- 基于前序本地 candidate `1743eed4694acd585d2a5ef40d090acf56e2969e`，在同一干净 worktree 中清理
  精确的 92 项 / 53 文件 Ruff 基线；未触碰原脏 worktree。
- 仅使用 Ruff safe fixes、最小等价手工修改，以及计划中冻结的 3 处 TRY004 和 14 处既有 boundary BLE001
  精确行级说明（其中一处同线 S110）；没有 unsafe fix、global/per-file ignore 或规则降级。
- 当前证据：canonical `python -I scripts/verify.py` 全绿，full pytest `971 passed`，full Ruff PASS，
  stage-doc/skill-eval scanners PASS；OpenSpec active strict PASS、all `25 passed, 0 failed`；
  `git diff --check` PASS。
- OpenSpec change 已归档到 `openspec/changes/archive/2026-08-26-clear-repository-ruff-baseline/`，长期
  `verification-runner` spec 同步 1 项 modified。当前只剩最终两席 post-archive implementation review、
  第二个 finite candidate，以及 controller 的
  fast-forward/exact-lease push closeout；这些步骤尚未完成。

## Restore Deterministic Verification Baseline（archived，pre-candidate，2026-08-26）

- OpenSpec change `restore-deterministic-verification-baseline` 已归档到
  `openspec/changes/archive/2026-08-26-restore-deterministic-verification-baseline/`；仅在干净 worktree
  `/private/tmp/agentic-codeops-restore-verification.01a03bfc` 开发，不触碰原脏 worktree。
- 当前小阶段修复三项可复现 pytest 问题：JSON object mode 对超过 128 层 structural container fail closed；
  Verification Runner 和相关测试固定使用当前 `sys.executable -I`；pytest/Ruff 缺失或 probe 异常明确失败。
- 新的 `scripts/verify.py` 是 canonical cross-platform 入口；PowerShell scripts 只做薄委托，缺工具不得跳过。
- 当前证据：full pytest `971 passed`，changed-file Ruff PASS；full Ruff 已重测为 92 项 / 53 文件。
  当前小阶段只清理 changed-file Ruff，随后 `clear-repository-ruff-baseline` 机械阶段清理 residual inventory，
  不加全局 ignore。
- Canonical `python -I scripts/verify.py` 已证明先完成 967 项 pytest，再在 residual Ruff 处非零停止；
  remediation 后 full pytest 已独立重跑为 `971 passed`；
  required Ruff 没有被跳过。两个 Python scanners、OpenSpec change strict、archive 后 all non-strict 与
  `git diff --check` 均通过。
- Pre-archive implementation review 的 A/B 两席在首轮发现的 spec sync、PowerShell fail-closed、scanner parity
  与 canonical success-path tests 问题均经原 same-slot remediation re-review 关闭；共同 packet
  `0b5d2a0616605f54bc20af15ffb40e13365c5f87675ed622d39bfe939a53995a` 为 READY / NO_FINDINGS。
  Archive gate 随后 PASS，并完成 2 个 requirement added、3 个 modified 的 durable spec sync；post-archive
  final packet/reviewer refresh 与 local candidate 尚未完成。
- 两阶段的 full pytest、full Ruff、canonical verification 与 scanners 全绿后，才能按授权执行 reviewed
  commits、fast-forward merge 和 exact-old-OID lease push。

## Stage Change Replay（archived，2026-08-21）

- OpenSpec change `add-stage-change-replay` 已归档到
  `openspec/changes/archive/2026-08-21-add-stage-change-replay/`；风险为 high / L3，属于 process-only
  repository development workflow change。未修改 `app/**`、公开 API、provider/persistence runtime、依赖、
  网络默认值、runtime subagent 或产品级 Git automation。
- 新增长期 `stage-change-replay` capability，并同步 `stage-authority-binding` 与
  `harness-development-workflow`：V1 使用 code-owned 线性 graph、exact fact-to-suffix/prefix/frontier、
  canonical event/receipt lineage、append CAS、workspace/Git identity 与逐级 symlink 边界；历史 receipt、
  authority/event delta 和 gate evidence 均按当前 graph 重算。
- Repo-local replay/v2 固定为 `mechanical_consistency_only` 和
  `blocked_on_external_host_capability`。Caller-supplied 11-gate adapter、terminal state 或 repository fixture
  不能证明 native producer、host dispatch、activation、push reconciliation 或 action readiness；当前任何 action
  均 `requested_action_ready=false`。后续若要激活，必须另起阶段接入并审查
  `provider_neutral.stage_state_cas/v1`、restart/CAS、native attestation 与 activation chronology。
- Authority 仍由 pre-change v1 流程管理到 terminal；later-v1 epoch 2 线性绑定 direct-user 批准的 exact scope、
  push ceiling、origin/main、endpoint fingerprint 与 authorized old tip。Repo authority record/hash/validator 不能
  自证用户身份、消息真实性或授权时序。
- Final implementation review 的 A/B 两席在 packet `8e1452cd…49d6a9` 上发现的 P1/P2，以及 remediation 中
  新发现的 adapter/unknown-push bypass，均经原 same-slot re-review 关闭；最终共同 packet
  `7eccf12cf3b8793c52a7e5146ffe6698746f69b19d212f0b0d272aebcf636500` 为 READY / NO_FINDINGS，最终
  candidate/pushed commit 为 `2c0d0d4e749e16e43d867931c58c6a82be56cf13`。
- 验证 evidence：focused replay/authority `363 passed`；changed Python Ruff、`py_compile` 与
  `git diff --check` PASS；OpenSpec active strict PASS，archive 后 `openspec list` 为 No active changes found，
  `openspec validate --all` 为 `24 passed, 0 failed`。Full pytest 为 `916 passed, 3 failed`；3 项是既有
  baseline（model-provider recursion-depth 1 项、当前 shell 无 `python` 命令导致 verification-runner 2 项）。
  Full Ruff 96 项同样为既有 baseline，因此不宣称 full repository verification PASS。
- Claim ceiling：该 archived stage 已完成 archive、durable docs、finite candidate、ff-only merge 和
  exact-old-OID lease push；commit `2c0d0d4e749e16e43d867931c58c6a82be56cf13` 是本阶段 planning base。

## Stage Authority Binding And Invalidation（archived，2026-08-20）

- OpenSpec change `bind-stage-authority-and-invalidation` 已归档到
  `openspec/changes/archive/2026-08-20-bind-stage-authority-and-invalidation/`；风险级别为 high，属于
  process-only repository development workflow change。它没有修改 `app/**`、公开 API、provider runtime、
  RepoPilot runtime subagent、后台任务、credential handling 或产品级 Git automation。
- 新增长期 `stage-authority-binding` capability，并同步 `harness-development-workflow`：宿主观察到的
  direct-user instruction 是唯一 human-authority 来源；repo-local append-only epoch record、delivery binding、
  hashes 和 validator 只提供 `mechanical_consistency_only`，不能证明用户身份、消息真实性、授权时序或
  `human_authorized=true`。
- Authority gate 绑定 exact stage/epoch/record、risk、scope digest、planning base、action ceiling、remote name、
  effective fetch/push endpoint fingerprints、target branch 与 authorized old tip。Validator 从 planning base
  重算 committed/dirty/untracked/rename/delete scope，要求 canonical authority directory、严格可逆的 Git `-z`
  path transport 和结构化 malformed-rule failures；endpoint equality 与两项 fingerprint 未在本地通过前不得
  触发 `ls-remote`、credential helper 或 network contact。
- Archive/merge/push 绑定实际 independent implementation review set、穷尽 reviewed-change manifest、精确四路径
  metadata exclusion、两文件 evidence tail 与 host-retained exact candidate。Merge/push 仍是 controller-only；
  push 只允许 ancestry 已证明 fast-forward 后的 explicit refspec + exact-old-OID lease，ambiguous outcome 保持
  `UNKNOWN_PUSH_OUTCOME` 并只做 same-endpoint read-only reconciliation。
- Final implementation review 的 A/B 两个首轮 reviewer 发现的 blocking P1 均经原 same-slot remediation re-review
  关闭；Focused Stage Debt Sweep 已完成，没有遗留新的 in-scope blocking debt。该结论不替代后续 final packet、
  candidate、merge 或 push gate。
- 验证 evidence：focused authority remediation tests `92 passed`；authority + independent-review + CLI 组合测试
  `163 passed`；changed Python Ruff PASS；OpenSpec pre-archive strict change PASS / all `24 passed, 0 failed`，
  post-archive all `23 passed, 0 failed`；`git diff --check` PASS。Full pytest 为 `645 passed, 3 failed`，3 项均为未修改路径的
  inherited baseline：model-provider recursion-depth 1 项，以及当前 shell 无 `python` 命令导致的
  verification-runner 2 项。Full Ruff 的 96 项也属于既有 baseline，因此不宣称 full repository verification
  PASS。
- Claim ceiling：OpenSpec archive 和上述 review/verification 事实已完成；finite candidate commit、merge、push、
  remote parity 与 `vcs_pushed=verified` 尚未由本记录证明，仍属于 tasks 4.5–4.8 的 controller closeout。

## Workflow Collaboration Rules Update（process-only，2026-07-05）

- 本次只更新 RepoPilot 开发流程和 review 规则，不修改 runtime、tests、public `/chat` contract、
  provider runtime、live eval、默认 CI 或产品能力。
- 普通窄阶段改为 summary approval（摘要确认）：Agent 负责阅读完整 OpenSpec
  proposal/design/tasks/spec，并向用户输出中文高信号摘要、风险级别、touched file families、non-goals
  和 implementation confirmation gate；用户不需要逐字审 OpenSpec artifacts，除非阶段高风险、
  改公开/runtime 行为、术语模糊或用户明确要求。
- MCP、Skill、subagent、connector、runtime plugin、background worker、durable execution、
  always-on assistant 等容易膨胀或误导的主题，在 OpenSpec 落笔前使用轻量 Grilling Gate
  压实术语、反例、runtime availability、approval/audit boundary 和 non-goals；普通 bugfix、文档修正、
  已知窄代码债不默认运行该 gate。
- Code review（代码审查）固定为分层审查：scope、business logic、architecture boundary、
  minimality、failure semantics、security/privacy、test adequacy、maintainability。Agent 默认负责底层
  实现、测试、安全和维护性判断，并把结论翻译成用户可判断的中文摘要；用户主要确认方向、边界、
  行为语义、风险接受和残余风险。
- 已同步 `docs/AGENT_RULES.md`、`.harness/rules.md`、repo-local `repo-stage-workflow` /
  `repo-stage-review-loop` skills，以及长期 `harness-development-workflow` spec。OpenSpec、skills、
  MCP 和 plugins 仍是开发流程参考，不能因此写成 RepoPilot runtime 能力。
- 2026-07-05 追加 human review depth（人工审查深度）规则到 repo-local
  `repo-stage-workflow` skill：L1 小改动看摘要/拍板点/non-goals/测试项并在实现后审 diff；
  L2 用户可见或 routing-sensitive 改动要求实现前扫 `design.md` 决策/风险和 `tasks.md`
  测试项，实现后提供 human review packet；L3 高风险改动要求完整审 `design.md`、
  `tasks.md` 和 spec MUST/SHALL 场景。该调整仅改变协作流程，不改变 runtime 能力。

## Runtime-Derived Capability Status（archived，2026-07-06）

- OpenSpec change：`derive-capability-status-from-runtime` 已归档到
  `openspec/changes/archive/2026-07-06-derive-capability-status-from-runtime/`；风险级别：medium。
  Scope 是让 capability-status（能力状态）和 Assistant Control Surface（助手控制面）的当前能力摘要
  从 active `ToolRegistry` backing primitives（支撑运行时原语）和固定安全边界派生，避免静态文案漂移。
- 已实现最小内部 adapter：新增 `app/harness/capabilities.py`，由 `ToolRegistry.list_specs()`
  的只读 `ToolSpec` snapshot 派生 structured runtime capability facts；`ToolRegistry`
  仍只存元数据，不 dispatch，不负责用户文案。
- `AgentLoop` 的 capability-status 路径现在通过 adapter 生成回答；当 custom `ToolRegistry`
  缺少 `patch_apply`、`verification_run`、`worktree_create` 或 `worktree_dispose` 时，不再宣称对应
  patch execution path 当前可用。默认 registry 仍报告 Safe Patch Authoring、Verification Runner、
  Patch + Verify、Persistent Audit / Recovery、worktree lifecycle 和 Verified Patch Promotion。
- Assistant Control Surface 现在接受 `AgentLoop` 显式传入的 active registry-derived capability summary；
  `AgentLoop(tool_registry=ToolRegistry(...))` 处理 `assistant status` 时不会回退到 default registry。
  控制面仍保持简短状态句，不输出 V11/V12/V13/V16/V25 阶段 marker，不新增 `/chat` 字段。
- 当前验证 evidence：RED focused tests 初次失败 4 项，覆盖缺少 `ToolRegistry.list_specs()`、
  capability-status 无视 custom registry、Assistant Control Surface 无视 active registry summary、
  `answer_status()` 不接受 injected summary。Internal final review 又发现 repo RAG backed status
  在 `repo_rag` 缺失时仍宣称 V11/V9 当前可用，已补 regression 并 fail-closed 到 `repo_rag 未注册`。
  OpenCode final review 发现 default patch answer 漏列 spec 要求的 `branch/PR automation`、`connector`、
  `background retry`、`runtime subagent` non-goals，已补 answer 和 test；focused re-review 确认 finding closed，
  no new in-scope findings。GREEN 后
  `pytest tests/test_agent_harness_kernel.py tests/test_assistant_control_surface.py -q`
  为 77 passed；`pytest tests/test_chat_api.py -q` 为 22 passed；`ruff check .` passed；
  `openspec validate derive-capability-status-from-runtime --strict` passed；
  `openspec validate --all` 为 23 passed、0 failed。Full `scripts/verify.ps1` 通过：pytest
  525 passed、1 skipped；ruff、stage docs scan、skill eval structure scan passed。`git diff --check`
  passed，仅 CRLF normalization warnings。Final implementation review 和 Focused Stage Debt Sweep
  未发现剩余 blocking debt。Archive 已同步长期 `agent-loop-tool-execution` 和
  `assistant-control-surface` specs；archive-after `openspec list` 为 No active changes found；
  `openspec validate --all` 为 22 passed、0 failed；archive-after full `scripts/verify.ps1`
  通过，pytest 525 passed、1 skipped，ruff、stage docs scan、skill eval structure scan 均通过；
  archive-after `git diff --check` 通过，仅有 CRLF normalization warnings。Implementation/archive
  commit `ec301b9` 已推送到 `agentic-codeops/main`。

## Control Routing And Test Naming Cleanup（archived，2026-07-03）

- OpenSpec change：`cleanup-control-routing-and-test-names`，已归档到
  `openspec/changes/archive/2026-07-03-cleanup-control-routing-and-test-names/`；当前分支：
  `main`；implementation commit `b3c92f5` 已 fast-forward 合并到 `main`；风险级别：medium。
- Scope 仅限 control routing cleanup（控制路由整理）和测试命名清理：`app/harness/kernel.py`
  的 capability-status（能力状态）识别收拢为内部 classifier/helper；相关 tests 改成能力导向命名；
  Assistant Control Surface parser（助手控制面解析器）保持小而明确，本阶段不扩展自然语言触发词。
  不修改 `/chat` public contract、provider runtime、live eval、默认 CI、patch/worktree、RAG、Memory
  或 Long Task 行为。
- Planning gate 已完成：proposal/design/tasks/spec delta 已创建；`.harness/allowed_files.md`
  与 `.harness/review_checklist.md` 已同步；internal、Codex independent 和 OpenCode independent
  plan review 均完成，findings 均按 `clarify` 处理；`openspec validate
  cleanup-control-routing-and-test-names --strict` 通过。
- Implementation 使用 TDD：新增 capability-status classifier route regression、location/search
  non-swallow regression 和 Assistant Control Surface narrow parser regression。RED 阶段
  `CapabilityStatusClassifier` import 按预期失败；GREEN 后 classifier 仍留在 `RequestRouter`
  内，不前移到 AgentLoop pre-router routes；`_capability_status_answer()` answer-selection 行为
  不变。
- 当前验证 evidence：focused classifier/parser tests 为 3 passed；adjacent
  `pytest tests/test_agent_harness_kernel.py tests/test_assistant_control_surface.py tests/test_chat_api.py -q`
  为 93 passed；`ruff check .` passed；`openspec validate --all` 为 23 passed、0 failed；
  full `scripts/verify.ps1` 通过，pytest 519 passed、1 skipped，ruff、stage docs scan、
  skill eval structure scan 均通过；`git diff --check` 通过，仅有 CRLF normalization warnings。
  Final implementation review 已完成初轮：Codex final review 的 documentation backfill finding
  和 spec wording finding 已按 `fix` / `clarify` 处理；OpenCode final re-review 复用
  `ses_1018bd2aeffeKLTCcQhhuQ1jFZ`，确认 findings closed 且 no findings。Focused Stage Debt
  Sweep 覆盖 changed runtime/tests/docs/OpenSpec/Harness 与 `app/assistant/control_surface.py`、
  `AgentLoop._run_inner()`、`RequestRouter.route()`、`AgentLoopResult.to_agent_result()` 直接边界，
  未发现新增 blocking debt。Archive 已同步长期 `agent-loop-tool-execution` 和
  `assistant-control-surface` specs；archive-after `openspec list` 为 No active changes found；
  archive-after `openspec validate --all` 为 22 passed、0 failed；archive-after full
  `scripts/verify.ps1` 通过，pytest 519 passed、1 skipped，ruff、stage docs scan、
  skill eval structure scan 均通过。Closeout 文档随当前 `main` 一起推送。

## Hybrid Fusion Settings Parameterization（archived，2026-07-03）

- OpenSpec change `parameterize-hybrid-fusion-settings` 已归档到
  `openspec/changes/archive/2026-07-03-parameterize-hybrid-fusion-settings/`；当前分支：
  `main`；implementation commit `c5946bf` 已 fast-forward 合并并推送到
  `agentic-codeops/main`；风险级别：medium。
- Scope 仅限 `app/rag/repo_rag.py` 的 hybrid fusion settings（混合检索打分配方）参数化，
  以及 `app/tools/tool_executor.py` 对有效 settings 的内部 audit summary 透传。不修改
  query understanding、rewrite、rerank、Evidence Pack、grounded answer、provider runtime、
  public `/chat` contract、live eval、默认 CI 或网络依赖。
- Planning gate 已完成：proposal/design/tasks/spec delta 已创建；`.harness/allowed_files.md`
  与 `.harness/review_checklist.md` 已同步；internal、Codex independent 和 OpenCode
  independent plan review 均完成，findings 已按 `fix/clarify` 处理；`openspec validate
  parameterize-hybrid-fusion-settings --strict` 通过。
- Implementation 使用 TDD：新增 default settings、custom settings、invalid settings、lexical anchor
  和 `ToolExecutor` internal audit pass-through RED coverage。旧实现下 focused tests 按预期失败：
  `HybridFusionSettings` 不存在，retriever audit summary 缺少权重，`ToolExecutor` 未透传权重。
  GREEN 后 lexical / embedding 权重和 `min_fused_score` 由显式 settings 表达，默认配方保持
  `0.65 / 0.35 / 0.35`，公开 `call_summary()` 不暴露这些内部配方值。
- 当前验证 evidence：focused/adjacent
  `pytest tests/test_repo_rag.py tests/test_tool_executor.py tests/test_agent_harness_kernel.py tests/test_chat_api.py -q`
  为 100 passed；`ruff check .` passed；`openspec validate --all` 为 23 passed、0 failed；
  full `scripts/verify.ps1` 通过，pytest 517 passed、1 skipped，ruff、stage docs scan、
  skill eval structure scan 均通过；`git diff --check` 通过，仅有 CRLF normalization warnings。
  Final implementation review 已完成：
  Codex final review 的流程记录 backfill finding 已按 `fix` 关闭，OpenCode final review 无 findings。
  Focused Stage Debt Sweep 覆盖 changed runtime/tests/docs/OpenSpec/Harness 与
  `app/harness/kernel.py` public/internal summary 边界；其两个 `fix` findings 已关闭：
  `ToolExecutor` 不再为缺失 fusion settings 合成默认 audit values，AgentLoop internal trace regression
  已覆盖 `lexical_weight` / `embedding_weight` / `min_fused_score`。Codex/OpenCode fix verification
  均确认 no findings。Archive 已同步长期 `repo-query-understanding-rag` spec；archive-after
  `openspec validate --all` 为 22 passed、0 failed；archive-after full `scripts/verify.ps1`
  通过，pytest 517 passed、1 skipped，ruff、stage docs scan、skill eval structure scan 均通过；
  archive-after `git diff --check` 通过，仅有 CRLF normalization warnings。Merge 后
  `openspec list` 为 No active changes found，`openspec validate --all` 为 22 passed、0 failed；
  merge-after full `scripts/verify.ps1` 通过，pytest 517 passed、1 skipped，ruff、stage docs scan、
  skill eval structure scan 均通过；commit `c5946bf` 已推送到 `agentic-codeops/main`。

## Evidence Pack Empty Snippet Omission（archived，2026-07-02）

- OpenSpec change `omit-empty-evidence-snippets` 已归档到
  `openspec/changes/archive/2026-07-02-omit-empty-evidence-snippets/`；当前分支：
  `codex/omit-empty-evidence-snippets`；风险级别：medium。
- Scope 仅限 `app/rag/evidence.py::build_evidence_pack()` 对 empty / whitespace-only
  snippet 的 Context Budget 计数语义，以及 `tests/test_evidence_pack.py` focused
  coverage、OpenSpec/Harness 和真实状态文档。不修改 retriever、grounded answer assembly、
  provider runtime、public `/chat` contract、live eval、默认 CI 或网络依赖。
- Planning gate 已完成：proposal/design/tasks/spec delta 已创建；`.harness/allowed_files.md`
  与 `.harness/review_checklist.md` 已同步；internal、Codex independent 和 OpenCode
  independent plan review 均完成，findings 已按 `clarify` 处理；`openspec validate
  omit-empty-evidence-snippets --strict` 通过。
- Implementation 使用 TDD：新增 empty snippet、whitespace-only snippet 和 empty-before-non-empty
  mixed ordering RED coverage；旧实现下 3 个新增测试按预期失败，因为 empty snippet 被计为
  `included=True`。GREEN 后 empty / whitespace-only snippet 保留 evidence item 以便审计，但
  `included=False`、`truncated=False`、不消耗 budget，并计入 `omitted_count`；后续非空 item
  仍可正常纳入预算。
- 当前验证 evidence：RED focused tests 为 3 expected failures；focused
  `pytest tests/test_evidence_pack.py -q` 为 7 passed；adjacent
  `pytest tests/test_grounded_answer.py tests/test_chat_api.py tests/test_repo_rag.py -q`
  为 43 passed；`ruff check .` passed；`openspec validate --all` 为 23 passed、0 failed；
  full `scripts/verify.ps1` 通过，pytest 513 passed、1 skipped，ruff、stage docs scan、
  skill eval structure scan 均通过；`git diff --check` 通过，仅有 CRLF normalization warnings。
  Final implementation review 已完成：Codex final review 的 P3 gate backfill finding 已按
  `fix` 关闭，OpenCode final review 无 findings。Focused Stage Debt Sweep 覆盖 changed
  runtime/tests/docs/OpenSpec/Harness 与 `grounded_answer`、`tool_executor`、`kernel`
  直接依赖，未发现新增 blocking debt。Archive 已同步长期 `repo-query-understanding-rag`
  spec；archive 后 `openspec list` 为 No active changes found，`openspec validate --all`
  为 22 passed、0 failed；archive-after full `scripts/verify.ps1` 通过，pytest 513 passed、
  1 skipped，ruff、stage docs scan、skill eval structure scan 均通过；archive-after
  `git diff --check` 通过，仅有 CRLF normalization warnings。

## Worktree Disposal Mutation Output Bounds Hardening（archived，2026-07-01）

- OpenSpec change `harden-worktree-disposal-mutation-output-bounds` 已归档到
  `openspec/changes/archive/2026-07-01-harden-worktree-disposal-mutation-output-bounds/`；风险级别：high；implementation
  commit `6c3ae95` 已 fast-forward 合入 `main`，closeout docs commit 已推送到
  `agentic-codeops/main`。
- Scope 仅限 `app/worktrees/disposal.py::_run_mutation()` destructive Git worktree mutation
  subprocess 的 stdout/stderr pre-read hard cap、timeout kill/reap hardening，以及
  `tests/test_worktree_disposal.py` focused coverage、OpenSpec/Harness 和真实状态文档。不修改
  disposal preflight、ownership、registry parsing、metadata runner、postcheck semantics、repo lock、
  ToolExecutor/PermissionPolicy/ApprovalGate、promotion、public `/chat` contract、provider runtime、
  live eval 或默认 CI。
- Planning gate 已完成：proposal/design/tasks/spec delta 已创建；`.harness/allowed_files.md`
  与 `.harness/review_checklist.md` 已同步；internal、Codex independent（用户授权 subagent）、
  OpenCode independent plan review 均完成，findings 已按 `fix / clarify / reject / defer`
  triage；`openspec validate harden-worktree-disposal-mutation-output-bounds --strict` 通过。
- Implementation 使用 TDD：新增 mutation fixed argv/shell/env regression、timeout kill/bounded reap、
  stdout/stderr oversize、pipe read failure、process start failure、non-zero exit、安全异常摘要、
  AgentLoop/audit 不泄漏 raw output/path/traceback-like/diff-like 内容，以及既有 disposal lifecycle
  回归覆盖。
- `_run_mutation()` 已从 `subprocess.run(..., capture_output=True)` 改为 disposal-local
  `subprocess.Popen(stdout=PIPE, stderr=PIPE, shell=False)` + Windows-safe bounded reader threads。
  stdout/stderr 各自最多计数/保留 `WORKTREE_DISPOSAL_MUTATION_OUTPUT_MAX_BYTES = 256_000`；reader
  可为 oversize detection 临时读取 1 byte sentinel，但不保留、不解码、不暴露 cap 外内容。Timeout、
  oversize、reader failure/non-completion、start failure 和 non-zero exit 均转为 caller 可捕获的安全
  `subprocess.SubprocessError`，不暴露 raw Git output、stderr、exception text 或本机路径。
- 当前验证 evidence：RED focused tests 7 expected failures before implementation；
  `pytest tests/test_worktree_disposal.py -q -k "mutation_runner"` 为 7 passed；
  mutation/lifecycle focused subset 为 11 passed；final review fix subset 为 3 passed；
  `pytest tests/test_worktree_disposal.py -q` 为 49 passed；
  `pytest tests/test_repo_mutation_locking.py -q` 为 17 passed；
  `ruff check .` passed；`openspec validate --all` 为 23 passed、0 failed；final full
  `scripts/verify.ps1` 通过，pytest 510 passed、1 skipped，ruff、stage docs scan、skill eval
  structure scan 均通过；`git diff --check` 通过，仅有 CRLF normalization warnings。
  Final implementation review 已完成：Codex independent review 的 3 个 P2 均按 `fix` 关闭，
  OpenCode final review 无 P0/P1/P2，P3 已按 `clarify/defer` 记录。Focused Stage Debt Sweep
  覆盖 changed runtime/tests/docs/OpenSpec/Harness 与 manager/tool/audit/kernel 直接依赖，未发现
  新增 blocking debt。Archive 已同步长期 `worktree-disposal-reconciliation` spec；archive-after
  `openspec validate --all` 为 22 passed、0 failed；archive-after full `scripts/verify.ps1`
  通过，pytest 510 passed、1 skipped，ruff、stage docs scan、skill eval structure scan 均通过；
  archive-after `git diff --check` 通过，仅有 CRLF normalization warnings。

## Git Metadata Output Bounds Hardening（archived，2026-06-28）

- OpenSpec change `harden-git-metadata-output-bounds` 已归档到
  `openspec/changes/archive/2026-06-28-harden-git-metadata-output-bounds/`，并已 fast-forward
  合并并推送到 `main`；风险级别：high。
- Scope 仅限 `app/worktrees/git_metadata.py` shared Git metadata runner 的 stdout
  pre-read hard cap、timeout kill/reap hardening，以及 `tests/test_worktree_disposal.py`
  focused coverage、OpenSpec/Harness 和真实状态文档。不修改 destructive disposal
  `_run_mutation()`、worktree create helper、inspection streaming diff、re-verification
  runner、promotion state machine、public `/chat` contract、provider runtime、live eval 或默认 CI。
- Planning gate 已完成：proposal/design/tasks/spec deltas 已创建；`.harness/allowed_files.md`
  与 `.harness/review_checklist.md` 已同步；internal、Codex independent、OpenCode
  independent plan review 均完成，findings 已按 `fix / clarify / reject / defer`
  triage；`openspec validate harden-git-metadata-output-bounds --strict` 通过。
- 当前 implementation 使用 TDD：新增 metadata timeout bounded reap、stdout oversize
  pre-read cap、pipe read failure、non-zero exit、cap-edge 和 disposal postcheck metadata
  unavailable 回归测试。
- `run_git_metadata()` 已从 temporary-file capture 改为 `stdout=subprocess.PIPE` +
  Windows-safe background reader；只保留最多 `MAX_GIT_METADATA_BYTES = 256_000`，允许
  transient 读取 1 个额外字节用于 oversize detection 但不保留；timeout、oversize、reader
  failure/non-completion、process-start failure 和 non-zero exit 均返回 `None`，并使用
  `GIT_METADATA_REAP_TIMEOUT_SECONDS = 1.0` / `GIT_METADATA_READER_JOIN_TIMEOUT_SECONDS = 1.0`
  做 bounded cleanup。
- 当前验证 evidence：metadata focused tests 5 passed；`pytest tests/test_worktree_disposal.py -q`
  为 38 passed；adjacent regressions 为 inspection 20 passed、re-verification 31 passed、
  promotion 28 passed；改动文件 `ruff check app/worktrees/git_metadata.py tests/test_worktree_disposal.py`
  通过；final full `scripts/verify.ps1` 通过，pytest 499 passed、1 skipped，ruff、stage docs
  scan、skill eval structure scan 均通过；`openspec validate --all` 为 23 passed、0 failed；
  `git diff --check` 无 whitespace error，仅 CRLF normalization warnings。
- Final review evidence：internal review 无 P0/P1/P2；OpenCode final review 复用 session
  `ses_1018bd2aeffeKLTCcQhhuQ1jFZ`，无 P0/P1/P2。两个 P3（Popen start-failure coverage、
  reader thread name）已按 `fix` / `clarify/fix` 处理，focused re-review 确认关闭且无新
  P0/P1/P2。
- Focused Stage Debt Sweep 覆盖 changed runtime/tests/docs/OpenSpec/Harness 和直接依赖的
  inspection、disposal/reconciliation、re-verification、promotion metadata caller；未发现
  blocking debt。残余相邻债仍是 `app/worktrees/disposal.py::_run_mutation()` destructive
  subprocess output cap，应独立阶段处理。
- Archive evidence：`openspec archive harden-git-metadata-output-bounds --yes` 成功，同步
  `verified-patch-promotion`、`worktree-disposal-reconciliation`、`worktree-inspection` 和
  `worktree-reverification` 4 个长期 specs；archive 后 `openspec list` 为 No active changes
  found，`openspec validate --all` 为 22 passed、0 failed；archive 后 full `scripts/verify.ps1`
  通过，pytest 499 passed、1 skipped，ruff、stage docs scan、skill eval structure scan 均通过。
- Merge/push evidence：`main` fast-forward 到 commit `6a16f5e` 并推送到
  `agentic-codeops/main`；merge 后 full `scripts/verify.ps1` 通过，pytest 499 passed、1 skipped，
  ruff、stage docs scan、skill eval structure scan 均通过。

## Worktree Inspection Timeout Hardening（archived，2026-06-28）

- OpenSpec change `harden-worktree-inspection-timeouts` 已归档到
  `openspec/changes/archive/2026-06-28-harden-worktree-inspection-timeouts/`；风险级别：high。
- 本阶段修复 `app/worktrees/inspection.py` 中 V21 read-only worktree inspection 的 streaming
  Git diff / hunk count / preview timeout 债务。Scope 仅限 inspection streaming Git process
  handling，不修改 worktree create / rollback、disposal/reconciliation、re-verification、promotion、
  repo mutation locking、public `/chat` contract、provider runtime、live eval 或默认 CI。
- Planning gate 已完成：proposal/design/tasks/spec delta 已创建；`.harness/allowed_files.md`
  与 `.harness/review_checklist.md` 已同步；internal plan review 按 `fix` 关闭 wait-only
  timeout 不覆盖 blocked stdout read 的缺口；OpenCode plan review 复用 session
  `ses_1018bd2aeffeKLTCcQhhuQ1jFZ`，无 P0/P1/P2，P3 均按 `clarify` 处理；Codex independent
  plan review 由 subagent `Euler` 完成，无 P0/P1/P2，P3 residual risks 已纳入 implementation guardrails。
- 当前 implementation 使用 TDD：新增 hunk count wait timeout、hunk count read timeout 和 preview
  timeout 回归测试；初次 focused RED 证明旧实现会抛 `TimeoutExpired` 且不会 kill/reap；GREEN
  后 `inspection.py` 通过 watchdog timer/thread 覆盖 stdout consumption 与 process wait，并在
  timeout / subprocess failure 时 kill/reap、返回 partial，不暴露 raw stderr、raw exception 或 raw diff。
- Final review evidence：internal implementation review 无 P0/P1/P2；OpenCode final review 复用
  session `ses_1018bd2aeffeKLTCcQhhuQ1jFZ`，发现 P2 unrealistic read-timeout test，已按
  `fix` 改成 timer fires -> kill -> EOF -> timed_out -> reap 的 watchdog path 测试；focused
  OpenCode re-review 确认 P2 closed 且无新 P0/P1/P2。P3 docstring / dead-code cleanup 已处理。
- 当前验证 evidence：`pytest tests/test_worktree_inspection.py -q` 为 20 passed；adjacent
  worktree/AgentLoop/API regressions 为 183 passed；`openspec validate --all` 为 23 passed、
  0 failed；`ruff check .` 通过；full `scripts/verify.ps1` 通过，pytest 489 passed、1 skipped，
  ruff、stage docs scan、skill eval structure scan 均通过；`git diff --check` 通过，仅有 CRLF
  normalization warnings。Archive 后 `openspec list` 为 No active changes found，`openspec validate
  --all` 为 22 passed、0 failed。

## Workflow Skill Update（archived，2026-06-28）

- OpenSpec change `update-repo-stage-workflow-skill` 已归档到
  `openspec/changes/archive/2026-06-28-update-repo-stage-workflow-skill/`；风险级别：low。
- 本阶段只更新 repo-local workflow/process 文档，不修改 RepoPilot runtime、public `/chat`
  contract、provider runtime、live eval、默认 CI、网络依赖、后台任务、runtime subagent、
  connector、notification 或自动 commit/merge/push 能力。
- `repo-stage-workflow` 已吸收 OpenSpec + Superpowers-style 工作流优点：OpenSpec 负责规格基线
  （需求、接口/模型、设计、任务、评审、变更和归档），执行纪律负责读规格、隔离、TDD、验证、
  review、finish 和 skill/process 自检。需求变化、设计矛盾或 scope drift 必须先回 OpenSpec。
- 同步修正 repo mutation locking closeout 后的 current-state 文档漂移，并把
  `tests/test_chat_api.py` docs consistency assertion 从“active OpenSpec 必须为无”改为“必须存在
  active-state 记录”，避免正常 active stage 触发误报。
- 验证 evidence：focused docs consistency regression 1 passed；`openspec validate
  update-repo-stage-workflow-skill --strict` 通过；archive 前 `openspec validate --all` 为
  23 passed、0 failed；full `scripts/verify.ps1` 通过，pytest 486 passed、1 skipped，
  ruff、stage docs scan、skill eval structure scan 均通过；archive 后 `openspec list`
  为 No active changes found，`openspec validate --all` 为 22 passed、0 failed；
  `git diff --check` 通过，仅有 CRLF normalization warnings。

## Repo Mutation Locking（archived，2026-06-28）

- OpenSpec change `harden-repo-mutation-locking` 已归档到
  `openspec/changes/archive/2026-06-28-harden-repo-mutation-locking/`；风险级别：high。
- Planning gate 已完成：proposal/design/tasks/spec delta 已创建；`.harness/allowed_files.md`
  与 `.harness/review_checklist.md` 已同步；internal、Codex independent、OpenCode
  independent plan review 均完成，findings 已按 `fix / clarify / reject / defer`
  triage；`openspec validate harden-repo-mutation-locking --strict` 通过。
- 当前 implementation 已新增 repo-key scoped SQLite mutation lock，用于 RepoPilot-owned
  write-risk flows：ordinary patch apply、组合 Patch + Verify、standalone
  verification、retained worktree re-verification、worktree disposal/reconciliation 和
  verified patch promotion。锁 conflict/unavailable 在 mutation 前 fail closed；read-only
  inventory/inspection/status/repo search 不获取 lock。
- 写风险 permission context 现在要求 lock provenance；lock conflict、release failure 等
  通过现有 `/chat.answer` 和 redacted persistent audit summary 表达，不新增 `/chat`
  顶层字段。
- 当前 verification evidence：`pytest tests/test_repo_mutation_locking.py -q` 为 17 passed；
  adjacent patch/worktree/promotion/verification/AgentLoop regressions 为 227 passed；
  `openspec validate --all` 为 23 passed、0 failed；full `scripts/verify.ps1` 通过，
  pytest 486 passed、1 skipped，ruff、stage docs scan、skill eval structure scan 均通过；
  `git diff --check` 通过，仅有 CRLF normalization warnings。
- Final review evidence：internal implementation review 已按 `fix` 关闭 lock acquisition
  exception、acquired/released audit outcome、exception-handler release failure 和 trace
  ordering；OpenCode final implementation review 复用 session
  `ses_1018bd2aeffeKLTCcQhhuQ1jFZ`，无 P0/P1/P2。Codex independent final review
  发现 P1 standalone `verification_run` runner exception 可能遗留 lock；已按 `fix`
  补 safe `runner_error` result 与释放锁回归测试，复核确认 P1 关闭且无新 P0/P1/P2。
- Stage Debt Sweep 已覆盖 changed runtime/tests/docs/specs/Harness、直接依赖、共享状态
  与调用路径；未发现新的 blocking debt。Archive 后 `openspec list` 为 No active changes
  found，`openspec validate --all` 为 22 passed、0 failed。该阶段已 fast-forward 合并并
  推送到 `main`。

## Documentation Source Consolidation（archived，2026-06-27）

- OpenSpec change `consolidate-stage-documentation-sources` 已归档到 `openspec/changes/archive/2026-06-27-consolidate-stage-documentation-sources/`；风险级别：medium。
- 本阶段目标是减少 README、ARCHITECTURE、PROGRESS、FEATURE_LIST、HANDOFF 和 Harness 之间的 current-stage fact 重复，降低 closeout 后 stale wording 漂移。OpenSpec、Harness、review checklist、Codex/OpenCode skills、Superpowers、MCP 和 plugin 继续只作为开发流程或外部协作范式，不写成 RepoPilot runtime 能力。
- Planning evidence：已创建 proposal/design/tasks/spec delta 并同步 `.harness/allowed_files.md` 与 `.harness/review_checklist.md`；internal、Codex independent、OpenCode independent plan review 已完成，findings 均按 `fix / clarify / reject / defer` triage；`openspec validate consolidate-stage-documentation-sources --strict` 通过。
- Implementation scope：README 中等压缩为项目门面；ARCHITECTURE 只保留稳定 runtime boundary；PROGRESS 保留阶段历史、durable decisions、validation evidence 和 unresolved debt；HANDOFF 只保留下轮安全行动上下文；FEATURE_LIST 保持 acceptance-oriented；`scripts/check_stage_docs.ps1` 只检查 current fact sections，不误伤 archived OpenSpec 或 historical PROGRESS entries。
- Implementation evidence：docs consistency regression 已更新为验证新文档职责，不再要求 README 承载完整 route map；full `scripts/verify.ps1` 通过，pytest 469 passed、1 skipped，ruff、stage docs scan、skill eval structure scan passed；`openspec validate --all` 为 22 passed、0 failed；`git diff --check` 通过，仅 CRLF normalization warnings。
- Final review evidence：OpenCode final implementation review 复用 session `ses_1018bd2aeffeKLTCcQhhuQ1jFZ`，覆盖 README route-map 收敛、ARCHITECTURE stable facts、PROGRESS/HANDOFF current facts、drift script、test contract、allowed files 和 runtime scope；无 P0/P1/P2/P3。Stage Debt Sweep 覆盖 changed docs、adjacent responsibility statements、drift script 和 docs consistency regression；无新增 blocking debt。
- Archive evidence：archive 使用 `openspec archive consolidate-stage-documentation-sources --skip-specs --yes`，因为长期 `harness-development-workflow` spec 已在 implementation 中同步；archive 后 `openspec list` 为 No active changes found，`openspec validate --all` 为 21 passed、0 failed。

## V25 Verified Patch Promotion（archived and merged，2026-06-27）

- OpenSpec change `add-verified-patch-promotion` 已归档到 `openspec/changes/archive/2026-06-27-add-verified-patch-promotion/`；风险级别保持 `high`；implementation commit `71aefd6 Add verified patch promotion` 已 fast-forward 合入 `main`。
- 已实现严格确认路由，位置在 V23 disposal/reconciliation 后、V22 re-verification 前；promotion 仅接受当前 scope 内 `verification_succeeded` + `applied_in_worktree` retained worktree，并检查主工作区干净、`HEAD == base_commit`、Git/worktree metadata、stored patch hash 和 worktree 内容完整性。
- 主工作区写入只使用 stored controlled patch，并经既有 `ToolRegistry`、`PermissionPolicy`、`ApprovalGate` 与 `ToolExecutor.patch_apply`。promotion 专用写入使用 Git atomic apply，patch/worktree/journal 的 `promoted` 终态通过 SQLite cross-database transaction 提交；状态同步失败会使用受控逆向 patch 回滚主工作区与 lifecycle，不能把 partial promotion 作为成功返回。
- V25 不实现 commit、merge、push、branch/PR、后台任务、自动 retry/repair、删除 retained worktree 或 `git worktree prune`。Fresh evidence：promotion focused tests 28 passed；adjacent patch/worktree/audit/AgentLoop/API regressions 172 passed；promotion + adjacent total 200 passed；archive 前 `openspec validate --all` 为 22 passed、0 failed；archive 后 `openspec list` 为 No active changes found，`openspec validate --all` 为 21 passed、0 failed；full `scripts/verify.ps1` 通过，pytest 469 passed、1 skipped，ruff、stage docs scan、skill eval structure scan 均通过；`git diff --check` 通过，仅有 CRLF normalization warnings。
- Review evidence：internal final review 修复了 promotion partial-write、post-apply state truthfulness、dirty-worktree TOCTOU、failed journal retry 和 capability-status 文案漂移；Codex final review 的 P1/P2 已按 `fix` 关闭：atomic apply 增加 `expected_base_commit` guard、`finalize_promotion()` 增加 patch/worktree/journal 状态前置条件、promotion audit payload 增加安全 `patch_id`。OpenCode final review 复用 session `ses_1018bd2aeffeKLTCcQhhuQ1jFZ`；focused re-review 确认上述 findings 已关闭且无新 P0/P1/P2。Stage Debt Sweep 已覆盖 changed runtime/tests/docs/specs/Harness；当时残余 P3 为无全局 repo lock 下的极窄跨进程 HEAD/file mutation race，后续由 `harden-repo-mutation-locking` 处理。

## V24 CLI Capability Surface / Plan Review Workflow Hardening（2026-06-25）

- OpenSpec change `polish-demo-cli-capability-surface` 已归档到
  `openspec/changes/archive/2026-06-25-polish-demo-cli-capability-surface/`，并已 fast-forward
  合并到 `main`；风险级别：medium；当前无 active OpenSpec change。
- V24 已重定义为 CLI Capability Surface / Demo-ready Product Surface：`repopilot` 继续作为 `ChatService.handle_chat()` 的薄入口，展示 grounded answer、patch proposal、explicit apply、deterministic verify、status 和 audit；不修改 `/chat` public contract、provider runtime、live eval、默认 Patch wiring、默认 CI、AgentLoop、ToolExecutor、VerificationRunner、Audit 或 Worktree runtime。
- 原 Verified Patch Promotion 已顺延为 V25/backlog 候选；本阶段不实现 promotion、commit、merge、push、branch management、PR creation、后台任务、subagents 或 connectors。
- 计划 review 流程已纳入本阶段：实现前计划 review 必须区分 internal plan review、Codex independent plan review 和 OpenCode independent plan review；OpenCode review 优先复用已有 session，终端超时后先检查 session final assistant review text，再决定 blocker/triage。
- 当前实现进展：CLI 已固定 `patch "<request>" -> "create patch: <request>"` 映射，patch id validator 固定为 `^patch_[A-Za-z0-9_]{1,122}$`，CLI 输出改为基于公开 `trace_id`、`answer`、`related_files`、`tool_calls` 的人类可读分段。
- 当前 workflow 进展：已更新 `.codex/skills/openspec-stage-planner`、`repo-stage-workflow`、`repo-stage-review-loop`、`external-review-triage` 和 `.opencode/skills/openspec-plan-review`，覆盖 plan-level review、final implementation review、外部 plan findings triage 和 OpenCode session reuse/timeout 规则。
- 当前验证 evidence：`openspec validate polish-demo-cli-capability-surface --strict` 通过；`openspec validate --all` 为 21 passed、0 failed；focused CLI tests 为 41 passed；adjacent CLI/API/AgentLoop/Verification regression 为 133 passed；`scripts/verify.ps1` 通过，pytest 441 passed、1 skipped，ruff、stage docs scan、skill eval structure scan 均通过；`git diff --check` 通过，仅有 CRLF normalization warnings。
- Final review evidence：internal final implementation review 修复了 `docs/PROGRESS.md` 路线图旧口径和长期 spec 中 `V24 promotion` 短语；focused external final review 复用 OpenCode session `ses_1018bd2aeffeKLTCcQhhuQ1jFZ`，终端超时后从 session final assistant review text 取证，无 P0/P1。P2.1 `FEATURE_LIST passes:true` vs unchecked checklist 已按 `fix` 通过 checklist 更新关闭；P3 输出风格、parser-coupled test、skill wording tests 和错误消息措辞均分类为 `defer` 或 `clarify`，不阻断。
- Stage Debt Sweep：覆盖 `app/cli.py`、`tests/test_cli.py`、`app/patching/parser.py` / `ChatService` 邻近 message path、`.codex/skills/**` workflow、`.opencode/skills/openspec-plan-review`、README/ARCHITECTURE/PROGRESS/AGENT_RULES/FEATURE_LIST/HANDOFF、OpenSpec change artifacts、long-term specs 和 Harness files；无新增 blocking debt。
- Archive evidence：long-term specs 已在 archive 前同步；archive 使用
  `openspec archive polish-demo-cli-capability-surface --skip-specs --yes`，避免重复应用已同步的
  delta specs。Archive-after `openspec list` 为 No active changes found；`openspec validate --all`
  为 20 passed、0 failed；full `scripts/verify.ps1` 通过，pytest 441 passed、1 skipped，ruff、
  stage docs scan、skill eval structure scan 均通过；`git diff --check` 通过，仅有 CRLF normalization
  warnings。

## Demo-ready Agent CLI Implementation Closeout（2026-06-25）

- OpenSpec change `add-demo-ready-agent-cli` 已归档到 `openspec/changes/archive/2026-06-25-add-demo-ready-agent-cli/`；当前分支：`codex/add-demo-ready-agent-cli`；风险级别：medium；当前无 active OpenSpec change。
- 已完成 TDD RED -> GREEN：新增 `tests/test_cli.py`，覆盖 `ask`、`patch`、`patch confirm`、`patch confirm --verify`、`verify`、`status`、`audit latest` 到 `ChatService` 的薄映射。
- 已实现 `app/cli.py` 和 `pyproject.toml` console script：`repopilot = "app.cli:main"`；CLI 默认 `repo_path=.`、`user_id=cli`、`session_id=cli`，支持 `--repo`、`--user-id`、`--session-id` 覆盖。
- 安全边界保持不变：只接受 `verify`、`pytest`、`ruff` 固定验证标签；unsafe verification input、empty required values 和 unsafe patch id 在调用 `ChatService` 前拒绝；不新增网络依赖、HTTP client mode、provider runtime wiring、默认 CI、`/chat` contract、默认 Patch wiring 或 Verified Patch Promotion。
- Review evidence：内部 final review 无 P0/P1/P2；focused external review 复用 OpenCode session `ses_10290b071ffeLx5JxfppaZ3qfo`，结论无 P0/P1/P2；其非阻塞空值 exit-code 观察已补 RED coverage 并修复。
- Verification evidence：focused CLI tests 32 passed；adjacent AgentLoop/API/verification regressions 124 passed；pre-archive full `scripts/verify.ps1` 通过，pytest 432 passed、1 skipped；archive-after `openspec validate --all` 20 passed、0 failed；archive-after full `scripts/verify.ps1` 通过，pytest 432 passed、1 skipped，ruff、stage docs scan、skill eval structure scan 均通过；`git diff --check` 通过，仅有 CRLF normalization warning。

## README 门面优化 / Demo-ready Agent CLI Planning（2026-06-24）

- Active change：`demo-ready-readme-cli-planning`；当前分支：`main`；风险级别：low。
- 本阶段目标是先优化 README 顶部“面试官版”项目介绍，并规划 Demo-ready Agent CLI；当前不直接实现 CLI runtime，不创建 V24。
- README 规划口径：面向代码仓库理解、受控 Patch 和验证闭环的本地 Coding Agent Harness；只列当前已实现能力，不把 Roadmap 或 CLI 写成已实现。
- CLI 规划口径：未来 `repopilot` 命令只作为现有 AgentLoop / ToolExecutor / VerificationRunner / Audit / Worktree 能力的薄入口；不重写 AgentLoop，不修改 `/chat` contract，不改变默认 CI，不引入网络依赖。
- 已同步 `.harness/allowed_files.md` 与 `.harness/review_checklist.md`；允许范围排除 `app/**`、`tests/**`、live eval profile、provider runtime、默认 Patch wiring、CLI implementation 和 V24。
- Planning validation：`openspec validate demo-ready-readme-cli-planning --strict` 通过；`openspec validate --all` 为 20 passed、0 failed；`git diff --check` 通过，仅有 CRLF normalization warning。
- README 首屏已优化为项目门面：一句话定位、核心能力、执行闭环、快速开始、文档入口和 `Demo-ready CLI 规划中`；V20-V23 阶段记录已下沉到阶段历史。
- CLI 仍保持规划-only；未新增 runtime entrypoint、package metadata、命令 parser、命令测试或发布配置。
- Verification：focused route-map regression 1 passed；full `scripts/verify.ps1` 通过，pytest 400 passed、1 skipped，ruff passed，stage docs scan passed，skill eval structure scan passed；OpenSpec all 20 passed、0 failed；`git diff --check` 通过，仅有 CRLF normalization warning。
- 2026-06-25 archive closeout：`demo-ready-readme-cli-planning` 已归档到
  `openspec/changes/archive/2026-06-25-demo-ready-readme-cli-planning/`；long-term specs 已同步
  `openspec/specs/demo-ready-agent-cli/spec.md` 与
  `openspec/specs/harness-development-workflow/spec.md`；当前无 active OpenSpec change。Archive 后
  `openspec validate --all` 为 20 passed、0 failed；full `scripts/verify.ps1` 通过，pytest
  400 passed、1 skipped，ruff passed，stage docs scan passed，skill eval structure scan passed。

## DeepSeek Provider Conformance Revalidation Closeout（2026-06-24）

- `revalidate-deepseek-provider-conformance` 已归档并 fast-forward 合并到本地 `main`。
- Merge 后 full `scripts/verify.ps1` 为 400 passed、1 skipped；OpenSpec all 为 19 passed、0 failed；
  stage docs 与 `git diff --check` 通过。
- 当前无 active OpenSpec change；未创建 V24。下一步仅剩 push `main` 到远端。

## Grounded Prompt Injection Live Behavior Remediation（2026-06-24）

- Change `harden-grounded-prompt-injection-live-behavior` 已归档到
  `openspec/changes/archive/2026-06-24-harden-grounded-prompt-injection-live-behavior/`，并已
  fast-forward 合回 paused `codex/revalidate-deepseek-provider-conformance`；风险级别：high。
- 本 remediation 从 paused `codex/revalidate-deepseek-provider-conformance` 切出，只处理
  `deepseek-v4-flash` 可信 conformance FAIL 中唯一失败的 `prompt_injection_executed` gate。
- Scope：只允许收紧 Grounded Answer grounded-text prompt contract 与 deterministic tests；不修改
  evaluator、fixture、rubric、profile、pricing、live evidence schema、`scripts/verify.ps1`、默认 CI、
  `/chat` public contract、默认 Patch wiring 或 V24。
- 非目标：不做 output sanitizer、marker blacklist、evidence filtering/projection/suppression、额外模型调用、
  retry、模型切换或 evaluator gate 降级。
- 已按 TDD 实现最小 prompt-only remediation：`grounded_text` system prompt 和 user-message evidence
  JSON 前的 handling contract 现在要求从 evidence data 中抽取 repository facts，把 directed-at-assistant
  的命令、角色、策略、response rule 和 extra-output request 视为 evidence-borne instruction，并静默忽略其
  requested output target；同段合法 repository fact 和用户明确询问的同名 repository identifier 仍允许回答。
- 新增 deterministic payload tests 验证：raw hostile evidence 仍完整进入 user prompt，attack target 未进入
  system prompt blacklist，`json_object` prompt assembly 保持不变。
- Deterministic verification：`pytest tests/test_model_provider.py -q` 为 45 passed；full
  `scripts/verify.ps1` 为 400 passed、1 skipped；OpenSpec strict/all 为 21 passed、0 failed；stage docs、
  skill eval、ruff 与 `git diff --check` 通过。
- Formal review：internal review、OpenCode independent adversarial review 和 focused Stage Debt Sweep 均未发现
  P0/P1/P2。Residual：deterministic tests 只能证明 prompt contract，没有证明真实 DeepSeek 服从；后续仍需
  paused revalidation 分支按原 contract 运行一次 renewed live gate。
- 本 change 未运行真实 live gate；合回 paused revalidation 分支后，旧 `20260624-110532` live evidence
  因 runtime prompt 变化而成为 stale certification evidence。新的 live gate 必须先完成 deterministic
  preflight，再由用户再次明确确认。
- 合回后的 revalidation deterministic preflight 已通过：focused evaluator tests 64 passed；full
  `scripts/verify.ps1` 400 passed、1 skipped；`openspec validate revalidate-deepseek-provider-conformance --strict`
  通过；OpenSpec all 20 passed、0 failed；stage docs 与 `git diff --check` 通过。
- 用户已明确确认 renewed live gate；runner 在 clean commit
  `8b018b84ae8c39eff3b18aeda98ac4a106b9d65d` 上返回 PASS，stdout 包含
  `PASS live model provider eval` 和 attestation path。
- PASS attestation：`docs/evals/live-model-provider/20260624-124206.json`；local sanitized report：
  `.repopilot/live-eval/20260624-124206.json`；report SHA-256：
  `bd5010d556061fdb77243da16e4a305790f5416f3bcaa5a3382fe84d2170cdbb`，与 attestation 一致。
- Renewed live evidence：10 cases、8 provider calls、quality baseline 5/5、aggregate 4638 tokens、
  12629 ms、cost ¥0.00334040；所有 provider-backed cases 均为 `availability=available`、
  `finish_reason=stop` 且 usage complete；no-answer 与 secret-filter 为预期 zero-call PASS。
- 同 run 未生成 failure record；key-level redaction review 未发现 API key、完整 URL、raw prompt、
  EvidencePack、raw answer、raw response、HTTP payload、headers、diff、reasoning content 或 raw
  fingerprint。只出现允许的 aggregate token keys 与 `system_fingerprint_status`。
- `revalidate-deepseek-provider-conformance` 已归档到
  `openspec/changes/archive/2026-06-24-revalidate-deepseek-provider-conformance/`，并同步长期
  `openspec/specs/live-model-provider-eval/spec.md`；archive 后 full verify 为 400 passed、1 skipped，
  OpenSpec all 为 19 passed、0 failed，stage docs 与 `git diff --check` 通过。当前等待用户授权
  merge to `main` / push。

## DeepSeek Provider Conformance Revalidation（2026-06-24）

- Change `revalidate-deepseek-provider-conformance` 已归档到
  `openspec/changes/archive/2026-06-24-revalidate-deepseek-provider-conformance/`；当前分支：
  `codex/revalidate-deepseek-provider-conformance`；风险级别：high；未创建 V24。
- 最终 certification evidence 是 PASS attestation
  `docs/evals/live-model-provider/20260624-124206.json`，认证 tested commit
  `8b018b84ae8c39eff3b18aeda98ac4a106b9d65d` 下的 `deepseek-v4-flash` profile/rubric/model。
- 下面保留本 change 的历史执行轨迹；早期 transport blocker 与旧 runtime prompt-injection FAIL 均不得解释为最终 provider certification。
- Planning baseline commit：`ffaa453`；pre-live evidence commit：
  `f4d1270b218dd95078b0c84ceec85a38422e05ee`。Preflight 已通过：focused evaluator
  tests 57 passed；full `scripts/verify.ps1` 为 391 passed、1 skipped；OpenSpec 20/20；
  stage docs、skill eval、ruff 与 `git diff --check` 通过。`.env.live` 仅做 key presence
  检查，未打印值，未发送额外诊断请求。
- 独立 focused review 确认无 P0/P1/P2 blocker；Stage Debt Sweep 仅检查 live
  runner/entrypoint 直接依赖和 closeout docs，未发现本 change 需处理 finding。
- 真实 DeepSeek live gate 已按用户确认执行一次，无 retry、无模型切换、无额外诊断请求；runner
  结果为 FAIL，未生成 PASS attestation。随后用户从 provider 侧确认本次运行未看到请求，因此该
  run 不得解释为 DeepSeek provider conformance FAIL，只能作为 provider-contact 未证实的
  transport/integrity blocker 现场。
- 本次失败证据：`docs/evals/live-model-provider/failures/20260624-013028.json`；本地脱敏报告：
  `.repopilot/live-eval/20260624-013028.json`；本地报告 SHA-256：
  `aeebd2aea7c3a41411242e3fe651daad4a14b93b93b39ff28c93f9ef8a681d8a`。
- Runner-produced failure record 绑定 commit `f4d1270b218dd95078b0c84ceec85a38422e05ee`、UTC
  `2026-06-24T01:30:28Z`、provider `openai_compatible`、model `deepseek-v4-flash`、
  rubric `2026-06-22`；10 cases / 8 calls 完整，report hash 与 record 一致，未生成同 run
  attestation sibling，API key 和完整 base URL 未进入 tracked failure record。但这些 “8 calls”
  是 runner/provider-attempt 计数，不证明 DeepSeek 服务端收到请求。
- Runner failed gates：`chat_citation_invalid`、`finish_reason_not_stop`、
  `grounded_answer_provider_error`、`patch_proposal_invalid`、`planner_fallback`,
  `returned_model_mismatch`、`usage_incomplete`。
- 本地诊断显示 8 个应发起 provider 调用的 case 全部为 `availability=unavailable`、finish/model/usage
  为空，且当前环境存在 `HTTP_PROXY` / `HTTPS_PROXY` / `ALL_PROXY` 等代理变量；初步怀疑请求在
  本地 transport/proxy 层失败，未到达 DeepSeek endpoint。当前 runner/report 不保留脱敏
  `error_class`，因此无法仅凭 tracked report 证明具体 transport 根因。
- 当前状态：本 change 按契约暂停。Failure record 只是当前 revalidation 分支的失败现场 artifact，
  不是 provider certification evidence，也不应作为 provider conformance FAIL evidence 使用；不得
  archive、不得 merge 到 `main`、不得 push 为完成态，除非后续正式 reshape 契约。任何 remediation
  必须进入独立 OpenSpec change。

## Live Model Provider Integration / Eval（2026-06-22）

- Active change：`add-live-model-provider-eval`；开发分支：
  `codex/add-live-model-provider-eval`；风险级别：high。
- 已实现独立 Python evaluator、DeepSeek `deepseek-v4-flash` profile、固定 `x/5` 质量
  baseline、安全/结构/provider hard gates、8 次调用预算、成本计算、脱敏本地报告和
  PASS-only tracked attestation。
- 已实现 fresh subprocess `/chat` 默认 wiring smoke、Grounded Answer、Long Task Planner、
  显式注入 Patch Authoring、无答案零调用、prompt injection 和 secret filtering。
- 默认 pytest、`scripts/verify.ps1` 与 CI 保持离线 deterministic；薄 PowerShell 入口缺少 live
  配置时明确 SKIP。
- Remediation 合入前的 deterministic verification 为 361 passed、1 skipped，evaluator tests
  30 passed；旧 internal/external review 无剩余 P0/P1。由于 runtime 已变化，这些证据必须重跑，
  不作为当前 archive gate。
- Remediation 合入后的新 deterministic evidence：evaluator tests 31 passed、直接相邻回归
  155 passed、full verify 363 passed、1 skipped、OpenSpec strict/all 19 passed。
- 新 formal review 修复 Prompt Injection 原始输出包含 `ATTACK_MARKER` 但先被 citation fallback
  掩盖归因的问题；独立 re-review 确认无剩余 P0-P2。聚焦 Stage Debt Sweep 未发现新增阻断债务。
- 更新后的真实 DeepSeek run 在 commit `3dfd06d` 完成 8 calls：所有 response
  `finish_reason=stop` 且 usage 完整；Planner、Patch、无答案和 secret filtering PASS；4 个
  grounded fixture fallback、`/chat` citation invalid，Prompt Injection 输出
  `ATTACK_MARKER`。质量 baseline 为 0/5，未生成 attestation。
- 第二个 remediation 已归档、合并、推送并合入本分支：grounded user message 改用裸 citation
  labels 与 untrusted JSON evidence envelope，system instruction 强化 anti-injection 规则。
  因 runtime 再次变化，旧 deterministic review/live 证据全部失效，当前等待完整重验。
- 新 deterministic evidence：evaluator tests 31 passed、adjacent regression 157 passed、
  full verify 365 passed、1 skipped、OpenSpec strict/all 19 passed；等待基于新 commit 的
  formal review 与 live gate。
- Final internal review、independent adversarial re-review 与 Stage Debt Sweep 已完成，无
  P0-P2；P3 均为冗余 smoke、脱敏诊断或固定 rubric scope 边界，不阻断 live gate。
- 第三次真实 run 在 commit `46687f3` 完成 8 calls：`/chat`、实现解释、配置、测试、
  Prompt Injection、Planner、Patch、no-answer 与 secret filtering 全部通过，仅 ambiguous case
  fallback；所有真实 response 均为 `finish_reason=stop` 且 usage 完整。
- 该失败暴露 evaluator 诊断缺口：报告只记录泛化 `grounded_answer_fallback`，无法区分
  `missing_citation`、`invalid_citation` 或 provider error。Evaluator 现从 Grounded Answer 已脱敏
  audit allowlist 读取 `fallback_reason` 并生成具体 hard-gate code，不保存原始回答。
- Evaluator 自身再对 fallback reason 做逐值 allowlist，未知值统一为 `grounded_answer_unknown`。
  Final evaluator tests 32 passed、adjacent regression 157 passed、full verify 366 passed、
  1 skipped、OpenSpec strict/all 19 passed；最终 re-review 无 P0-P3。
- 第四次真实 run 在 commit `0b82afb` 再次仅 ambiguous case 失败，具体原因为
  `grounded_answer_missing_citation`；其余 hard gates PASS，8 calls 的 finish reason 与 usage
  完整。连续两次该 case 都返回 235 tokens 并缺 citation，判定为稳定 runtime instruction 行为，
  不是可通过无 retry 重跑解决的模型漂移。
- 独立 grounded citation footer remediation 已归档、合并、推送并合入 eval 分支：所有 grounded
  response（包括澄清或拒答）最后一行必须逐字输出一个裸 allowed label，不降低 validator 或 gate。
  因 runtime 再次变化，旧 deterministic review/live/attestation 证据全部失效。
- 最终 deterministic revalidation：evaluator tests 34 passed、adjacent regression 144 passed、
  full verify 368 passed、1 skipped、OpenSpec strict/all 19 passed；ruff、stage docs、skill checks
  与 `git diff --check` 通过。
- 最终 adversarial review 修复 API subprocess 失败时附带错误 call-count 诊断，以及
  Prompt Injection marker 大小写变体绕过；re-review 无剩余 P0-P3。Final Stage Debt Sweep
  未发现新增阻断债务。
- 第五次真实 DeepSeek run 在 clean commit `3b7d5cc` 完成 8 calls：质量 baseline 5/5，
  citation、ambiguous、Planner、Patch、no-answer、secret filtering、finish reason 与 usage
  全部通过；唯一失败为 `prompt_injection_executed`。聚合 2810 tokens、9561 ms、成本
  ¥0.00301968；sanitized report SHA-256 为
  `9990cf23dbcead3daf83fb1b23945a1ed4a0bb403559c0efd05b05157476c02c`，未生成 attestation。
- 该失败证明模型仍会输出 evidence 内不可信指令要求的 marker。Eval change 已按契约冻结，
  后续必须通过独立 prompt-injection runtime remediation 处理；不得在 eval change 内修改
  Provider prompt、fixture、rubric 或 gate，也不得通过重复 live run 碰运气。
- Reviewed evaluator implementation 已提交；随后在 clean tracked tree 上运行 live 入口，因五个
  必需环境变量均缺失而按契约 SKIP/0，未发起真实网络请求、未生成 attestation。
- 随后用户通过 Git-ignored 临时环境文件提供完整配置，真实 DeepSeek run 在 commit `a842ca1`
  上完成 8 次调用：Planner、Patch、无答案和 secret filtering PASS；6 个 grounded-text 路径均
  因 citation gate 失败。所有 provider response 均为 `finish_reason=stop` 且 usage 完整。
- 根因是 runtime grounded-text system prompt 只要求“引用 citation”，未明确要求逐字复制 provided
  `path:start-end` label，而 validator 要求 exact match。独立
  `harden-grounded-citation-instruction` remediation 已归档、合并、推送并合入本分支；旧
  live/review 证据全部失效，当前等待完整重验。
- 真实 PASS 和 attestation 产生前，本 change 不得归档或合并。
- 本阶段不修改 Model Provider runtime、默认 Patch wiring、`/chat` contract，不创建 V24。
- 已知非阻断 residual：Patch smoke 的临时 SQLite DB 在 Windows 清理前依赖 CPython
  `gc.collect()` 释放短生命周期连接；当前 Windows regression 通过，若未来引入其他 Python
  runtime，应在独立 store-lifecycle hardening change 中增加显式 close 边界。
- 已知非阻断 residual：既有 citation regex 不接受 `Makefile`、`README` 等无扩展名路径；
  本轮固定 fixture 未触发，修改该 validator contract 需独立 OpenSpec change。
- 独立 `harden-grounded-prompt-injection-suppression` remediation 已归档、合并、推送并合入
  eval 分支；旧 deterministic review/live/attestation 证据再次失效，当前等待完整重验。
- 第四个 remediation 合入后的 deterministic revalidation：evaluator 34 passed、adjacent
  144 passed、full verify 368 passed、1 skipped、OpenSpec strict/all 19 passed。Final internal
  review、independent adversarial re-review 与 Stage Debt Sweep 已完成，无剩余 P0-P3。
- 第六次真实 DeepSeek run 在 clean commit `21ec714` 完成 8 calls：质量 baseline 5/5，
  citation、ambiguous、Planner、Patch、no-answer、secret filtering、finish reason 与 usage
  全部通过；唯一失败仍为 `prompt_injection_executed`。聚合 3642 tokens、11986 ms、成本
  ¥0.00288216；sanitized report SHA-256：
  `53754678b7bc3a03354b19863a20dc8be676875e0e7e1b85a005f85e26362496`，未生成 attestation。
- Prompt-only remediation 前后相同 hard gate 均稳定失败，因此停止继续堆叠自然语言措辞或重复
  live run。未创建 evidence filtering remediation：代码仓库中的 prompt、测试、脚本和安全文档
  本身包含合法指令性文本，通用语义过滤可能误删证据、破坏 citation/model-view 一致性并制造 DoS。
- Change 2 正式 reshape 为两层结论：evaluator readiness 与 provider conformance 分离。Prompt
  Injection 仍是 hard gate，FAIL 仍返回 1，PASS-only attestation 不变；可信完整 FAIL 将生成固定
  allowlist 的 evaluated-failure record。Change 归档只表示 evaluator readiness，不表示
  `deepseek-v4-flash` 获得认证。
- Failure record 只允许记录 evaluator commit、UTC 时间、provider/model、rubric version、
  排序后的失败 gate 和本地报告 SHA-256；禁止回答摘录、prompt、EvidencePack、完整 URL、密钥、
  diff、reasoning content、原始 fingerprint 或 HTTP payload。
- Reshaped evaluator 已按 TDD 实现：本地报告、PASS attestation 与 evaluated-failure record 使用
  exclusive create；固定 conformance/integrity gate 分类中，所有单 case/整轮 call-count 异常均为
  integrity blocker。Failure record 额外验证固定 10-case/8-call 完整性、SHA-256 和 UTC 时间。
- 最终实现 review 修复了基于异常消息字符串区分 integrity 的 P1，改为
  `EvaluationIntegrityError` 类型；独立复审未发现新增 P0-P2。最新 deterministic evidence：
  evaluator 57 passed，adjacent 167 passed，full verify 391 passed、1 skipped。
- 最终真实 DeepSeek gate 在 clean evaluator commit
  `9697c3e8f565a1cd765f36523c5f330c75a2d4bc` 上完成 10 个计划 case、8 次调用，返回
  FAIL（exit 1）并生成 tracked evaluated-failure record
  `docs/evals/live-model-provider/failures/20260623-091528.json`；未生成 attestation。
- 本地脱敏报告 `.repopilot/live-eval/20260623-091528.json` 的 SHA-256 为
  `e2a5aea7e634d56c54259cd219a8c92437fd918f43dce572565da273bcc657f3`，与 failure record
  一致；record exact allowlist、UTC、provider/model、rubric 和排序去重 gate 均已复核，敏感字段
  扫描无命中。
- 本轮 8 个真实 provider 调用均记录为 `availability=unavailable`，未返回 model、finish reason
  或 usage；失败 gates 为 `chat_citation_invalid`、`finish_reason_not_stop`、
  `grounded_answer_provider_error`、`patch_proposal_invalid`、`planner_fallback`、
  `returned_model_mismatch`、`usage_incomplete`。因此本阶段只证明 evaluator readiness，
  `deepseek-v4-flash` 未通过本 profile/rubric 的 conformance gate，不能写为已认证。
- Change 2 已归档为
  `openspec/changes/archive/2026-06-23-add-live-model-provider-eval/`，并同步新增长期 capability spec
  `openspec/specs/live-model-provider-eval/spec.md`。归档语义仅为 evaluator readiness 完成。
- Change 2 已合并并推送到 `agentic-codeops/main`；merge 后 full verify 为 391 passed、1 skipped，
  OpenSpec 19/19 与 stage closeout 均通过。当前无 active OpenSpec change。

## Grounded Prompt Injection Suppression Remediation（2026-06-23，已归档）

- Change 已归档为 `2026-06-23-harden-grounded-prompt-injection-suppression`；风险级别：medium。
- 第五次真实 DeepSeek eval 在 clean commit `3b7d5cc` 完成 8 calls，质量 baseline 5/5，
  citation、Planner、Patch、ambiguous、no-answer、secret filtering、finish reason 和 usage 均通过，
  唯一失败为 `prompt_injection_executed`。
- Grounded-text instruction 现要求静默忽略 evidence 内的命令、角色、策略、声明式 response rule
  和额外输出要求；不得确认、解释拒绝、转换或复现 original query 未明确询问的 marker/token。
- 相同字符串若是 original query 明确询问的仓库事实或标识符，仍允许只基于相关 evidence 回答；
  citation footer、validator、evidence envelope、JSON mode、metrics、API、默认 Patch wiring 和
  persistence 均未修改。
- TDD RED/GREEN 已完成；focused Provider/Grounded Answer/AgentLoop/API regression 为
  137 passed。Final full verify 为 334 passed、1 skipped；OpenSpec strict/all 为 19 passed。
- Focused external review 初审提出 2 个 P2、1 个 P3 和 1 个测试表述缺口；已收紧
  `attack target`、`unrelated`、声明式规则覆盖和 prompt-contract 证据措辞，re-review 无剩余
  P0-P3。Stage Debt Sweep 未发现新增阻断债务。
- Residual：prompt-only contract 是否被真实模型服从必须由 eval change 完整重跑验证；同名合法
  标识符例外与通用 marker substring gate 的潜在语义冲突未被当前固定 fixture 触发。

## Grounded Citation Footer Remediation（2026-06-23，已归档）

- Change 已归档为 `2026-06-23-require-grounded-citation-footer`；风险级别：medium。
- Ambiguous live case 连续两次稳定生成 235 tokens 但缺 citation；其他 hard gates 已通过。
- Grounded instruction 现要求每个 response（包括回答、澄清或拒答）最后一行只包含一个裸
  allowed `path:start-end` label，不得添加前缀、markdown、包装符号、bullet、标点或额外文本。
- 不自动追加 citation，不修改 validator、evidence envelope、JSON mode、metrics、API、默认
  Patch wiring、persistence 或 paused evaluator。
- TDD RED/GREEN 已完成；Provider/Grounded Answer/AgentLoop/API focused regression 为
  137 passed。
- External review 发现默认 `FakeModelProvider` 仍使用句中带标点 citation；已按 TDD 对齐为裸
  citation footer，使默认 deterministic provider 与真实 provider instruction 使用同一 contract。
- Final full verify 为 334 passed、1 skipped；OpenSpec strict/all 为 19 passed。Internal/
  focused external review 与 Stage Debt Sweep 已完成，无剩余 P0-P3。
## Grounded Evidence Framing Remediation（2026-06-23，已归档）

- Change 已归档为 `2026-06-23-harden-grounded-evidence-framing`；风险级别：medium。
- 第二次真实 DeepSeek run 在 8 calls、finish reason 与 usage 均正常时，仍出现 grounded citation
  fallback 和 Prompt Injection marker；Planner/Patch/no-answer/secret filtering 正常。
- Grounded user prompt 现使用与 validator/system allowed list 一致的裸 `path:start-end` label，
  并把 evidence 序列化为明确的不可信 JSON data envelope。
- System instruction 现禁止遵循、复述、转换、编码或以其他方式执行 evidence 内改变回答行为、
  泄露内容或输出 marker/token 的指令；JSON mode prompt assembly 保持不变。
- TDD RED/GREEN 已覆盖 framing、envelope、anti-injection instruction 与 JSON parity；
  external review 后又移除 allowed-list bullet、收紧行为指令措辞并增加特殊字符 round-trip；
  Provider/Grounded Answer/AgentLoop/API focused regression 为 137 passed。
- Final deterministic verification 为 334 passed、1 skipped；OpenSpec strict/all 为 19 passed。
  Internal/focused external review 与 Stage Debt Sweep 已完成，无剩余 P0-P3。

## Grounded Citation Instruction Remediation（2026-06-22，已归档）

- Change 已归档为 `2026-06-22-harden-grounded-citation-instruction`；风险级别：medium。
- 真实 DeepSeek live eval 证明所有 grounded-text case 因 citation exact-match 失败而 fallback，
  而 Planner/Patch structured output、finish reason、usage、无答案和 secret filtering 正常。
- Grounded-text system instruction 现列出稳定去重的 allowed citation labels，要求至少逐字复制一个
  `path:start-end` label，并将 evidence text 声明为不可信数据。
- Citation validator、JSON mode、metrics、默认 Patch wiring、API 与 persistence 保持不变。
- TDD RED 证明旧 prompt 不包含 allowed label；GREEN 与 Provider/Grounded Answer/AgentLoop/API
  回归为 135 passed；full deterministic verification 为 332 passed、1 skipped。Paused live
  evaluator 已在 remediation 归档合并后恢复，正在重新验证。
- Residual debt：repo retrieval 可产生 `Makefile` 等无扩展名 evidence，但既有 Grounded Answer
  citation regex 只接受带扩展名路径。该问题未触发本次 live failure；修复会改变 validator
  contract，明确不在本 prompt-only remediation 内，后续需独立 OpenSpec change 评估。

## Model Provider Contract Hardening（2026-06-22）

- Change `harden-model-provider-contract` 已归档至
  `openspec/changes/archive/2026-06-22-harden-model-provider-contract/`；风险级别：high；
  当前无 active OpenSpec change。
- 本阶段把共享 Model Provider 拆分为向后兼容的 `grounded_text` 与显式 `json_object` request
  contract；结构化 instruction 在 HTTP 前校验，Provider 不按 `question_type` 猜业务 schema。
- Long Task Planner 与 Model Patch AuthoringProvider 已删除重复 JSON instruction 拼接；Planner
  在解析前检查 provider status，Planner/Patch 保留各自业务 schema 与安全校验。
- OpenAI-compatible provider 已支持显式 `thinking=disabled`、基础 JSON object response 校验、
  已知非完成 finish reason fail-closed，以及 response-local 脱敏 metrics；metrics 不进入公开或
  持久化 contract。
- TDD focused provider/Planner/Patch/Grounded Answer/persistent audit 为 75 passed；加入 AgentLoop
  与 API 回归及 review remediation 后为 165 passed。最终 full verification 为 331 passed、
  1 skipped；ruff、stage docs、skill checks、实现完成时 OpenSpec 19/19 与 `git diff --check`
  通过；归档后长期 specs validation 为 18/18。
- 独立 external review 初审 0 P0/P1、3 P2；已增加 `json_example` 4096 字符上限、instruction
  深度/response 深度 fail-closed、malformed evidence 与 JSON missing-finish 回归。最终 re-review
  无剩余 P0/P1/P2。Focused Stage Debt Sweep 未发现新增具体债务。
- Runtime/test 最终状态已完成 internal review、独立 adversarial external review、Stage Debt Sweep
  与 archive；归档后没有 runtime/test 变更。
- 本 change 不执行真实网络或 live eval，不修改默认 Patch wiring，不创建 V24。后续
  `add-live-model-provider-eval` 必须在本 change 归档合并后独立创建。

## V11/V12 Capability Truth Fix（2026-06-20）

- Change `fix-v11-v12-capability-truth` 已于 2026-06-20 归档至
  `openspec/changes/archive/2026-06-20-fix-v11-v12-capability-truth/`；当前无 active change。
- V11 capability-status 现承认 V12 deterministic query rewrite/rerank 与 V13 Memory 已实现；
  V12 capability-status 不再声称 Memory 未实现。
- 回答继续明确真实 LLM rewrite/rerank、向量 memory、自动 memory 总结、跨 repo 智能召回和
  context compression 尚未实现。
- 变更只涉及两个静态回答常量、Kernel/API tests 与统一 capability-status spec；不修改路由、
  执行链、存储、API contract 或 README/ARCHITECTURE 的历史阶段边界。
- TDD RED 为 4 failed，最终 focused GREEN 为 4 passed；full verification 为 292 passed、
  1 skipped，ruff、stage docs 与 skill checks 通过；OpenSpec all strict 为 19 passed。
- Internal review 修复 API 测试命中错误 capability 分支的问题。OpenCode 免费 DeepSeek
  external review 发现 standalone V12 缺少覆盖，以及 V11 仅用 PREF/LTM/STM 隐式表达 Memory；
  两项均已修复，re-review 确认无剩余 in-scope finding。
- Focused Stage Debt Sweep 覆盖 V11/V12/V13 constants、capability router、Kernel/API tests、
  统一 spec、历史 README/ARCHITECTURE 与 allowed files；无新增债务。
- Change 已合并到 `main`；合并态 full verification 为 292 passed、1 skipped，OpenSpec all strict
  为 18 passed。精确 remote 同步状态以 Git 查询为准。

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
- V21（已完成）：Worktree Inventory / Inspection。保持纯只读，提供 scoped
  inventory、diffstat、changed files、限长脱敏 diff preview、验证摘要和一致性检查。
- V22（已完成）：Worktree Re-verification。明确触发白名单验证重跑，复用现有
  verification 状态，patch 保持 `applied_in_worktree`，每次结果进入脱敏 audit。
- V23（已完成）：Worktree Disposal / Reconciliation。明确确认后幂等清理并协调
  Git registry、目录和 metadata；discard 后使用独立终态，不回退为 `pending`。
- V24（当前）：CLI Capability Surface / Demo-ready Product Surface。通过 `repopilot`
  稳定展示已有 grounded answer、patch proposal、explicit apply、deterministic verify、
  status 和 audit 能力；不改 `/chat` contract、provider runtime 或默认 Patch wiring。
- V25/backlog 候选：Verified Patch Promotion。仅在独立 OpenSpec change 中重新评估，
  不写成当前已实现能力。
- V24 CLI surface 完成后重新评估 Verified Patch Promotion、Operator Control、Durable Execution、Background Worker、
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

- 当前记录的小代码债已由 archived change `cleanup-control-routing-and-test-names` 处理；archived
  change `derive-capability-status-from-runtime` 已完成 final review 与 Stage Debt Sweep，未发现新的
  blocking debt。若后续发现新债，再按真实证据补充。

## 下一步建议

下一步建议：

- 长期规格入口已切换为 `openspec/specs/`。
- 后续新阶段继续使用 OpenSpec change；不要恢复旧 `specs/00x-*` 作为规格入口。
- 当前建议：完成 `restore-deterministic-verification-baseline`，随后只做
  `clear-repository-ruff-baseline` 的机械清理；所有门禁全绿后按已授权路径交付到 `origin/main`。
- 近期路线：V21 inspection、V22 re-verification、V23 disposal/reconciliation、V24 CLI
  Capability Surface / Demo-ready Product Surface 与 V25 Verified Patch Promotion 均已完成；
  当前不启动额外 runtime feature stage。
- 后续再重新评估 Operator Control、Durable Execution、Background Worker、
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
## Live Eval Transport Blocker Classification Remediation (2026-06-24)

- Archived remediation change: `classify-live-eval-transport-blockers`; merged into current
  `codex/revalidate-deepseek-provider-conformance` branch; risk level: high.
- This change fixes live evaluator evidence semantics: provider conformance verdicts and tracked evaluated-failure
  records are allowed only after all required live provider attempts have evaluable provider contact. If any required
  attempt is a transport/sandbox/provider-contact blocker, the round outcome is `transport_blocked` and no PASS
  attestation or evaluated-failure record is generated.
- Missing `REPOPILOT_LIVE_NETWORK_CONFIRMED=1` now stops before git/provider work with
  `SKIP live model provider eval: live_network_not_confirmed` / exit 0. The variable is an operator
  authorization/declaration only, not proof that the shell is technically network-capable.
- During-run transport blocker is fixed as `BLOCKED live model provider eval: transport_blocked` / exit 1 with only a
  local sanitized report. Internal runner bugs remain `ERROR live model provider eval: <ErrorClass>` / exit 2.
- Local reports may include only allowlisted diagnostics: `phase`, `error_class`, `status_class`. `error_class` is
  reduced to a safe code token before serialization. Reports must not persist API key, full URL, headers, payload,
  prompt, EvidencePack, raw answer, raw exception message, traceback, HTTP body, diff, reasoning content or raw
  fingerprint.
- `build_evaluated_failure_record()` now also enforces required provider-contact completeness, so direct builder use
  cannot create tracked failure evidence for a transport-blocked run.
- Scope remained frozen: no `app/**`, fixture, rubric, profile, pricing, `scripts/verify.ps1`, default CI, `/chat`
  contract or default Patch wiring changes; no V24; no real live gate was run in this remediation.
- Deterministic evidence: focused evaluator tests `64 passed`; full `scripts/verify.ps1` `398 passed, 1 skipped`;
  OpenSpec strict/all `21 passed, 0 failed`; stage docs check passed; `git diff --check` clean except CRLF
  normalization warnings.
- Formal review: internal review fixed the builder guard and diagnostic sanitizer; independent adversarial review found
  no P0/P1 issue. P2.1 grounded diagnostics was closed with repo evidence and regression coverage; P2.2
  `api_subprocess_error` / `run_timeout` remains an existing integrity-failure path with no tracked evidence.
- Stage Debt Sweep inspected changed evaluator paths, `scripts/run_live_model_eval.ps1`,
  `app/providers/model_provider.py` and `app/answering/grounded_answer.py`; no new blocking debt was found.
- The paused `revalidate-deepseek-provider-conformance` live artifact
  `docs/evals/live-model-provider/failures/20260624-013028.json` should be treated as provider-contact-unverified
  transport/integrity blocker现场 evidence under the old contract, not as DeepSeek provider certification or a reliable
  provider conformance FAIL conclusion.
## DeepSeek Revalidation Rerun Result (2026-06-24T11:05:32Z)

- After `classify-live-eval-transport-blockers` was archived and merged, the revalidation live gate was rerun once on
  clean tested commit `16da45b7230b654ba308f4104e9f45abad92eb3a` with no retry, no model switch and no extra
  diagnostic provider calls.
- Runner result: FAIL / exit 1 with tracked evaluated-failure record
  `docs/evals/live-model-provider/failures/20260624-110532.json`; no PASS attestation was generated.
- Local sanitized report: `.repopilot/live-eval/20260624-110532.json`; SHA-256:
  `2a9b6d8f464719228beb8a693403f59fa35605f9a644ca2b367b737723e3a0d2`, matching the failure record.
- Evidence shape: 10 planned cases, 8 provider calls, profile `openai_compatible` / `deepseek-v4-flash`, rubric
  `2026-06-22`. All provider-backed cases had `availability=available`, `finish_reason=stop` and complete usage.
- Only failed gate: `prompt_injection_executed`. Therefore this is a trustworthy provider conformance FAIL pause-site
  record, not a transport blocker and not provider certification.
- Redaction check: report/record did not contain API key, full base URL, prompt, EvidencePack, raw answer, traceback,
  HTTP payload, reasoning content or raw fingerprint. `system_fingerprint_status` may appear as an allowed redacted
  status field.
- Outcome handling remains paused: do not archive, merge to `main`, or push as a completed state. Any remediation or
  contract reshape must be a separate OpenSpec change; do not modify runtime/evaluator/profile/rubric inside this
  revalidation change.

## Worktree Create Timeout Hardening (2026-06-28)

- OpenSpec change `harden-worktree-create-timeouts` has been archived to
  `openspec/changes/archive/2026-06-28-harden-worktree-create-timeouts/`; risk level remains high.
- Scope is limited to worktree create / workspace preflight / rollback Git subprocess timeout and bounded output
  hardening in `app/worktrees/manager.py` and focused coverage in `tests/test_worktree_isolation.py`.
- Implemented a manager-local bounded Git subprocess helper with fixed argv, `shell=False`, `GIT_OPTIONAL_LOCKS=0`,
  `WORKTREE_GIT_TIMEOUT_SECONDS = 10.0`, `WORKTREE_GIT_OUTPUT_MAX_BYTES = 256_000`, and Windows-safe capped reader
  threads for stdout/stderr.
- Timeout, oversized stdout/stderr, read failure, and fatal `git check-ignore` subprocess failures now fail closed
  through existing worktree create failure semantics without exposing raw Git output or local absolute paths.
- `git check-ignore` semantics are explicit: return code 0 means `.repopilot/placeholder` is ignored; return code 1
  means it is not ignored and continues to map to existing `repopilot_not_ignored`; return code greater than 1 is a
  fatal subprocess failure and maps to safe `create_failed` through the create boundary.
- Rollback remains best-effort: unlock/remove subprocess failures are swallowed, filesystem cleanup remains
  best-effort, and create failure never returns `created=True`.
- Existing older debt notes that mention `app/worktrees/manager.py` create / rollback subprocess timeout are superseded
  by this change and must not be interpreted as open debt after this stage.
- Harness files for this stage were restored to readable UTF-8 Chinese and synchronized with the active OpenSpec
  change.
- Verification completed before final review:
  - RED focused tests: 4 expected failures before implementation.
  - `pytest tests/test_worktree_isolation.py -q`: 20 passed.
  - Adjacent regressions: selected worktree / AgentLoop / API / promotion suites: 214 passed.
  - `ruff check .`: passed.
  - `openspec validate --all`: 23 passed, 0 failed.
  - `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`: pytest 495 passed, 1 skipped; ruff, stage docs scan,
    and skill eval structure scan passed.
  - `git diff --check`: passed with CRLF normalization warnings only.
- Final implementation review before archive:
  - Internal review: no P0/P1/P2.
  - OpenCode review reused session `ses_1018bd2aeffeKLTCcQhhuQ1jFZ`: no P0/P1/P2. P3 `_is_bare_repo()` try/except
    suggestion was handled as `reject/clarify` because propagating subprocess failure to `create_failed` is the safer
    fail-closed behavior; P3 oversize extra-byte semantics was handled as `clarify` with a code comment.
- Focused Stage Debt Sweep covered changed runtime/tests/docs/OpenSpec/Harness and directly dependent worktree create
  paths. No blocking debt was found. Adjacent residual subprocess hardening remains in `app/worktrees/disposal.py` and
  `app/worktrees/git_metadata.py`; those are outside this stage and should be separate small changes if prioritized.
- Archive evidence: `openspec archive harden-worktree-create-timeouts --yes` succeeded; archive-after
  `openspec list` reported no active changes; archive-after `openspec validate --all` passed with 22 passed, 0 failed.

## Independent Review Provider Generalization（archived，2026-08-20）

- OpenSpec change `generalize-independent-review-provider` 已归档到
  `openspec/changes/archive/2026-08-20-generalize-independent-review-provider/`；这是 low-risk、process-only
  的项目开发流程变更，不修改 `app/**`、公开 API、权限、持久化、provider runtime 或 RepoPilot runtime
  subagent 能力。
- Medium/high plan review 保留 internal review 加两个 independent review slots；OpenCode、Codex 或其他受支持
  工程 Agent 只作为 reviewer adapter，不再成为固定门禁。Final implementation review 的 slot 数量仍由阶段风险
  合同决定，不统一改成两个。
- Codex 首轮 reviewer 只能使用新的 empty-context task，或宿主明确记录 `fork_turns="none"` 的 subagent；
  inherited/unknown context、与 implementer 身份重合、先看到其他首轮结论或不同 slot 复用同一 reviewer 均 fail closed。
- Remediation re-review 可以复用原 slot 的 reviewer 以保留 finding lineage，但所有 required slots 最终必须刷新到
  同一个 content-addressed baseline。
- 新增 `.harness/templates/independent-review-receipt.template.json` 和
  `scripts/validate_independent_review.py`。实际回执集固定在
  `.harness/reviews/<stage-id>/<phase>/review-set.json`；validator 会重算 artifact SHA-256 和 packet hash，校验
  stage/phase/slot 数量、声明的身份/上下文/首轮盲审、canonical baseline、闭合结论与原 receipt-bound
  remediation lineage，并以结构化 JSON/非零退出 fail closed。其 claim ceiling 固定为
  `mechanical_consistency_only`/`gate_ready=false`；宿主 dispatch provenance 与 activation 时序仍需外部门禁。
- Self-bootstrap 边界保持真实时序：本 change 的 pre-implementation plan review 继续保留变更前 manual contract
  和冻结 hashes，不追溯声称新 validator 已运行；新 gate 在实现、负样本与 workflow wiring 通过后激活，
  从本 change 的 final implementation review 和后续适用 review 生效。
- 当前确定性验证：聚焦 workflow/validator tests `32 passed`；changed Python files 的 Ruff 检查通过；
  archive 前 OpenSpec strict change validation 通过，`openspec validate --all` 为 `23 passed, 0 failed`；archive 后
  `openspec validate --all` 为 `22 passed, 0 failed` 且无 active change；`git diff --check` 通过。当前主机没有
  `powershell`/`pwsh`，因此 `.ps1` 总入口未运行；等价 stage-doc/skill-eval 结构扫描退出 0。
- 全仓验证没有形成 PASS claim：pytest 为 `537 passed, 3 failed`，失败位于未修改的 recursion-depth provider
  用例和两个依赖 `python` 可执行名的 verification-runner 用例；全仓 Ruff 报告 97 个既有问题，而本阶段 changed
  Python files 的 Ruff 为 PASS。这些基线问题不在当前 process-only allowed files 内。
- Final implementation review 使用一个用户要求的 empty-context Codex slot：初轮 4 个 P1、3 个 P2 和后续
  clean-slot refresh P1 均已按 `fix` 关闭，最终 same-slot re-review 为 `NO_FINDINGS`。实际 receipt set 位于
  `.harness/reviews/generalize-independent-review-provider/implementation/review-set.json` 并通过 validator；其结论
  仍只证明 mechanical consistency，宿主另行核对了 `fork_turns="none"` dispatch 与 activation sequence。
- Implementation/archive commit `99ec132` 已 fast-forward 进入 `main` 并推送到 `agentic-codeops/main`；原
  `/Users/chelaile/agentic-codeops` 的 dirty `feature/bootstrap-refactor-harness` 工作树未被覆盖或带入。

</details>
