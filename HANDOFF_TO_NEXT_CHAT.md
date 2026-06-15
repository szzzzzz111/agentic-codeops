# 交接给下一轮 Chat

## V23 Implementation Handoff（2026-06-15）

```text
当前基线：main@27a754a
当前工作分支：main
当前 active OpenSpec change：无
当前阶段：V23 已实现、review、提交、归档并合并，等待下一阶段规划
```

V23 已创建 stage planning、proposal、design、tasks 与 spec deltas，并同步 harness
边界与 feature list。规划锁定四种 exact confirmed disposal/reconciliation 命令，V23 route 位于
inventory/inspection 后、V22 re-verification 前；讨论文本与缺少 confirmation 的请求不会执行或
落入其他路由。

Shared Git metadata runner 的独立 timeout 与读取前硬上限已作为 V23 blocking 工作实现。Reconciliation
只允许安全残缺收尾；path/HEAD/metadata/scope/ownership 不可信时永久 fail closed，禁止
`git worktree prune`、隐式修复和自动重试。Patch store 已新增 true no-create lookup 与 scoped
status update，同时保留 legacy `mark_status`。

内部 plan review 已补强 exact linked-worktree ownership attestation、destructive action 前的
scoped patch existence/status gate、true no-create patch store，以及按实际步骤表达的部分失败终态。
Strict V23 change validation 通过；V23 与相关 V20-V22/patch-store/AgentLoop/API/audit 回归
168 passed；当前未提交工作区 full verify 通过，`pytest` 283 passed, 1 skipped，ruff、stage docs
drift 与 skill eval structure scan 均通过，`openspec validate --all` 18 passed，`git diff --check`
通过。内部 review 已修复审计 related-id、terminal gate、scoped update、控制流回归与
cleanup/store partial-failure 步骤表达。implementation commit 为
`3991d4a Implement V23 worktree disposal reconciliation`；V23 已归档到
`openspec/changes/archive/2026-06-15-v23-worktree-disposal-reconciliation/`，并已以 fast-forward
合并到 `main`。archive 后与 merge 后 stage closeout、full verify 均通过。

## V22 Merge Handoff（2026-06-14）

```text
当前基线分支：main（V22 archive merge 为 6da406b，后续 merge handoff closeout 为 2843dda）
当前工作分支：main
当前 active OpenSpec change：无
当前阶段：V22 Worktree Re-verification 已实现、review、归档、合并并推送
```

V22 只允许用户明确对当前 `user_id + repo_key` scope 中的 retained worktree 重跑现有
`pytest`、`ruff` 或 `verify`。执行前必须 fail closed 核对 metadata scope、expected
directory、Git registry、registry path 与 HEAD/base；任一失败不运行 verification，
不修复、不 reconcile、不 cleanup、不重试，并保留原 lifecycle。

实际 verification 只在 trusted retained worktree execution path 内运行，继续复用
`ToolRegistry`、`PermissionPolicy`、`ApprovalGate`、`ToolExecutor.verification_run`、
timeout、输出限长和脱敏。成功/失败只使用 `verification_succeeded` /
`verification_failed`；patch 始终保持 `applied_in_worktree`。每个识别出的请求尝试写入
一条 related-to-worktree 的脱敏 `verification_result` audit，matching event count 表达
rerun 次数，不新增 schema。

内部 plan review 已补强 malformed/unsafe re-verification-like 请求的路由拒绝语义，
避免其滑落到 standalone verification 或 repo search。规划验证已通过：
`openspec validate v22-worktree-re-verification --strict`、`openspec validate --all`
（17 passed, 0 failed）、`scripts/check_stage_docs.ps1` 与 `git diff --check`。

V22 runtime/tests 已按明确实现确认完成：targeted tests 30 passed，相关 V20/V21/
Verification Runner/audit/AgentLoop/API 回归 158 passed，审查收窄修复后相关回归
115 passed。长期 specs 已同步；`openspec validate --all` 18 passed，默认 full verify
通过，`pytest` 254 passed, 1 skipped，ruff、stage docs drift 与 skill eval gate 均通过。
Initial internal final review 与 Stage Debt Sweep 当时报告未发现剩余阻塞项；该结论已被下方
post-merge 独立复核补充。Implementation commit 为
`30ae5a6 Add V22 worktree re-verification`；change 已归档到
`openspec/changes/archive/2026-06-14-v22-worktree-re-verification/`。Archive 后 OpenSpec
17 passed、stage closeout check 与 full verify 通过。V22 已 fast-forward 合并并推送到
`agentic-codeops/main` at `6da406b`；本地 feature branch fully merged 且保留。

最终 review follow-up 修复了非法但已识别 re-verification attempt 丢失安全 worktree
`related_id` 的审计缺口，并统一了 archive-sync 所需的 worktree-isolation requirement header。

External plan review follow-up 已处理：路由顺序确认满足；新增 lifecycle eligibility
preflight，只允许 `patch_applied`、`verification_failed`、`verification_succeeded`，
并在 Git inspection 前拒绝其他状态。Specs 已明确可区分 answer、mandatory
`attempt_kind` / related worktree audit，以及不入 DB 的 `execution_repo_path` 动态重建方式。

Post-merge 独立 Stage Debt Sweep 发现初次“无剩余阻塞项”结论不完整：malformed Git
registry output 若夹带 expected path，旧 parser 会继续执行 HEAD 检查。当前 remediation
已改为严格解析完整 porcelain record，unknown/malformed field 立即 fail closed，并新增
回归证明不运行第二次 Git 或 verification。同时修正 durable docs 的 stale baseline、
V21 历史 current-branch 措辞、`V10-V22` archive 范围，以及当前主链路遗漏的
`WorktreeManager` / `worktree_create`。非阻塞相邻硬化债为 V21/V22 Git metadata subprocess
尚无独立 timeout，且 metadata output 上限在读取/capture 后判定；后续 worktree hardening
阶段统一处理。

Remediation 验证：新增 RED/GREEN regression 1 passed；V22 targeted 31 passed；相关
V20/V21/V22/Verification Runner/Persistent Audit/AgentLoop/Chat API 回归 161 passed；
`scripts/verify.ps1` 通过，`pytest` 255 passed, 1 skipped；ruff、stage docs drift、
skill eval structure gate、`scripts/check_stage_closeout.ps1` 与 OpenSpec 17/17 均通过。
Remediation commit `454d145 Fix V22 closeout debt` 已 fast-forward 合并并推送到 `main`；
本地 `feature/v22-closeout-debt-remediation` fully merged 且按审计惯例保留。

## V21 Implementation Review Handoff（2026-06-09）

```text
当前基线分支：main
当前工作分支：main
当前 active OpenSpec change：无
当前阶段：V21 Worktree Inventory / Inspection 已合并并推送，等待下一阶段规划
```

V21 已实现 Git-derived preview paths、untracked count-only、bounded safe formatter、
统一 audit wrapper 内事件 skip，以及纯只读 no-create 语义。V20 status 命令继续兼容，
但 request-local event 已由 `worktree_status` 替换为 `worktree_inspection`。

内部实现 review 修复 metadata 路径穿越/revision option 注入、Git 启动失败安全降级、
失败 per-file diff 的部分 preview、不受限 metadata drain、异常超长 diff 单行，以及
`_is_binary_file()` 全文件读取。当前 targeted regression 为 132 passed；implementation
commit 前工作区默认 verify 通过，pytest 为 224 passed, 1 skipped，`openspec validate --all`
为 17 passed, 0 failed。Stage Debt Sweep 未发现未记录阻塞项。

V21 internal final review 已修复 public metadata/tracked-path 摘要未统一限长脱敏、
preview state/DB 路径和空 preview counters、Git/SQLite optional writes，以及
verification/metadata consistency 摘要不完整等 findings；损坏 worktree store 现安全
降级。当前无未解决 internal findings；external review 已完成，用户确认无阻塞
findings。implementation commit 已创建：`ca8e299 Add V21 worktree inventory
inspection`。V21 已归档到
`openspec/changes/archive/2026-06-09-v21-worktree-inventory-inspection/`；当前等待
下一阶段规划。

