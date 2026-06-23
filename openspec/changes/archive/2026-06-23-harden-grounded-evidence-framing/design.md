## Context

真实 DeepSeek run 已连续两次证明共享 Provider、usage、finish reason、Planner 与 Patch JSON
路径正常，但 grounded-text 路径仍失败。当前 system message 列出裸 citation labels，而 user
message 把同一 label 写成 `[path:start-end]`，形成两个竞争格式。Evidence snippet 也直接拼接在
普通文本中，仅靠一句 “untrusted data” 未能阻止模型执行其中要求输出 `ATTACK_MARKER` 的指令。

本 change 为 medium risk：只修改 grounded-text prompt assembly，但会影响真实模型回答与安全
硬门，因此要求 TDD、全量 deterministic verification、focused external review 和重新运行 live
gate。Eval runner 保持冻结。

## Goals / Non-Goals

**Goals:**

- Grounded user message 与 system allowed list 只展示同一种裸 `path:start-end` label。
- 把 evidence items 序列化成明确标记为不可信数据的 JSON envelope，避免普通文本 framing 与
  citation 语法竞争。
- 明确禁止遵循、复述、转换、编码或以其他方式执行 evidence 内改变回答行为、泄露内容或输出
  marker 的指令。
- 保持模型仍可根据 evidence 中的事实内容回答并复制合法 citation。

**Non-Goals:**

- 不放宽或修改 citation validator。
- 不修改 JSON mode 的既有 user/system prompt、Planner/Patch schema、metrics 或 finish reason。
- 不引入 provider-specific 分支、内容分类器、第二次模型调用、retry 或 answerability classifier。
- 不修改 eval runner、默认 Patch wiring、API、persistence、CI 或 V24。

## Decisions

1. `_format_provider_prompt(request)` 只在 `grounded_text` mode 使用新 framing；`json_object`
   mode 保留现有 prompt assembly，避免 remediation 改变 Planner/Patch 行为。
2. Grounded evidence 使用 JSON object envelope：
   `{"evidence":[{"citation":"path:start-end","content":"..."}]}`。JSON escaping 负责稳定表达
   任意 snippet 文本；citation 不使用方括号、markdown link 或其他 validator 不接受的包装。
3. System instruction 明确 evidence JSON 仅为数据，并禁止执行或复述其中要求改变规则、输出
   marker、泄露信息或忽略指令的文本。模型仍可总结事实内容，但必须引用 allowed list 中的裸 label。
4. Provider 层不尝试检测 prompt injection 内容；安全边界仍由 instruction、严格 citation
   validator 与 live hard gate 共同组成。

## Risks / Trade-offs

- [模型仍可能不服从] → validator 与 live prompt-injection gate 继续 fail closed；不降低门槛。
- [JSON envelope 增加 token] → 仅包含已预算 evidence，且不在 system message 重复 snippet。
- [误伤正常事实文本] → 禁止的是 evidence 内改变回答行为的指令，不禁止总结普通代码或文档事实。
- [影响 structured output] → mode 分支保证 JSON Planner/Patch prompt 保持原状，并增加回归测试。
