## Context

同一 ambiguous fixture 在两个无 retry live run 中均生成 235 tokens 且缺少 citation；其他 grounded
cases 与 Prompt Injection 已通过。这表明模型理解 evidence 与安全规则，但对模糊问题倾向于生成
澄清文本而忽略“回答中至少引用一次”的非位置化要求。

本 change 为 medium risk：只收紧 grounded-text system instruction，但直接影响真实模型输出。
Eval runner 保持冻结，验证继续由 strict validator 和完整 live gate 完成。

## Goals / Non-Goals

**Goals:**

- 给模型一个唯一、稳定、与 validator 兼容的 citation 输出槽位。
- 即使正文是澄清、保守回答或拒答，只要使用了 evidence，最后一行仍包含 exact citation。
- 保持正文自然语言不受固定模板约束。

**Non-Goals:**

- 不在 Provider 或 Grounded Answer 中自动追加 citation。
- 不允许缺 citation 的模型输出通过 validator。
- 不修改 evidence framing、JSON mode、metrics、API、wiring、eval fixture/rubric 或 V24。

## Decisions

1. System instruction 要求 response 最后一行“只包含”一个 allowed label，例如
   `app/file.py:1-3`，不加 `Citation:`、markdown 或标点。
2. 该要求适用于回答、澄清和拒答，避免 ambiguous intent 成为 citation contract 例外。
3. 不做 runtime post-processing；模型不服从时 strict validator 仍 fallback，live gate 仍失败。
4. Structured JSON instruction 保持原状，并由现有 parity regression 保护。

## Risks / Trade-offs

- [Footer 影响自然语言] → 只固定最后一行，正文保持自由。
- [模型仍可能忽略] → 无 retry，validator/live gate 继续 fail closed。
- [引用与澄清内容关联较弱] → citation 表示该 grounded response 使用的 evidence 来源，不等于回答
  已完全消除问题歧义。