Archive-after 验证：`openspec list` 为 No active changes found；
`openspec validate --all` 为 16 passed, 0 failed；默认 verify 通过，pytest 为
224 passed, 1 skipped；`scripts/check_stage_closeout.ps1` 与 `git diff --check`
通过。README 同时保留 V20 历史归档 marker 与 V21 最新归档 marker。

`feature/v21-worktree-inventory-inspection` 已 fast-forward 合并到 `main` 并推送到
`agentic-codeops/main` at `60c2dc2a8f7fb73e3f1c5fac90c99c54f3b7d106`；本地
feature branch 按审计惯例保留。Merge 后默认 verify 通过，pytest 为
224 passed, 1 skipped；stage closeout check、OpenSpec all 与 `git diff --check`
通过。

## V20 Archived Handoff（2026-06-07）

```text
当前基线分支：main
当前工作分支：main
当前 active OpenSpec change：无
当前阶段：V20 Worktree Isolation 已实现、提交、归档、合并并推送
```

V20 已实现 `worktree_create -> patch_apply -> optional verification_run` 隔离链路。
patch/verify 使用同一个内部 `execution_repo_path`，主工作区保持不变；standalone
verification 继续使用主工作区。worktree 状态保存在
`.repopilot/worktrees.sqlite3`，支持 `worktree status <worktree_id>` 只读查询，并
写入脱敏 persistent audit。

当前 archive-after 验证证据：V20 worktree targeted 14 passed；全量 `pytest -q`
206 passed, 1 skipped；`openspec validate --all` 15 passed, 0 failed；
`scripts/verify.ps1` 与 `scripts/check_stage_closeout.ps1` 通过；
`git diff --check` 通过。Stage Debt Sweep 已完成，未发现长期 spec 占位债。
内部 final review 已修复 metadata failure rollback、locked worktree unlock/remove、
worktree id collision 保护、README 当前态和 design interface 偏差。external review
已完成，用户确认无阻塞 findings。implementation commit 为
`8be9b37 Add V20 worktree isolation`；archive 路径为
`openspec/changes/archive/2026-06-07-v20-worktree-isolation/`。V20 已 fast-forward
合并到 `main` 并推送到 `agentic-codeops/main` at
`35f9ecc7c1b19a317e5c461a436f7805c09a7743`；merge 后 full verify 与 closeout
gate 均通过。本地 `feature/v20-worktree-isolation` 按审计惯例保留。不要在 V20
增加删除/prune/commit/merge/push/promote/重试能力。

## 当前状态

```text
当前基线分支：main
当前工作分支：main
当前活跃 OpenSpec change：无
最近完成阶段：V20 Worktree Isolation（已实现、提交、归档、合并并推送）
当前阶段：V22 Worktree Re-verification 已实现、归档、合并并推送；等待下一阶段规划
```

RepoPilot 当前定位为面向代码仓库分析任务的可控 Code Agent Harness，不是替代通用 AI IDE 的编程助手。V1-V22 已实现并归档；V22 提供 retained worktree 的明确白名单 re-verification，并保持 patch 与主工作区边界。

后续路线已重排为 lightweight industrial harness：不是企业级平台，也不是玩具 demo；默认使用 SQLite、文件、进程内状态和白名单命令等轻量实现，但逐步交付可确认 patch、受控验证、失败恢复和隔离执行。V18 只实现明确组合确认下的 apply 后 verify，不代表 Persistent Audit / Recovery、worktree、subagents、connectors 或 always-on 已实现。

V20 后的近期后端路线已经过内部复核和外部路线 review，按风险拆为：

1. V21 Worktree Inventory / Inspection：纯只读 inventory、diffstat、changed files、
   限长脱敏 diff preview、验证摘要和一致性检查。
2. V22 Worktree Re-verification：明确触发白名单验证重跑；复用既有 verification
   成功/失败状态，patch 保持 `applied_in_worktree`，每次结果进入脱敏 audit。
3. V23 Worktree Disposal / Reconciliation：明确确认后幂等清理并协调 registry、
   目录与 metadata；discard 后 worktree/patch 使用独立终态，不回退 `pending`。
4. V24 Verified Patch Promotion：仅提升验证成功且内容完整性校验通过的原始受控
   patch；主工作区必须干净且 `HEAD == base_commit`，不直接复制 worktree 文件，
   不自动 commit/push。

V21 的 diff preview 必须有专用安全 formatter 和确定性长度限制，且不得进入
persistent audit。V24 完成后重新评估 Operator Control、Durable Execution、
Background Worker、subagents、connectors、notifications、heartbeat/cron 和
always-on assistant；不提前锁定后续顺序、公开 API 或后台模型。

新增设计判断：RepoPilot adopts a grep-first, RAG-assisted retrieval stance。deterministic lexical/path/symbol search、exact match、文件树和路径线索是代码仓库分析的主要可审计检索基线；embedding/hybrid retrieval、query rewrite 和 rerank 只作为辅助召回或排序通道。V12 Query Rewrite / Rerank 服务于 grep-first baseline，不默认引入 Milvus、Elasticsearch、PgVector、Qdrant、重型 embedding cache 或真实 LLM rewrite/rerank。

V8 已归档到：

```text
openspec/changes/archive/2026-05-20-v8-query-understanding-repo-rag/
```

V9 已归档到：

```text
openspec/changes/archive/2026-05-22-v9-embedding-hybrid-search/
```

V11 已归档到：

```text
openspec/changes/archive/2026-05-26-v11-grounded-answer-model-provider-boundary/
```

V12 已归档到：

```text
openspec/changes/archive/2026-05-27-v12-query-rewrite-rerank/
```

V13 已归档到：

```text
openspec/changes/archive/2026-05-28-v13-memory/
```

V14 已归档到：

```text
openspec/changes/archive/2026-05-30-v14-long-task-react-subagents/
```

V15 已归档到：

```text
openspec/changes/archive/2026-05-31-v15-assistant-control-surface/
```

V16 已归档到：

```text
openspec/changes/archive/2026-05-31-v16-safe-patch-authoring/
```

## 当前主链路

```text
API -> ChatService(trace_id) -> CodeAgent -> AgentLoop
  -> MemoryManager(STM/PREF/LTM command/read audit)
  -> LongTaskManager(command/status/step audit)
  -> AssistantControlSurface(read-only status)
  -> PatchManager(proposal/apply confirmation)
  -> WorktreeManager(scoped create / inventory / inspection / re-verification preflight)
  -> PatchVerifyLoop(explicit apply+verify confirmation)
  -> VerificationRunner(whitelisted pytest/ruff/verify)
  -> AuditManager(persistent redacted audit / read-only recovery)
  -> QueryUnderstanding/SearchPlan -> QueryRewriteProvider
  -> ToolRegistry -> PermissionPolicy -> ApprovalGate
  -> ToolExecutor(repo_rag / worktree_create / patch_apply / verification_run) -> HybridRepoRetriever -> Reranker -> EvidencePack/ContextBudget
     -> GroundedAnswerGenerator -> ModelProvider
     -> LexicalRepoRetriever + EmbeddingRepoRetriever -> file_tools
```

`/chat` 顶层响应保持现有 contract：`trace_id`、`answer`、`related_files`、`tool_calls`。V7 的权限和审批审计、V8/V9 的 query understanding/retrieval 摘要、V10 的 Evidence Pack audit summary、V11 的 provider audit summary、V12 的 rewrite/rerank audit summary、V13 的 memory audit summary、V14 的 long task / ReAct 摘要、V15 的 Assistant Control Surface 摘要和 V16 的 patch audit 摘要只保留在内部 trace 或现有 `answer`，不作为 `/chat` 顶层字段暴露。

