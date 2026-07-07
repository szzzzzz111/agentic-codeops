# 当前 Review 清单

Active OpenSpec change：无。最近归档 change：`derive-capability-status-from-runtime`，
归档到 `openspec/changes/archive/2026-07-06-derive-capability-status-from-runtime/`。
风险级别：medium。

目标：把 capability-status（能力状态）和 Assistant Control Surface（助手控制面）的当前能力摘要，
从现有 `ToolRegistry` backing primitives（支撑运行时原语）和固定安全边界派生出来；避免静态文案
继续漂移，同时不开放 MCP、Skill、connector、subagent 或后台执行能力。

## Grilling Gate

- [x] 已压实术语：本阶段不是 MCP server、不是 Skill execution、不是 connector，也不是手写大 catalog；
  它是 runtime-derived capability status（从真实运行时能力派生的状态摘要）。
- [x] 已确认反例：仅存在 `skill_loader` 不等于支持 Skill execution；存在 `patch_apply` 不等于用户可任意调用 patch apply；
  存在 descriptor 文案不等于开放 MCP runtime。
- [x] 已确认 runtime availability 边界：能力可用性先看 active `ToolRegistry` 是否有 backing primitive，
  再叠加 approval、固定 label、non-goals 等产品/安全边界。
- [x] 已确认 approval/audit boundary：本阶段不绕过 `PermissionPolicy`、`ApprovalGate`、mutation lock 或 persistent audit；
  capability-status 本身仍不调用 repo RAG 或写风险工具。
- [x] 已确认 non-goals：不实现 MCP server、Skill execution、connector、runtime subagent、background worker、
  dynamic tool registration、网络依赖或新的公开 descriptor API。

## Planning / Harness

- [x] 已读取 `AGENTS.md`、必读文档、OpenSpec README、Harness rules 和 workflow/planning skills。
- [x] 已检查 branch、worktree、recent commits 和 active OpenSpec changes。
- [x] 已选择 change name：`derive-capability-status-from-runtime`。
- [x] 已创建 OpenSpec proposal、design、tasks、spec deltas。
- [x] 已同步 `.harness/allowed_files.md` 与本 checklist。
- [x] `openspec validate derive-capability-status-from-runtime --strict` 通过。

## Plan Review Gate

- [x] Internal plan review：proposal/design/tasks/spec deltas/test plan/Harness 边界一致性。
- [x] Codex independent plan review：Newton 发现 1 个 P2，已按 `fix` 处理。
- [x] OpenCode independent plan review：复用 `ses_11a9a66e9ffemxERTmX6uRcA34`，初审发现 F1/P1、F2/P2、F3/P2、F4/P3、F5/P3；focused re-review 确认 all prior findings closed，no new in-scope findings。
- [x] 所有 plan findings 按 `fix / clarify / reject / defer` 分类并处理。
- [x] Implementation confirmation gate：用户已确认继续本阶段实现。

Plan findings:

- `clarify`（internal）：Persistent Audit / Recovery 不是 `ToolRegistry` primitive；spec 已澄清为 execution subcapabilities 由 backing tools 支撑，manager-only subcapabilities 可由固定 runtime manager wiring 表达。
- `fix`（OpenCode F1/P1）：spec 曾要求 promotion 由 `ToolRegistry` backing tool 支撑，但当前没有独立 promotion tool；已澄清 Verified Patch Promotion 是 composed subcapability（组合能力），依赖既有 promotion route/preflight 和主工作区写入 primitive，而不是要求新增 tool。
- `fix`（OpenCode F2/P2）：default patch capability scenario 的 WHEN 曾被 registry 条件窄化，可能造成默认行为覆盖空洞；已恢复为普通 patch support query，缺失 backing primitive 由独立 scenario 覆盖。
- `clarify`（OpenCode F3/P2）：Assistant Control Surface 与 capability-status 复用同一 adapter 的 structured facts，但 formatter 不同；已澄清控制面保持简短，不输出 V11/V12/V13/V16/V25 等阶段化长文案。
- `clarify`（OpenCode F4/P3）：控制面不应主动引入 MCP/Skill/connector/subagent 的否定清单；已改为避免新增这些技术名，除非后续 change 明确扩展 wording。
- `clarify`（OpenCode F5/P3）：`ToolRegistry` registration 不等于任意请求可执行；已澄清 adapter 粒度是 coarse availability（可能通过既有 route/context/approval 可用），不是 per-request eligibility engine。
- OpenCode focused re-review：F1-F5 均已关闭；residual uncertainty 低，仅剩 promotion route availability 的具体实现方式，属于 implementation choice。
- `fix`（Codex/Newton P2）：Assistant Control Surface 可能隐式使用 default registry，导致 custom `AgentLoop.tool_registry` 下 capability-status 与 `assistant status` 再次漂移；已补 design/spec/tasks，要求 AgentLoop 将 active registry-derived facts 传入控制面，并增加 custom registry assistant status RED coverage。

## Implementation Gate（plan review 后）

- [x] RED tests：active `ToolRegistry` 缺少 backing primitive 时，capability-status 不宣称该执行能力当前可用。
- [x] RED tests：default registry 仍正确声明 patch、verification、worktree、promotion、grounded answer、rewrite/rerank 和 memory 边界。
- [x] RED tests：Assistant Control Surface 当前能力摘要复用 active runtime-derived capability summary，custom `ToolRegistry` 缺失 primitive 时也不宣称对应执行能力当前可用，且不把 MCP、Skill execution、connector 或 runtime subagent 写成当前 runtime 能力。
- [x] Runtime：添加最小 read-only `ToolRegistry` snapshot/list 和内部 capability status adapter。
- [x] Runtime：capability-status 与 Assistant Control Surface 通过同一 adapter 生成能力摘要。
- [x] 保持 `/chat` public contract、route order、`related_files=[]`、`tool_calls=[]` 和 no repo RAG 行为不变。

