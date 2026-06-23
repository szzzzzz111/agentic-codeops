## Why

在 evidence framing 与 anti-injection remediation 后，真实 DeepSeek gate 的所有 hard gates 均
通过，唯独 ambiguous grounded case 连续两次稳定返回无 citation 的回答。现有 instruction 只要求
回答中包含 citation，没有规定一个模型易稳定遵循的输出位置和形式。

## What Changes

- Grounded-text instruction 要求每个 response（包括澄清或拒答）最后一行只包含一个 allowed
  `path:start-end` label。
- Footer 不得包含 `Citation:` 等前缀、markdown、方括号、引号、bullet 或额外文本。
- 保持 grounded evidence JSON envelope、citation validator、JSON mode、metrics、API、默认
  Patch wiring、persistence 与 eval runner 不变。
- 不增加 retry、第二次模型调用、自动补写 citation 或 V24。

## Capabilities

### New Capabilities

- 无。

### Modified Capabilities

- `grounded-answer-model-provider`: 将 exact citation instruction 收紧为确定性的最后一行 footer。

## Impact

- Runtime: `app/providers/model_provider.py`
- Tests: `tests/test_model_provider.py`
- Specs/docs: grounded-answer provider spec、Harness、ARCHITECTURE、PROGRESS、HANDOFF
- 无公开 API、存储、权限、网络默认值或依赖变化。