## V16 实现摘要

- OpenSpec change 已归档到 `openspec/changes/archive/2026-05-31-v16-safe-patch-authoring/`，包含 proposal、design、tasks，以及 `safe-patch-authoring` / `agent-loop-tool-execution` / `chat-api` / `harness-development-workflow` spec delta。
- 已同步长期 specs，新增 `openspec/specs/safe-patch-authoring/spec.md`；V16 当时的 `.harness/allowed_files.md` 和 `.harness/review_checklist.md` 已在归档后切回暂无 active stage。
- 新增 `app/patching/`：
  - `parser.py`：明确 patch proposal intent 和 `确认/应用/apply/confirm patch <patch_id>` 确认语法。
  - `provider.py`：Patch Authoring provider 边界，默认 fake provider 不生成真实 diff，ModelProvider wrapper 可解析结构化 JSON diff。
  - `store.py`：repo-local `.repopilot/patches.sqlite3` pending patch store，按 `user_id + repo_key` 隔离，默认 24 小时 TTL。
  - `apply.py`：unified diff parser/applicator，全量 preflight、repo 内相对路径、安全文件、二进制和 context 校验。
  - `manager.py`：proposal、apply confirmation、`ToolInvocationContext` 预校验和状态更新。
- 新增 `ToolInvocationContext`，`PermissionPolicy.decide(..., context=None)` 和 `ApprovalGate.evaluate(..., context=None)` 保持可选 context；权限状态仍只有 `allow`、`deny`、`ask`。
- `patch_apply` 注册为 `read_only=False`、`risk=write`、`requires_approval=True`；只有有效确认上下文才能 `ask -> ApprovalGate pass`。
- `ToolExecutor.patch_apply(...)` 是 V16 唯一写入路径；普通 API handler 不直接写文件。
- AgentLoop 前置顺序为 Memory command、Long Task command、Assistant Control Surface、Patch command / Patch intent、capability-status、repo_search/chat_only。
- V16 不运行测试、不自动 commit、不创建 worktree、不执行 shell、不实现 Verification Runner 或 Patch + Verify Loop。
- 当前验证：
  - `openspec validate v16-safe-patch-authoring`：通过。
  - V16 targeted RED：缺少 `ToolInvocationContext` 和 patching runtime，按预期失败。
  - V16 targeted GREEN：`pytest tests\test_patch_authoring.py tests\test_agent_harness_kernel.py::test_permission_policy_allows_patch_apply_only_via_confirmation_context tests\test_agent_harness_kernel.py::test_agent_loop_handles_patch_confirm_before_repo_search tests\test_agent_harness_kernel.py::test_agent_loop_reports_v16_patch_capability_without_repo_search tests\test_chat_api.py::test_chat_endpoint_patch_proposal_keeps_contract_and_does_not_write tests\test_chat_api.py::test_chat_endpoint_confirm_patch_applies_without_running_verification -q`：11 passed。
  - V16 相关回归：`pytest tests\test_patch_authoring.py tests\test_agent_harness_kernel.py tests\test_chat_api.py -q`：72 passed。
  - V16 self-review follow-up：已补 provider unsafe diff 不得创建 pending patch 测试，并把 unified diff 只读 preflight 前移到 pending patch 创建前；`pytest tests\test_patch_authoring.py -q`：7 passed；`pytest tests\test_patch_authoring.py tests\test_agent_harness_kernel.py tests\test_chat_api.py -q`：73 passed。
  - V16 external review follow-up：已补 provider summary 本机绝对路径不得进入 `/chat.answer` 的回归测试；patch proposal answer 公开展示前会对 summary 做路径脱敏；复核 `__pycache__` / `.pyc` 未被 git 跟踪且已被 `.gitignore` 忽略，并清理本地 `app\patching\__pycache__`、`app\providers\__pycache__`。
  - V16 external review follow-up targeted 验证：`pytest tests\test_patch_authoring.py -q`：8 passed。
  - V16 external review follow-up 相关回归：`pytest tests\test_patch_authoring.py tests\test_agent_harness_kernel.py tests\test_chat_api.py -q`：74 passed。
  - V16 final stage debt sweep：已复核 active OpenSpec、harness、README、ARCHITECTURE、PROGRESS、FEATURE_LIST、HANDOFF 和长期 specs；修正 handoff 中残留的旧 “no active change” harness 状态，并补齐 V15 `assistant-control-surface` 长期 spec Purpose；未发现新的阶段内 P0/P1/P2。
  - V16 OpenSpec 全量验证：`openspec validate --all`：11 passed, 0 failed。
  - V16 默认验证：`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 158 passed, 1 skipped；`ruff check .` All checks passed；stage docs drift scan 无漂移。
  - V16 diff 验证：`git diff --check`：通过，仅有 CRLF 换行提示。
  - V16 implementation commit：`d32a367 Add V16 safe patch authoring`。
  - V16 archive：`openspec archive v16-safe-patch-authoring -y` 已完成，归档到 `openspec/changes/archive/2026-05-31-v16-safe-patch-authoring/`；长期 specs 已同步，新增 `openspec/specs/safe-patch-authoring/spec.md`。
  - V16 archive 后验证：`openspec validate --all`：11 passed, 0 failed；`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过，`pytest` 158 passed, 1 skipped，`ruff check .` All checks passed，stage docs drift scan 无漂移；`powershell -ExecutionPolicy Bypass -File scripts\check_stage_closeout.ps1`：通过。
  - V16 merge：已 fast-forward 合并 `feature/v16-safe-patch-authoring` 到 `main`；merge 后 `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1` 通过，`pytest` 158 passed, 1 skipped，`ruff check .` All checks passed；`powershell -ExecutionPolicy Bypass -File scripts\check_stage_closeout.ps1` 通过。

## V15 当前实现摘要

- OpenSpec change 已归档到 `openspec/changes/archive/2026-05-31-v15-assistant-control-surface/`，包含 proposal、design、tasks，以及 `assistant-control-surface` / `agent-loop-tool-execution` / `chat-api` / `memory` / `long-task-agent-execution` / `harness-development-workflow` spec delta。
- 长期 specs 已同步，新增 `openspec/specs/assistant-control-surface/spec.md`。
- V15 implementation commit：`86d175a Add V15 assistant control surface`。
- V15 archive 当时已完成；该历史段落保留阶段背景，不表示当前分支状态。
- 新增 `app/assistant/control_surface.py`：明确触发词、只读状态聚合和 answer formatter。
- `AgentLoop` 前置顺序为 Memory command、Long Task command、Assistant Control Surface、capability-status、repo_search/chat_only。
- Memory / Long Task 增加只读 control surface summary；不存在 `.repopilot` DB 时返回空状态，不创建目录或 DB。
- V15 不新增 API，不新增 `/chat` 顶层字段，不调用 `repo_rag`，不写 memory，不创建任务，不执行 shell，不后台运行。
- 当前 targeted TDD 验证：`pytest tests/test_assistant_control_surface.py tests/test_agent_harness_kernel.py::test_agent_loop_answers_assistant_status_without_repo_rag tests/test_agent_harness_kernel.py::test_agent_loop_memory_command_still_precedes_assistant_status tests/test_agent_harness_kernel.py::test_agent_loop_long_task_command_still_precedes_assistant_status tests/test_chat_api.py::test_chat_endpoint_assistant_status_keeps_contract_and_does_not_create_state -q`：11 passed。
- OpenSpec / 默认验证记录：`openspec validate v15-assistant-control-surface` 通过；`openspec validate --all`：10 passed, 0 failed；`powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`：通过，`pytest` 144 passed, 1 skipped，`ruff check .` All checks passed，stage docs drift scan 无漂移；`git diff --check` 通过，仅有 CRLF 换行提示。
- V15 external review follow-up：已补测试并修复 Assistant Control Surface Long Task 摘要中 task title / next step title 的本机绝对路径脱敏；`pytest tests/test_assistant_control_surface.py::test_status_answer_redacts_absolute_paths_from_recent_long_tasks -q`：1 passed；V15 targeted 相关验证：11 passed；`openspec validate v15-assistant-control-surface` 通过；`openspec validate --all`：10 passed, 0 failed；`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过，`pytest` 145 passed, 1 skipped，`ruff check .` All checks passed，stage docs drift scan 无漂移；`git diff --check` 通过，仅有 CRLF 换行提示；阶段文档已补齐 4.2-4.5 验证记录，`openspec/changes/v15-assistant-control-surface/tasks.md` 完成状态保留。
- V15 external review close：用户确认外部 review 没问题；final stage debt sweep 已执行，未发现新的 P0/P1/P2 或需记录的阶段内剩余债务。
- V15 archive：`openspec archive v15-assistant-control-surface -y` 已完成，长期 specs 已同步，`openspec list` 显示 no active changes。
- V15 archive 后验证：`openspec validate --all`：10 passed, 0 failed；`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过，`pytest` 145 passed, 1 skipped，`ruff check .` All checks passed，stage docs drift scan 无漂移；`powershell -ExecutionPolicy Bypass -File scripts\check_stage_closeout.ps1`：通过；`git diff --check`：通过，仅有 CRLF 换行提示。

