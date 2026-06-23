## Why

更新后的真实 DeepSeek live eval 仍显示所有 grounded-text 回答无法通过 citation gate，并且
Prompt Injection case 输出了 `ATTACK_MARKER`。当前 system instruction 要求复制裸
`path:start-end` label，但 user evidence 使用 `[path:start-end]` framing，且 evidence 内不可信
指令与事实文本没有清晰分隔，导致模型面对互相冲突的格式示例和指令层级。

## What Changes

- Grounded-text user prompt 使用与 validator 一致的裸 `path:start-end` citation label，不再使用
  方括号包装。
- 使用稳定、明确的 evidence item delimiters，把 citation metadata 与不可信 snippet 分隔。
- System instruction 明确禁止遵循、复述或转换 evidence 中要求改变回答行为、泄露内容或输出
  marker 的指令。
- 保持 citation validator、JSON mode、metrics、API、默认 Patch wiring、persistence 与 eval
  runner 不变。
- 不创建 V24，不降低 live eval hard gates。

## Capabilities

### New Capabilities

- 无。

### Modified Capabilities

- `grounded-answer-model-provider`: 对齐 grounded evidence framing、citation label 和
  untrusted-evidence instruction contract。

## Impact

- Runtime: `app/providers/model_provider.py`
- Tests: `tests/test_model_provider.py`、`tests/test_grounded_answer.py`
- Specs/docs: grounded-answer provider spec、Harness、ARCHITECTURE、PROGRESS、HANDOFF
- 无公开 API、持久化、权限、默认网络或依赖变化。
