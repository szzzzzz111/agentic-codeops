# grounded-answer-model-provider Specification

## ADDED Requirements

### Requirement: 系统基于预算内证据生成 grounded answer

系统 SHALL 在 repo-local retrieval 成功并产生 Evidence Pack 后，使用预算内 included evidence snippets 生成 grounded answer。Grounded answer MUST 优先基于可审计的 deterministic lexical/path/symbol evidence 和对应 citation metadata 组织回答。Grounded answer MUST NOT 直接读取仓库文件、执行工具、修改代码、执行 shell、执行 skill、访问 omitted/truncated snippets 或让模型自由编造未被 evidence 支撑的结论。

#### Scenario: 有证据时生成带 citation 的回答

- **WHEN** Evidence Pack 包含至少一个 `included=True` 的 evidence item
- **THEN** 系统 SHALL 将 original query、question type、included evidence snippets 和 citation metadata 传入回答生成边界
- **AND** `answer` SHOULD 基于 evidence 内容组织自然语言回答
- **AND** `answer` MUST 包含至少一个合法 citation

#### Scenario: 无证据时返回保守 fallback

- **WHEN** Evidence Pack 不包含 `included=True` 的 evidence item
- **THEN** 系统 MUST NOT 调用真实 model provider
- **AND** `answer` MUST 明确说明无法基于仓库证据回答

### Requirement: 系统提供 Model Provider 边界

系统 SHALL 提供 Model Provider 边界。默认 provider MUST 是本地 deterministic fake provider。系统 MAY 在显式环境变量配置下启用 OpenAI-compatible provider。默认验证 MUST NOT 依赖网络、密钥或真实模型输出。

OpenAI-compatible provider MUST 使用运行时依赖 `httpx`。Provider 配置 MUST 从环境变量读取：`REPOPILOT_MODEL_PROVIDER`、`REPOPILOT_MODEL_BASE_URL`、`REPOPILOT_MODEL_API_KEY`、`REPOPILOT_MODEL_NAME` 和 `REPOPILOT_MODEL_TIMEOUT_SECONDS`。

#### Scenario: 默认 provider 稳定生成回答

- **WHEN** 未配置真实 provider
- **THEN** 系统 MUST 使用 deterministic fake provider
- **AND** 相同输入 MUST 生成稳定输出
- **AND** 默认验证 MUST NOT 发起真实网络请求

#### Scenario: 显式配置 OpenAI-compatible provider

- **WHEN** `REPOPILOT_MODEL_PROVIDER=openai_compatible` 且 base URL、API key 和 model 均已配置
- **THEN** 系统 MAY 调用 OpenAI-compatible chat completions 接口
- **AND** 请求 MUST 使用脱敏边界，不记录 API key 或完整 prompt

### Requirement: 系统校验 grounded answer citation

系统 SHALL 校验 model provider 输出中的 citation。允许 citation 格式为 `relative/path.py:start-end`，其中 `start` 和 `end` MUST 为正整数。单行引用 SHOULD 规范化为 `path:n-n`。Citation MUST 完全匹配提供给 provider 的 evidence `file_path`、`start_line` 和 `end_line`。

系统 MUST 允许重复 citation 和乱序 citation。系统 MUST 将绝对路径、未提供路径、错误行号、错误范围、无法解析 citation 和没有合法 citation 的 provider 输出视为不可信，并返回保守 fallback。

#### Scenario: 越界 citation 被降级

- **WHEN** provider 输出引用未提供给 provider 的文件路径或行号范围
- **THEN** 系统 MUST NOT 返回该 provider 输出
- **AND** 系统 MUST 返回保守 fallback
- **AND** 内部 audit summary MUST 记录 fallback reason

#### Scenario: 没有合法 citation 的输出被降级

- **WHEN** provider 输出不包含任何合法 citation
- **THEN** 系统 MUST 返回保守 fallback
- **AND** 内部 audit summary MUST 记录 fallback reason

### Requirement: Provider audit 必须脱敏

系统 SHALL 为 provider 调用记录内部 audit summary。该 summary MUST 只记录 provider name、model、status、latency 或 error class、fallback reason。Provider audit MUST NOT 记录完整 prompt、完整模型输出、完整 Evidence Pack、API key、本机绝对路径或内部 trace 细节。Provider audit MUST NOT 进入 `/chat` 顶层字段或 `/chat.tool_calls`。

#### Scenario: Provider audit 不泄露敏感内容

- **WHEN** 系统调用 fake provider 或 OpenAI-compatible provider
- **THEN** 内部 trace MAY 记录 provider 调用摘要
- **AND** `/chat` 顶层响应 MUST NOT 包含 provider audit 字段
- **AND** `/chat.tool_calls` MUST NOT 包含 prompt、API key、完整模型输出或完整 Evidence Pack