## V14 当前实现摘要

- OpenSpec change 已归档到 `openspec/changes/archive/2026-05-30-v14-long-task-react-subagents/`，包含 proposal、design、tasks 和 `long-task-agent-execution` / `agent-loop-tool-execution` / `chat-api` / `harness-development-workflow` spec delta。
- 长期 specs 已同步，新增 `openspec/specs/long-task-agent-execution/spec.md`。
- V14 archive 后 `.harness/allowed_files.md` 和 `.harness/review_checklist.md` 曾切回暂无 active stage；V15 archive 后当时也已切回暂无 active stage。
- 新增 `app/longtask/`：
  - `parser.py`：解析明确长任务自然语言指令。
  - `planner.py`：deterministic task-type templates，并支持显式真实 provider 的受控 JSON 增强和 fallback。
  - `store.py`：repo-local `.repopilot/tasks.sqlite3`，复用 V13 repo_key 规范化规则。
  - `manager.py`：create/list/status/pause/resume/supplement/reopen/archive、quota 和状态流转。
- `AgentLoop` 已在 `RequestRouter` 前处理 Memory command 和 Long Task 指令，顺序为 Memory command 先识别、Long Task command 后识别；控制命令不调用 `repo_rag`，显式 resume/run 通过 `ToolRegistry -> PermissionPolicy -> ApprovalGate -> ToolExecutor(repo_rag)` 推进一个 step。
- Long Task 使用 `paused/running/blocked/completed/failed` 状态，`archived` 是标记；`completed` 只读，`failed` 可 reopen for retry。
- V14 不新增 `/tasks` API，不新增 `/chat` 必需顶层字段，不执行后台任务、不自动循环、不创建 worktree、不调度真实 subagents、不执行 shell、不自动修改代码。
- 当前验证：
  - `openspec validate v14-long-task-react-subagents`：通过。
  - TDD RED：`pytest tests\test_long_task.py tests\test_agent_harness_kernel.py::test_agent_loop_handles_long_task_command_before_router_keyword tests\test_chat_api.py::test_chat_endpoint_long_task_create_keeps_contract_and_does_not_search -q`：预期失败，缺少 `app.longtask`。
  - V14 目标验证：`pytest tests\test_long_task.py tests\test_agent_harness_kernel.py::test_agent_loop_handles_long_task_command_before_router_keyword tests\test_agent_harness_kernel.py::test_agent_loop_resumes_one_long_task_step_through_repo_rag tests\test_agent_harness_kernel.py::test_agent_loop_blocks_long_task_when_resume_has_no_results tests\test_chat_api.py::test_chat_endpoint_long_task_create_keeps_contract_and_does_not_search tests\test_chat_api.py::test_chat_endpoint_long_task_resume_returns_repo_rag_tool_call -q`：9 passed。
  - V14 相关集成：`pytest tests\test_long_task.py tests\test_agent_harness_kernel.py tests\test_chat_api.py -q`：60 passed。
  - V14 self-review follow-up：直接 `task_id` 访问补充 `user_id + repo_key` 隔离；新增测试先失败后修复。
  - V14 follow-up 相关验证：`pytest tests\test_long_task.py::test_manager_rejects_cross_user_task_id_access tests\test_long_task.py tests\test_agent_harness_kernel.py tests\test_chat_api.py -q`：62 passed。
  - V14 review follow-up RED：completion 阶段跨用户隔离与 provider JSON planning schema 测试先失败，分别暴露缺少 scoped completion 和 provider prompt 协议不足。
  - V14 review follow-up 修复：`complete_tool_action` 增加 `user_id + repo_key` 作用域校验；provider planning prompt 明确 JSON-only schema 和不可改变 step/action 边界。
  - V14 review follow-up targeted 验证：`pytest tests\test_long_task.py::test_planner_sends_json_schema_prompt_for_provider_enhancement tests\test_long_task.py::test_manager_rejects_cross_user_tool_completion -q`：2 passed。
  - V14 review follow-up 相关验证：`pytest tests\test_long_task.py tests\test_agent_harness_kernel.py tests\test_chat_api.py -q`：63 passed。
  - V14 review follow-up lint：`ruff check app\longtask app\harness\kernel.py tests\test_long_task.py tests\test_agent_harness_kernel.py tests\test_chat_api.py`：All checks passed。
  - V14 OpenSpec change 验证：`openspec validate v14-long-task-react-subagents`：通过。
  - V14 review follow-up 默认验证：`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 132 passed, 1 skipped；`ruff check .` All checks passed；stage docs drift scan 无漂移。
  - V14 review follow-up OpenSpec 全量验证：`openspec validate --all`：9 passed, 0 failed。
  - V14 external review triage：修复 Memory/Long Task 前置顺序、Long Task result summary 绝对路径脱敏，并清理 `app/longtask/__pycache__` 生成物；新增 targeted tests 先失败后修复。
  - V14 external review targeted 验证：`pytest tests\test_agent_harness_kernel.py::test_agent_loop_handles_memory_command_before_router_and_long_task tests\test_agent_harness_kernel.py::test_agent_loop_memory_command_confirms_without_repo_rag tests\test_long_task.py::test_manager_tool_completion_summary_redacts_absolute_paths -q`：3 passed。
  - V14 external review 相关验证：`pytest tests\test_long_task.py tests\test_agent_harness_kernel.py tests\test_chat_api.py -q`：65 passed。
  - V14 external review OpenSpec 验证：`openspec validate v14-long-task-react-subagents` 通过；`openspec validate --all`：9 passed, 0 failed。
  - V14 external review 默认验证：`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 134 passed, 1 skipped；`ruff check .` All checks passed；stage docs drift scan 无漂移。
  - V14 external review close：外部 review 确认无新增 P0/P1/P2；剩余 P3 `app/longtask/__pycache__` 已复核，文件系统和 git tracked files 均无 pyc。
  - Implementation commit：`ed48fa9 Add V14 long task control plane`。
  - Merge/push：已 fast-forward 合并到 `main` 并推送到 `agentic-codeops/main`。
  - Archive：`openspec archive v14-long-task-react-subagents -y` 已完成，长期 specs 已同步。
  - Archive 后 `openspec validate --all`：9 passed, 0 failed。
  - Archive 后默认验证：`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 134 passed, 1 skipped；`ruff check .` All checks passed；stage docs drift scan 无漂移。
  - Archive closeout：`powershell -ExecutionPolicy Bypass -File scripts\check_stage_closeout.ps1`：通过；包含 no active changes、OpenSpec 全量验证、stage docs drift scan 和 `git diff --check`。
  - `ruff check app\longtask app\harness\kernel.py tests\test_long_task.py tests\test_agent_harness_kernel.py tests\test_chat_api.py`：All checks passed。
  - `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 130 passed, 1 skipped；`ruff check .` All checks passed；stage docs drift scan 无漂移。
  - `git diff --check`：通过，仅有 CRLF 换行提示。

