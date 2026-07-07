# 交接给下一轮 Chat

## 当前基线

- 当前分支：`main`，已推送到 `agentic-codeops/main`。
- Active OpenSpec change：无；继续前运行 `openspec list` 刷新确认。
- 最近归档 OpenSpec change：`derive-capability-status-from-runtime`，归档到
  `openspec/changes/archive/2026-07-06-derive-capability-status-from-runtime/`。
- 当前 runtime 阶段实现、final review、Focused Stage Debt Sweep 和 full verify 已完成：
  capability-status（能力状态）和 Assistant Control Surface（助手控制面）已接入
  runtime-derived capability facts（从真实运行时工具派生的能力事实）；OpenSpec archive 已同步长期 specs，
  archive-after verification 已通过，implementation/archive commit 已推送。

建议先运行：

```powershell
git status --short --branch
git log -5 --oneline --decorate
openspec list
openspec validate --all
```

## 最新流程规则

- 普通窄阶段使用 summary approval（摘要确认）：Agent 阅读完整 OpenSpec
  proposal/design/tasks/spec，并向用户输出中文高信号摘要、风险级别、touched file families、
  non-goals 和 implementation confirmation gate；用户不需要逐字审 OpenSpec artifacts。
- 高风险、公开/runtime 行为变化、术语模糊或用户明确要求时，提升为更完整的 plan/spec review。
- MCP、Skill、subagent、connector、runtime plugin、background worker、durable execution、
  always-on assistant 等容易膨胀或误导的主题，应在 OpenSpec 落笔前做轻量 Grilling Gate
  （需求拷问关），明确 canonical terms、counterexamples、runtime availability、
  approval/audit boundary 和 non-goals。
- Code review（代码审查）按分层模式执行：scope、business logic、architecture boundary、
  minimality、failure semantics、security/privacy、test adequacy、maintainability。
  Agent 默认负责底层实现、测试、安全和维护性审查，并把结论翻译成用户可判断的中文摘要；
  用户主要确认方向、边界、行为语义、风险接受和残余风险。
- Human review depth（人工审查深度）按风险触发，不只按 diff 行数：L1 小改动看摘要/拍板点/
  non-goals/测试项并在实现后审 diff；L2 用户可见或 routing-sensitive 改动看 `design.md`
  决策/风险和 `tasks.md` 测试项，实现后需要 human review packet；L3 高风险改动完整审
  `design.md`、`tasks.md` 和 spec MUST/SHALL 场景，必要时先做反例审查。

## 当前实现状态

- 新增 `app/harness/capabilities.py`：内部 capability adapter，从 `ToolRegistry.list_specs()`
  派生 structured runtime capability facts。
- `ToolRegistry` 新增只读 `list_specs()`；仍不 dispatch、不负责 policy、不负责用户文案。
- `AgentLoop` capability-status 路径已改为使用 active registry-derived facts；custom registry 缺少
  `patch_apply`、`verification_run`、`worktree_create` 或 `worktree_dispose` 时，不宣称对应 execution
  path 当前可用。
- `AssistantControlSurface.answer_status()` 支持 injected `capability_summary`；`AgentLoop` 调用时传入
  同一 active registry-derived summary，避免回退到 default registry。
- 已跑验证：RED focused tests 初次失败 4 项；GREEN 后
  `pytest tests/test_agent_harness_kernel.py tests/test_assistant_control_surface.py -q` 为 77 passed；
  `pytest tests/test_chat_api.py -q` 为 22 passed；`ruff check .` passed；
  `openspec validate derive-capability-status-from-runtime --strict` passed；
  `openspec validate --all` 为 23 passed、0 failed。
- Full `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` 通过：pytest 525 passed、
  1 skipped；ruff、stage docs scan、skill eval structure scan passed。`git diff --check` passed，
  仅 CRLF normalization warnings。
- Archive-after verification：`openspec list` 为 No active changes found；`openspec validate --all`
  为 22 passed、0 failed；full `scripts/verify.ps1` 仍为 pytest 525 passed、1 skipped；
  `git diff --check` passed，仅 CRLF normalization warnings。
- Final review：internal review 修复 repo RAG backed status 在 `repo_rag` 缺失时仍宣称 V11/V9 可用的问题；
  OpenCode final review F1/P2 修复 default patch answer 漏列 non-goals 的问题，focused re-review
  确认 closed 且 no new in-scope findings。Stage Debt Sweep 未发现新增 blocking debt。

## 下一步

- 下一步由用户决定是否启动新的 runtime stage。
- 新阶段只能在用户明确要求后启动；commit、merge、push 仍需要用户明确授权。
- OpenSpec、skills、MCP、plugins 仍是开发流程或外部协作范式；除非新阶段明确实现，不得写成
  RepoPilot runtime 能力。

## 剩余债

- `docs/PROGRESS.md` 当前记录的小代码债已由 archived change
  `cleanup-control-routing-and-test-names` 处理。
- Archived change `derive-capability-status-from-runtime` final review 与 Focused Stage Debt Sweep
  未发现新增 blocking debt。
