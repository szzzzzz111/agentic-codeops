# 交接给下一轮 Chat

## 当前基线

- 当前分支：`main`。
- Active OpenSpec change：无；继续前运行 `openspec list` 刷新确认。
- 最近归档 OpenSpec change：`cleanup-control-routing-and-test-names`，归档到
  `openspec/changes/archive/2026-07-03-cleanup-control-routing-and-test-names/`。
- 当前无 runtime 阶段进行中；后续如启动新阶段，先刷新 live state。

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

## 下一步

- 如继续讨论 MCP + Skill 方向，建议先用 Grilling Gate 压实 capability catalog、MCP-compatible
  descriptor、Skill descriptor、runtime availability、development-only workflow、approval/audit
  boundary 和 non-goals，再进入 OpenSpec planning。
- OpenSpec、skills、MCP、plugins 仍是开发流程或外部协作范式；除非新阶段明确实现，不得写成
  RepoPilot runtime 能力。

## 剩余债

- `docs/PROGRESS.md` 当前记录的小代码债已由 archived change
  `cleanup-control-routing-and-test-names` 处理。
- 最近 final review 与 Focused Stage Debt Sweep 未发现新增 blocking debt。