## V13 实现摘要

- 新增 `app/memory/store.py`，提供 `SQLiteMemoryStore`、`InMemorySessionMemoryStore`、`compute_repo_key` 和 repo path normalization。
- 新增 `app/memory/manager.py`，提供明确 memory 指令解析、记住/忘记、普通请求 memory summary 和脱敏 audit。
- `ChatService -> CodeAgent -> AgentLoopRequest` 已传入 `user_id` 和 `session_id`。
- V14 external review follow-up 后，`AgentLoop` 在 route 前处理 memory command；命中后返回确认，不执行 `repo_rag`。
- 普通 repo_search 在权限通过后记录 `memory_summarized`，memory read failure 不阻断检索。
- `.gitignore` 已加入 `.repopilot/`，repo-local SQLite DB 被视为本地状态。
- Implementation commit：`1b5696d Add V13 memory`。
- Archive：`openspec archive v13-memory --skip-specs -y` 已完成；长期 specs 已在 archive 前同步。
- 当前验证：
  - `openspec validate v13-memory`：通过。
  - `pytest tests\test_memory.py -q`：5 passed。
  - `pytest tests\test_memory.py tests\test_agent_harness_kernel.py tests\test_chat_api.py -q`：57 passed。
  - `openspec validate --all`：9 passed, 0 failed。
  - `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 120 passed, 1 skipped；`ruff check .` All checks passed；stage docs drift scan 无漂移。
  - `git diff --check`：通过，仅有 CRLF 换行提示。
  - Archive 后 `openspec list`：No active changes found。
  - Archive 后 `openspec validate --all`：8 passed, 0 failed。
  - Archive closeout：`powershell -ExecutionPolicy Bypass -File scripts/check_stage_closeout.ps1`：通过。
  - Archive 后默认验证：`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 120 passed, 1 skipped；`ruff check .` All checks passed；stage docs drift scan 无漂移。

## V12 实现摘要

- 新增 `app/rag/query_rewrite.py`，提供 `QueryRewriteProvider` 边界、`QueryRewriteResult`、`QueryVariant` 和默认 deterministic Code Evidence variants。
- 新增 `app/rag/rerank.py`，提供 before-Evidence deterministic rerank 边界和 fallback。
- `ToolExecutor.search_repo_rag` 对 rewrite variants 执行 bounded multi-query retrieval，合并去重后 rerank，再构建 Evidence Pack；original variant 为空时不跳过 rewrite-only variants。
- `HybridRepoRetriever` 对包含 `symbols` 或 `path_hints` 的查询保持 lexical anchor，避免 rewrite 模板词产生 embedding-only 误召回。
- `AgentLoop` 记录 `query_rewrite_summarized` 和 `rerank_summarized` 内部 trace；`/chat.tool_calls` 不暴露完整 variants、完整 retrieval results 或完整 Evidence Pack。
- V12 保持 Evidence Pack budget/summary 和 grounded answer citation validation 语义不变。
- Implementation commit：`aaddad2 Add V12 query rewrite rerank`。
- Review follow-up commit：`4553b11 Fix V12 review follow-ups`。
- Archive：`openspec archive v12-query-rewrite-rerank --skip-specs -y` 已完成；长期 specs 已在 archive 前同步。
- 当前验证：
  - `openspec validate v12-query-rewrite-rerank`：通过。
  - `pytest tests\test_query_rewrite.py tests\test_repo_rerank.py tests\test_agent_harness_kernel.py -q`：41 passed。
  - `pytest tests\test_query_rewrite.py tests\test_repo_rerank.py tests\test_repo_rag.py tests\test_agent_harness_kernel.py tests\test_chat_api.py tests\test_evidence_pack.py tests\test_grounded_answer.py -q`：72 passed。
  - `openspec validate --all`：8 passed, 0 failed。
  - `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 104 passed, 1 skipped；`ruff check .` All checks passed；stage docs drift scan 无漂移。
  - `git diff --check`：通过，仅有 CRLF 换行提示。
- V12 外部 review follow-up：
  - 已修正 original variant 为空时跳过 rewrite-only variants 的召回问题。
  - 已将 variant 去重改为按 `query_text`、`keywords`、`symbols`、`path_hints` 分字段归一化。
  - 已为 symbol/path 查询加入 lexical anchor，避免 rewrite 模板词产生 embedding-only 误召回。
  - `pytest tests/test_chat_api.py::test_chat_endpoint_returns_empty_related_files_when_keyword_is_missing tests/test_repo_rag.py tests/test_query_rewrite.py tests/test_tool_executor.py tests/test_repo_rerank.py -q`：19 passed。
  - `openspec validate v12-query-rewrite-rerank`：通过。
  - `openspec validate --all`：8 passed, 0 failed。
  - `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 108 passed, 1 skipped；`ruff check .` All checks passed；stage docs drift scan 无漂移。
- V12 archive closeout：
  - `openspec list`：No active changes found。
  - `openspec validate --all`：7 passed, 0 failed。
  - `powershell -ExecutionPolicy Bypass -File scripts/check_stage_closeout.ps1`：通过。
  - `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 108 passed, 1 skipped；`ruff check .` All checks passed；stage docs drift scan 无漂移。
  - `git diff --check`：通过，仅有 CRLF 换行提示。

## V11 实现摘要

- 新增 `app/providers/model_provider.py`，提供 `ModelProvider` 边界、deterministic `FakeModelProvider`、`OpenAICompatibleModelProvider` 和环境变量 provider factory。
- 新增 `app/answering/grounded_answer.py`，提供 grounded answer、citation validation、fallback 和 provider audit 汇总。
- `AgentLoop` 在 successful `repo_rag` 且存在 Evidence Pack 后调用 `GroundedAnswerGenerator`；工具错误仍沿用原有失败回答。
- citation 格式为 `relative/path.py:start-end`；无合法 citation、越界 citation、provider error、timeout 或 invalid response 均降级为保守 fallback。
- 默认 provider 为 fake，默认验证不需要网络、API key 或真实模型输出。
- OpenAI-compatible provider 使用运行时依赖 `httpx`，通过 `REPOPILOT_MODEL_PROVIDER=openai_compatible`、`REPOPILOT_MODEL_BASE_URL`、`REPOPILOT_MODEL_API_KEY`、`REPOPILOT_MODEL_NAME` 显式启用。
- provider audit 不进入 `/chat` 顶层字段或 `tool_calls`，且不记录完整 prompt、完整模型输出、完整 Evidence Pack 或 API key。
- V11 仍不实现 query rewrite、rerank、memory、context compression、SandboxRunner、skill execution 或多 agent orchestration。
- 当前验证：
  - `openspec validate v11-grounded-answer-model-provider-boundary`：通过。
  - `pytest tests\test_model_provider.py tests\test_grounded_answer.py tests\test_agent_harness_kernel.py tests\test_chat_api.py`：54 passed。
  - `openspec validate --all`：8 passed, 0 failed。
  - `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 97 passed, 1 skipped；`ruff check .` All checks passed。
  - `git diff --check`：通过，仅有 CRLF 换行提示。
