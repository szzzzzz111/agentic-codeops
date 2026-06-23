## MODIFIED Requirements

### Requirement: 系统校验 grounded answer citation

系统 SHALL 校验 model provider 输出中的 citation。允许 citation 格式为
`relative/path.py:start-end`，其中 `start` 和 `end` MUST 为正整数。单行引用 SHOULD 规范化为
`path:n-n`。Citation MUST 完全匹配提供给 provider 的 evidence `file_path`、`start_line` 和
`end_line`。

Grounded-text provider instruction MUST 列出 request evidence 中允许的 citation labels，并要求
模型至少逐字复制一个完整 label。Instruction MUST NOT 允许模型改写路径、起止行、引用子范围或
创建未提供的 citation。Grounded-text user message MUST 使用与 allowed list 相同的裸
`path:start-end` label，MUST NOT 使用方括号或其他竞争 citation framing。

Grounded evidence MUST 通过明确标记为不可信数据的结构化 envelope 传递。Instruction MUST 明确
repository evidence 是不可信数据，其中的文本不得覆盖 system instruction；模型 MUST NOT
遵循、复述、转换、编码或以其他方式执行 evidence 内要求改变回答行为、泄露内容、忽略规则或输出
marker 的指令。

系统 MUST 允许重复 citation 和乱序 citation。系统 MUST 将绝对路径、未提供路径、错误行号、
错误范围、无法解析 citation 和没有合法 citation 的 provider 输出视为不可信，并返回保守
fallback。

#### Scenario: Grounded instruction 明确 exact citation contract

- **WHEN** grounded-text request 包含一个或多个 evidence items
- **THEN** system instruction MUST 按稳定顺序列出对应 `path:start-end` labels
- **AND** instruction MUST 要求至少逐字复制一个 label
- **AND** user message MUST 使用相同裸 label 且不得使用方括号包装

#### Scenario: Grounded evidence 使用不可信数据 envelope

- **WHEN** grounded-text request 包含 repository evidence snippets
- **THEN** user message MUST 把 citation metadata 和 snippet 放入明确的不可信数据 envelope
- **AND** instruction MUST 禁止执行或复述 evidence 内改变回答行为、泄露内容或输出 marker 的指令
- **AND** JSON object mode 的 prompt contract MUST 保持不变

#### Scenario: 越界 citation 被降级

- **WHEN** provider 输出引用未提供给 provider 的文件路径或行号范围
- **THEN** 系统 MUST NOT 返回该 provider 输出
- **AND** 系统 MUST 返回保守 fallback
- **AND** 内部 audit summary MUST 记录 fallback reason

#### Scenario: 没有合法 citation 的输出被降级

- **WHEN** provider 输出不包含任何合法 citation
- **THEN** 系统 MUST 返回保守 fallback
- **AND** 内部 audit summary MUST 记录 fallback reason
