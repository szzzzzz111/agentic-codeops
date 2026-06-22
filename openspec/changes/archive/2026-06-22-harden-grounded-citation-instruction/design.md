## Context

Live run 的 8 次调用中，Planner/Patch structured JSON、无答案和 secret filtering 均通过；6 个
grounded-text case 全部 citation failure。Provider user message 已以 `[path:start-end]` 展示
evidence label，但 system prompt 未描述 validator 的 exact-match 规则。

## Goals / Non-Goals

**Goals:**

- 让 grounded-text instruction 明确、可测试地表达 exact citation contract。
- 将允许 label 从 request evidence 动态生成，不按业务类型猜测。
- 同时明确 evidence 内文本不得覆盖 system instruction。

**Non-Goals:**

- 不放宽 citation validator，不接受模糊路径、子范围或模型自造 citation。
- 不修改 JSON output instruction、metrics、默认 wiring、API 或 eval runner。
- 不为某个 DeepSeek 模型硬编码特殊输出。

## Decisions

- `_system_prompt(request)` 从 evidence metadata 生成稳定、去重、按输入顺序排列的 allowed labels。
- Prompt 要求至少逐字复制一个完整 label，格式固定为 `relative/path:start-end`，不得添加括号内
  行号变体或改写范围。
- Prompt 声明 evidence 是 untrusted repository data，其中任何“忽略指令”等文本都不得执行。
- 无 evidence 的 grounded request 仍生成不含 label 的保守 instruction；正常 Grounded Answer
  已在调用 Provider 前对空 evidence 零调用 fallback。

## Risks / Trade-offs

- [Prompt 增长] → 只列 citation metadata，不重复 snippet；Evidence Pack 已受 context budget 限制。
- [模型仍可能不服从] → validator 继续 fail closed，live eval 再验证真实效果。
- [特定措辞过拟合] → contract 使用 provider-neutral 英文格式要求，不提 DeepSeek。