- Archive：`openspec archive v11-grounded-answer-model-provider-boundary --skip-specs -y` 已完成；长期 specs 已在 archive 前同步。
- Archive 后验证：`openspec validate --all`：7 passed, 0 failed；`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 97 passed, 1 skipped；`ruff check .` All checks passed；`git diff --check`：通过，仅有 CRLF 换行提示。
- 外部 review follow-up：
  - 已确认 `httpx>=0.27.0` 位于 `[project].dependencies`，并在 PROGRESS 中补充运行时依赖变更记录。
  - 已修正 citation 校验 allowed 集合，使其只接受实际传给 provider 的 included 且非空 snippet evidence。
  - `pytest tests\test_grounded_answer.py`：9 passed。

## LLMGateway 设计备忘

用户补充的 LLMGateway 概念应作为后续真实模型调用增强参考，但不要写成当前 runtime 已实现能力。当前项目只有 V11 Model Provider Boundary：统一 provider 接口、fake/openai-compatible provider、环境变量配置、基础 timeout、provider error fallback、citation validation 和脱敏 audit。

后续对 RepoPilot 有价值的轻量方向：

- 继续把真实模型调用收口在 `ModelProvider` / `GroundedAnswerGenerator`，避免散落 HTTP 调用。
- 保持 API key、prompt、模型输出、Evidence Pack 的脱敏边界。
- 在需要时加入小次数 retry、latency/token/cost 摘要和简单 provider/model routing。
- JavaGuide LLM API 工程实践（`https://javaguide.cn/ai/llm-basis/llm-api-engineering.html`）可作为 V16+ 规划参考：重点吸收流式输出取消/超时、结构化返回 schema/fallback、request/attempt id、重试幂等、解析失败率和 provider audit 摘要；不要照搬企业级网关。
- 不提前实现工业级限流、熔断集群、多租户成本账单、供应商竞价或控制台。

这个备忘适合后续单独 `llm-gateway-lite` change 或真实模型调用增强规划时参考。

## 已完成阶段摘要

### V7：Permission + Approval Gate

- 已提交：`7f1fc86 Add V7 permission approval gate`
- 已合并到 `main`：`Merge V7 permission approval gate`
- 已归档到：`openspec/changes/archive/2026-05-19-v7-permission-approval-gate/`
- 已实现 `ToolSpec.requires_approval`、`PermissionDecision`、`PermissionPolicy` 和最小 `ApprovalGate`。
- 权限优先级：未注册、非只读或非 `low` 风险 -> `deny`；否则 `requires_approval=True` -> `ask`；否则 -> `allow`。
- `deny` 和 `ask` 分支不调用 executor，`related_files=[]` 且 `tool_calls=[]`。

### V8：Query Understanding + Lexical Repo RAG

- 已提交：`2ab1316 Add V8 query understanding repo RAG`
- 已合并到 `main`：`cef8115 Merge V8 query understanding repo RAG`
- 已归档：`eff51c3 Archive V8 query understanding repo RAG`
- 已新增 deterministic `QueryUnderstanding/SearchPlan`。
- 已新增 repo-local lexical RAG：repo chunk、lexical scoring、dedup 和 citation。
- 已将 `/chat` 的 repo_search 分支从简单 `search_code` 搜索升级为 V8 的 `ToolExecutor(repo_rag) -> LexicalRepoRetriever`；后续 V9 已进一步升级为 `HybridRepoRetriever`，当前 V10 在此基础上加入 Evidence Pack / Context Budget。
- 已同步长期 specs：
  - `openspec/specs/agent-loop-tool-execution/spec.md`
  - `openspec/specs/repo-query-understanding-rag/spec.md`

V8 不实现 embedding、Milvus、Elasticsearch、PgVector、Qdrant、LLM rewrite、rerank、memory、SandboxRunner、skill execution 或多 agent orchestration。

### V9：Embedding Retrieval + Hybrid Search

- 已提交：
  - `61a7963 Add V9 embedding hybrid search`
  - `24d4d6e Fix V9 review follow-ups`
  - `d31e83e Document V9 implementation review recovery`
  - `9479a0c Address final V9 review findings`
  - `e5e5fa0 Archive V9 embedding hybrid search`
- 已归档到：`openspec/changes/archive/2026-05-22-v9-embedding-hybrid-search/`
- 已实现 `DeterministicEmbeddingProvider`、`EmbeddingRepoRetriever`、`HybridRepoRetriever` 和 deterministic `hybrid_fuse`。
- 默认 embedding provider 是本地确定性实现，不调用网络、密钥、模型下载或外部服务。
- `ToolExecutor(repo_rag)` 和 `AgentLoop` 默认使用 `retrieval_mode=hybrid`，同时保留 lexical retrieval 作为一等通道。
- 内部 trace 记录 hybrid channel audit summary，包括 lexical、embedding、fused 结果数和 `min_fused_score`；该摘要不作为 `/chat` 顶层字段暴露。
- V9 不默认引入 Milvus、Elasticsearch、PgVector、Qdrant、真实外部 embedding 服务、模型下载、LLM rewrite、rerank、memory 或 context compression。

## 当前 Harness 状态