Implementation evidence:

- RED focused tests：`pytest tests/test_agent_harness_kernel.py tests/test_assistant_control_surface.py -q` 初次失败 4 项，分别覆盖缺少 `ToolRegistry.list_specs()`、capability-status 无视 custom registry、Assistant Control Surface 无视 active registry-derived summary、`answer_status()` 不接受 injected capability summary。
- GREEN focused tests：`pytest tests/test_agent_harness_kernel.py tests/test_assistant_control_surface.py -q` 为 76 passed。
- Adjacent `/chat` contract tests：`pytest tests/test_chat_api.py -q` 为 22 passed。
- `ruff check .`：passed。
- `openspec validate derive-capability-status-from-runtime --strict`：passed。
- `openspec validate --all`：23 passed，0 failed。
- Internal final review finding `fix`：repo RAG backed status 在 empty registry 下仍宣称 V11/V9 可用；已新增 regression 并改为 `repo_rag 未注册` fail-closed。
- OpenCode final review finding `fix`：default patch answer 缺少 spec 要求的 `branch/PR automation`、`connector`、`background retry`、`runtime subagent` non-goals；已补 answer 和 test。Focused re-review 确认 F1/P2 closed，no new in-scope findings。

## Final Review / Verification（implementation 后）

- [x] Focused AgentLoop capability-status tests。
- [x] Focused Assistant Control Surface tests。
- [x] Adjacent Chat API contract tests。
- [x] `ruff check .`。
- [x] `openspec validate --all`。
- [x] `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`。
- [x] `git diff --check`。
- [x] Final implementation review and finding triage。
- [x] Focused Stage Debt Sweep。
- [x] Human review packet prepared for L2 review。
- [x] Archive readiness check。
- [x] `openspec archive derive-capability-status-from-runtime --yes` 已同步长期 specs 并归档 change。

Final verification evidence:

- `pytest tests/test_agent_harness_kernel.py tests/test_assistant_control_surface.py -q`：77 passed。
- `pytest tests/test_chat_api.py -q`：22 passed。
- `ruff check .`：passed。
- `openspec validate derive-capability-status-from-runtime --strict`：passed。
- `openspec validate --all`：23 passed，0 failed。
- Full `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`：pytest 525 passed，1 skipped；ruff、stage docs scan、skill eval structure scan passed。
- `git diff --check`：passed，仅 CRLF normalization warnings。

Final review findings:

- `fix`（internal）：repo RAG backed capability status 没有在 `repo_rag` 缺失时降级；已新增 grounded answer / vector status empty-registry regressions，并让 adapter 输出 `repo_rag 未注册`，不宣称 V11/V9 当前可用。
- `fix`（OpenCode F1/P2）：default patch answer 漏列 `branch/PR automation`、`connector`、`background retry`、`runtime subagent` non-goals；已补默认 answer 和 regression assertions。OpenCode focused re-review：F1 closed，no new findings。

Human review packet:

- Changed file map：`app/harness/capabilities.py` 新增内部 adapter；`app/harness/kernel.py` 新增 `ToolRegistry.list_specs()` 并接入 capability-status / assistant-status wiring；`app/assistant/control_surface.py` 支持 injected `capability_summary`；tests 覆盖 active registry / missing primitive / control surface summary；docs/harness 同步当前状态和 human review depth workflow。
- Behavior changes：capability-status 和 Assistant Control Surface 当前能力摘要从 active `ToolRegistry` 派生；missing `repo_rag`、`patch_apply`、`verification_run`、`worktree_create`、`worktree_dispose` 时不宣称对应执行路径当前可用；默认 registry 仍报告已实现边界。
- Suggested human inspection paths：`app/harness/capabilities.py` formatter/fail-closed logic；`app/harness/kernel.py` lines around `ToolRegistry.list_specs()` and `_run_inner()` status branches；`app/assistant/control_surface.py` injected summary fallback；`tests/test_agent_harness_kernel.py` new registry-derived status regressions。
- Residual risk：adapter 仍是 coarse availability（粗粒度可用性），不是 per-request eligibility engine；未新增 public descriptor API。

Stage Debt Sweep scope:

- Changed runtime/tests/docs/OpenSpec/Harness。
- Direct dependencies：`RequestRouter.route()` capability_status path、`AgentLoop._run_inner()` route order、
  `ToolRegistry` metadata boundary、`PermissionPolicy` / `ApprovalGate` assumptions、
  `AssistantControlSurface.answer_status()` public wording boundary、`AgentLoopResult.to_agent_result()` public contract。

Stage Debt Sweep result:

- Inspected changed runtime/tests/docs/OpenSpec/Harness and direct dependencies listed above。
- No new blocking debt found. Public `/chat` contract unchanged；status requests keep `related_files=[]` and `tool_calls=[]`；no MCP/Skill/connector/subagent runtime capability was introduced。
- Archive result：`openspec archive derive-capability-status-from-runtime --yes` succeeded；长期
  `agent-loop-tool-execution` 与 `assistant-control-surface` specs 已同步；change 已归档到
  `openspec/changes/archive/2026-07-06-derive-capability-status-from-runtime/`。
- Archive-after verification：`openspec list` reports no active changes；`openspec validate --all`
  为 22 passed，0 failed；full `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`
  为 pytest 525 passed，1 skipped，ruff、stage docs scan、skill eval structure scan passed；
  `git diff --check` passed，仅 CRLF normalization warnings。