- 当前 active change：无。
- `.harness/allowed_files.md` 当前开放 V19 Persistent Audit / Recovery 写入边界；runtime scope 限定为 persistent audit store、AgentLoop audit/recovery hook、测试和 durable docs。
- `.harness/review_checklist.md` 当前加入 V19 audit/recovery gates、Stage Debt Sweep evidence gate、post-merge durable docs gate 和 branch retention gate。
- V18 OpenSpec change 已归档到 `openspec/changes/archive/2026-06-04-v18-patch-verify-loop/`，长期 specs 已同步，新增 `openspec/specs/patch-verify-loop/spec.md`。
- V18 runtime 新增组合确认解析、verification label parser、AgentLoop Patch + Verify Loop 编排；组合确认必须完整解析 patch id 和 verification label，非法组合请求整体拒绝且不 apply。
- V18 targeted RED 已确认缺少 `parse_patch_verify_confirmation` 和 `parse_verification_label`；targeted GREEN 8 passed；相关回归 `pytest tests/test_patch_authoring.py tests/test_verification_runner.py tests/test_agent_harness_kernel.py tests/test_chat_api.py -q`：94 passed；`openspec validate --all`：13 passed；默认 `scripts/verify.ps1` 通过，`pytest` 178 passed, 1 skipped，`ruff check .` All checks passed。
- V18 外部 review 已处理并确认无阻塞：spec delta 文件实际存在；README 和 HANDOFF 当前链路已补齐 `PatchManager -> PatchVerifyLoop -> VerificationRunner`。
- V18 implementation commit：`e76807d Add V18 patch verify loop`。
- V18 archive：`openspec archive v18-patch-verify-loop -y` 已完成。
- V18 archive 后验证：`openspec validate --all` 13 passed；`powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` 通过，`pytest` 178 passed, 1 skipped，`ruff check .` All checks passed，stage docs drift scan 无漂移；`powershell -ExecutionPolicy Bypass -File scripts/check_stage_closeout.ps1` 通过。
- V18 archive merge/push：当时 `main`、`agentic-codeops/main` 和本地 `feature/v18-patch-verify-loop` 均指向 `3c7a8b3955bbcb0848ad56f0b074c70d1a506107`（`Archive V18 patch verify loop`），确认 V18 archive 已进入远端主线；该记录随后由 V18 closeout debt remediation commit `8b93330` supersede，当前真实 V19 基线为 `8b93330`。
- V18 post-merge/handoff audit 发现并修复的流程债：durable docs 残留 archive/merge 前状态；`patch-verify-loop`、`verification-runner` 和 `safe-patch-authoring` 长期 specs 残留 archive 自动生成 Purpose；`scripts/check_stage_docs.ps1` 未拦截这些问题。当前 remediation 已补齐 Purpose、同步 main/remote 状态、强化 docs drift scan，并清理本地未跟踪 `__pycache__` 生成目录。
- Branch retention：本地 `feature/v18-patch-verify-loop` 已 fully merged 且与 `main` 同 hash；按本仓库历史惯例暂保留，不自动删除。后续若要清理分支，应单独执行并记录。
- V18 closeout debt remediation 验证：`openspec validate --all` 13 passed, 0 failed；`powershell -ExecutionPolicy Bypass -File scripts/check_stage_docs.ps1` 通过，扫描 23 个文件；`powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` 通过，`pytest` 178 passed, 1 skipped，`ruff check .` All checks passed，stage docs drift scan 无漂移；`git diff --check` 通过，仅有 CRLF 换行提示。
- V18 closeout debt remediation commit/merge/push：`8b93330 chore: close v18 post-merge debt` 已 fast-forward 合并到 `main` 并推送到 `agentic-codeops/main`；V18 closeout debt branch 按审计惯例保留，不在 V19 中自动删除。
- V19 OpenSpec/harness：已创建 `openspec/changes/v19-persistent-audit-recovery/`，新增长期 `openspec/specs/persistent-audit-recovery/spec.md`，并同步 `.harness/allowed_files.md` 与 `.harness/review_checklist.md` 到 V19 边界；`openspec validate v19-persistent-audit-recovery --strict` 通过，`openspec validate --all` 15 passed, 0 failed。
- V19 targeted implementation 验证：`pytest tests/test_persistent_audit.py -q`：9 passed；`pytest tests/test_agent_harness_kernel.py tests/test_chat_api.py tests/test_persistent_audit.py -q`：85 passed；`ruff check app/audit app/harness/kernel.py tests/test_persistent_audit.py tests/test_agent_harness_kernel.py tests/test_chat_api.py`：All checks passed。
- V19 full verification：`powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` 通过，`pytest` 187 passed, 1 skipped，`ruff check .` All checks passed，stage docs drift scan 无漂移；`openspec validate --all` 15 passed, 0 failed；`git diff --check` 通过，仅有 CRLF 换行提示。
- V19 Stage Debt Sweep：已扫描 current docs、harness docs、active OpenSpec、long-term specs、changed runtime paths 和 adjacent older runtime paths；修复额外发现的 `docs/FEATURE_LIST.json` JSON 结构债、V19 passes 状态、V18 archive hash 历史表述和 checklist evidence；长期 specs 未发现 `TBD`、`TODO`、`created by archiving change` Purpose 占位。
- V19 external review follow-up：runtime/tests 无 P0/P1/P2；已修复文档 P2，将 `AuditManager(persistent redacted audit / read-only recovery)` 补入 `HANDOFF_TO_NEXT_CHAT.md` 与 `README.md` 当前主链路图，使其与 `docs/ARCHITECTURE.md` 一致。
- V19 archive：`openspec archive v19-persistent-audit-recovery -y` 已完成；长期 specs 已同步，归档路径为 `openspec/changes/archive/2026-06-05-v19-persistent-audit-recovery/`；archive 后 `openspec validate --all` 14 passed, 0 failed，`scripts/check_stage_docs.ps1` 扫描 24 files 无 drift，long-term specs 未发现 Purpose 占位。
- V19 archive 后 full verification：`powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` 通过，`pytest` 187 passed, 1 skipped，`ruff check .` All checks passed，stage docs drift scan 无漂移；`git diff --check` 通过，仅有 CRLF 换行提示。
- V19 merge/push closeout：`feature/v19-persistent-audit-recovery` 已 fast-forward 合并到 `main` 并推送到 `agentic-codeops/main` at `add702d62bcf737925b6418d3c9b9fb258e7ff35`；随后 post-merge handoff docs closeout commits 已推送到 `main`/remote；本地 feature branch 已 fully merged 并保留在 `add702d62bcf737925b6418d3c9b9fb258e7ff35`，按本仓库审计惯例不自动删除。
- V19 post-merge docs verification：durable docs 已更新真实 main/remote 状态、commit hash、验证结果和 branch retention 决策；stale phrase 与 long-term Purpose 扫描无命中；`openspec validate --all` 14 passed, 0 failed；`scripts/check_stage_docs.ps1` 扫描 24 files 无 drift；`powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` 通过，`pytest` 187 passed, 1 skipped，`ruff check .` All checks passed；`git diff --check` 通过，仅有 CRLF 换行提示。
- V19 post-closeout documentation parity audit：用户发现 README 未完整同步 V19。复核确认 README 缺少 V19 当前能力专章和阶段历史，路线图仍停在 V18，当前非目标误把已实现 persistent audit 列为未来项；PROGRESS/ARCHITECTURE/HANDOFF 也有同类 stale wording。现已修复 durable docs，并强化 `scripts/check_stage_docs.ps1`，要求 README 必须包含 V19 当前能力、V19 阶段历史和已归档至 V19 的路线图标记，同时拦截 V19 未完成及 persistent audit 仍属 Roadmap 的 stale wording。
- V19 documentation parity audit 验证与测试债修复：首次 full verify 发现 `tests/test_chat_api.py::test_docs_keep_stage_route_map_consistent` 仍强制要求旧 V18 archived marker，说明旧测试锁定了陈旧路线图。已将测试更新为正向验证 README 的 V19 当前能力、V19 阶段历史和已归档至 V19 路线图，并显式拒绝旧 V18 marker；targeted test 1 passed，最终 `scripts/verify.ps1` 187 passed, 1 skipped，ruff 与 stage docs drift scan 通过。
- Post-closeout semantic parity follow-up：继续复核发现 README 当前能力缺少 Verification Runner 专章及 `app/verification/` 模块说明，ARCHITECTURE 当前能力总览漏写 Patch + Verify Loop / Persistent Audit，PROGRESS 对 V18 过度描述为会再次 patch 的可恢复闭环，HANDOFF 末尾仍使用 V19 未来规划时态。现已修复，并扩展 stage docs checker 与 parity test 覆盖 Verification Runner 当前能力。
- Post-closeout semantic parity follow-up 验证：`scripts/check_stage_closeout.ps1` 通过，无 active OpenSpec change，14 specs valid，stage docs 无 drift，diff check 通过；`scripts/verify.ps1` 通过，`pytest` 187 passed, 1 skipped，`ruff check .` All checks passed。
- Process skill follow-up：复盘 V19 closeout 暴露的流程错误并沉淀到 repo-local skills。`openspec-archive-change` 新增 archive 前 delta `ADDED/MODIFIED/REMOVED` header 对齐检查；`repo-stage-review-loop` 新增 archive-syncable delta gate、positive README parity 和 stale-test gate；`repo-stage-handoff` 新增 README 分职责 parity、测试锁定陈旧文档检查、full verify 和稳定 post-merge hash 表述；stale-state checklist 同步上述检查。Skill 改动仅属于开发流程纪律，不是 RepoPilot runtime 能力。
- Process skill follow-up 验证：原先被 `.git/info/exclude` 排除的 repo-stage-handoff / repo-stage-review-loop / stale-state checklist 已显式加入 Git，确保改进会随仓库持久化；通用 `quick_validate.py` 因当前 bundled Python 缺少 `PyYAML` 无法运行，已人工核对 skill frontmatter，并通过 `scripts/check_stage_closeout.ps1`、`scripts/verify.ps1`（187 passed, 1 skipped）、ruff、stage docs drift scan 和 staged diff check。
- Skill authoring follow-up：吸收外部 skill 编写经验中适合本仓库的部分，将 repo-stage-handoff、repo-stage-review-loop、openspec-archive-change 的 description 收窄为加载时机/用户意图，并分别新增 `references/evals.md`，覆盖 positive、negative、edge 和 failure traps。未引入当前仓库没有执行环境的多模型 eval 平台、`depends` 或 `config.json`。
- Skill authoring follow-up 验证：轻量 eval 结构检查确认三个关键 skill 均包含 Positive/Negative/Edge/Failure Traps；首次检查发现 archive eval 缺少独立 Failure Traps 并已补齐；`scripts/check_stage_closeout.ps1` 与 `scripts/verify.ps1` 通过，`pytest` 187 passed, 1 skipped，ruff 和 stage docs drift scan 通过。
- Skill eval structure gate：新增 `scripts/check_skill_evals.ps1` 并接入 `scripts/verify.ps1` 与 `scripts/check_stage_closeout.ps1`，确定性检查关键流程 skill 的触发式 description、50-word 上限、eval reference 以及 Positive/Negative/Edge/Failure Traps 四类结构。该结构 gate 不替代未来真实多模型 routing eval。
- Skill eval structure gate 验证：独立结构扫描通过，`scripts/check_stage_closeout.ps1` 通过，`scripts/verify.ps1` 通过（`pytest` 187 passed, 1 skipped；ruff、stage docs drift、skill eval structure scan 均通过）。
- V17 已归档到 `openspec/changes/archive/2026-06-03-v17-verification-runner/`，长期 specs 已同步，新增 `openspec/specs/verification-runner/spec.md`。
- V17 runtime 新增 `app/verification/`、扩展 `ToolInvocationContext.command_label`、注册 `verification_run` 并接入 AgentLoop；targeted tests 已通过 11 项，相关回归 78 passed，默认 verify 通过：`pytest` 170 passed, 1 skipped；`ruff check .` All checks passed；stage docs drift scan 无漂移。
- V17 self-review 和外部 review 已覆盖 runtime、tests 和 OpenSpec change set，未发现 P0/P1/P2 问题。
- V16 已归档到 `openspec/changes/archive/2026-05-31-v16-safe-patch-authoring/`，长期 specs 已同步。
- V15 已归档到 `openspec/changes/archive/2026-05-31-v15-assistant-control-surface/`，长期 specs 已同步。
- V1-V22 active changes 均已归档；历史实现摘要保留在本 handoff 后续章节，仅作为阶段背景。

## V10 实现摘要

- 新增 `app/rag/evidence.py`，提供内部 Evidence Pack、Evidence item 和 Context Budget。
- `ToolExecutor.search_repo_rag` 在 successful hybrid retrieval 后生成 `ToolExecutionResult.evidence_pack`；工具错误时不伪造 Evidence Pack。
- Evidence item 固定包含 `evidence_id`、`file_path`、`start_line`、`end_line`、`score`、`snippet`、`source_summary`、`included` 和 `truncated`。
- Context Budget 默认 `max_context_chars=4000`，按 retrieval 顺序纳入 evidence，必要时裁剪最后一条。
- 内部 audit summary 固定包含 `evidence_items`、`included_count`、`omitted_count`、`truncated_count`、`budget_used_chars` 和 `max_context_chars`。
- `evidence_pack` 不进入 `call_summary()`、`/chat.tool_calls` 或 `/chat` 顶层响应。
- V10 仍不实现 grounded answer、model provider、prompt assembly、query rewrite、rerank、memory 或 context compression。
- V10 最新验证：
  - `openspec validate v10-evidence-pack-context-budget`：通过。
  - `pytest tests\test_evidence_pack.py tests\test_agent_harness_kernel.py tests\test_chat_api.py`：40 passed。
  - `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 75 passed, 1 skipped；`ruff check .` All checks passed。
  - `git diff --check`：通过，仅有 CRLF 换行提示。
- V10 review 收口：
  - 内部 self-review 未发现 P0/P1 阻塞；发现的 P2 历史文档措辞债已修正。
  - 外部 review：用户反馈外部 review 显示没问题，无阻塞发现。
  - 外部 review 后 full verify：`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1` 通过；`pytest` 81 passed, 1 skipped；`ruff check .` All checks passed。
  - 实现提交：`c5ec1ff Add V10 evidence pack context budget`。
  - Archive：已移动到 `openspec/changes/archive/2026-05-26-v10-evidence-pack-context-budget/`，并同步长期 `repo-query-understanding-rag` spec。
  - Archive 后验证：`openspec validate --all` 6 passed, 0 failed；`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1` 通过，`pytest` 81 passed, 1 skipped，`ruff check .` All checks passed；`git diff --check` 通过，仅有 CRLF 提示。
- V10 review follow-up：
  - 已修正长期 `agent-loop-tool-execution` spec，允许 repo-local deterministic hybrid RAG，不再禁止 V9 的本地 deterministic embedding retrieval。
  - 已把 `docs/FEATURE_LIST.json` 的 V8 条目标注为历史 lexical 验收口径，并指向当前 V9/V10 hybrid 口径。
  - `openspec validate --all`：7 passed, 0 failed。
  - `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 76 passed, 1 skipped；`ruff check .` All checks passed。
- V10 计划债务扫描修复：
  - 已修正 handoff 和 architecture 中残留的“当前 V9”口径。
  - 已把 V10 design 的实施前 `Migration Plan` 改成已执行的 implementation notes。
  - 已修正 Evidence Pack `original_query`，现在使用 `SearchPlan.original_query` 而不是提取后的 keyword。
  - 已修正 answer citation 过滤，混合相对路径和绝对路径结果时不把绝对路径写进 `/chat` answer。
  - `pytest tests\test_agent_harness_kernel.py tests\test_chat_api.py tests\test_evidence_pack.py`：42 passed。
  - `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 77 passed, 1 skipped；`ruff check .` All checks passed。
- 非 V10 历史代码债修复：
  - 已修正 V9 `hybrid_fuse` 默认阈值，强 embedding-only 命中可进入 hybrid 结果；`min_fused_score` 当前为 `0.35`。
  - 已把 AgentLoop 权限检查对象从底层 `search_code` 改为实际执行工具 `repo_rag`，并同步长期 `agent-loop-tool-execution` spec。
  - 已给 capability status 独立 route，英文状态问法不再进入 repo retrieval。
  - 已让普通英文问候避免误触发 repo_search，并清理测试中的部分 V8 命名噪音。
  - `pytest tests\test_repo_rag.py tests\test_agent_harness_kernel.py tests\test_chat_api.py`：50 passed。
  - `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 81 passed, 1 skipped；`ruff check .` All checks passed。
  - `openspec validate --all`：7 passed, 0 failed；`git diff --check`：通过，仅有 CRLF 换行提示。
- 已知剩余代码债：
  - `app/rag/evidence.py` 空 snippet 审计语义还可更干净，后续可改成 omitted 或跳过。
  - `app/harness/kernel.py` capability-status 仍是字符串规则集合，后续能力项增多时可抽成 classifier。
  - `app/rag/repo_rag.py` hybrid fusion 权重和阈值仍是硬编码常量，后续可参数化。
  - tests 中仍有少量历史阶段命名，可在测试清理时统一改成阶段无关命名。
- V10 前文档债扫描：
  - 已修正 `openspec/specs/README.md` 仍停留在 OpenSpec 初始化阶段的旧口径。
  - 已修正 `openspec/changes/README.md` 关于 legacy specs 迁移的旧口径。
  - 已修正 `docs/PROGRESS.md` 当前状态中的“当前 V4/V5 状态”措辞。
  - 已修正本 handoff V8 摘要中的“当前 V9 分支”措辞。

## 下一轮建议

1. V20 internal / external review、implementation commit、archive、merge 与 push 均已完成。
2. 下一阶段推荐规划 V24 Verified Patch Promotion；先创建 OpenSpec change，再同步 harness 边界。
3. 不要把后台执行、真实 subagents、connectors、notifications、heartbeat/cron 或
   always-on assistant 归入 V24 scope。

已完成路线：V10 Evidence Pack + Context Budget；V11 Grounded Answer / Model Provider Boundary；V12 Query Rewrite + Rerank；V13 Memory；V14 Long Task / ReAct Skeleton；V15 Assistant Control Surface；V16 Safe Patch Authoring；V17 Verification Runner；V18 Patch + Verify Loop；V19 Persistent Audit / Recovery；V20 Worktree Isolation；V21 Worktree Inventory / Inspection；V22 Worktree Re-verification；V23 Worktree Disposal / Reconciliation。近期候选路线为 V24 verified promotion；V24 后重新评估其余方向。
旧 V8 archive 中保留的是当时路线记录，已被后续 V9/V10 路线重排 supersede；当前长期 docs/specs 以 README、PROGRESS、ARCHITECTURE 和长期 OpenSpec specs 为准。
