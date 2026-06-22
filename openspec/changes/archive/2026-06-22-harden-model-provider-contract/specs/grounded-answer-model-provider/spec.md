## MODIFIED Requirements

### Requirement: 系统提供 Model Provider 边界

系统 SHALL 提供 Model Provider 边界。默认 provider MUST 是本地 deterministic fake provider。
系统 MAY 在显式环境变量配置下启用 OpenAI-compatible provider。默认验证 MUST NOT 依赖网络、
密钥或真实模型输出。

`ModelProviderRequest` MUST 默认使用 `grounded_text` output mode，以保持现有调用兼容。
系统 MAY 使用 `json_object` mode 请求结构化输出，但调用方 MUST 显式提供结构化输出名称、顶层
JSON object example 和正整数 output token 上限。Provider MUST NOT 根据 `question_type` 猜测业务
schema。未知 mode、text mode 携带结构化 instruction、JSON mode 缺少 instruction、非
`[A-Za-z][A-Za-z0-9_.-]{0,63}` 名称、超过 4096 字符、非法、深度解析失败或非 object JSON
example，以及超出 `1..16384` 的 token 上限 MUST 在 HTTP 调用前 fail closed。

OpenAI-compatible provider MUST 使用运行时依赖 `httpx`。Provider 配置 MUST 从环境变量读取：
`REPOPILOT_MODEL_PROVIDER`、`REPOPILOT_MODEL_BASE_URL`、`REPOPILOT_MODEL_API_KEY`、
`REPOPILOT_MODEL_NAME`、`REPOPILOT_MODEL_TIMEOUT_SECONDS` 和可选
`REPOPILOT_MODEL_THINKING`。Thinking 未配置时 MUST NOT 写入请求；值为 `disabled` 时 MAY 发送
`{"type":"disabled"}`；其他值 MUST fail closed。

#### Scenario: 默认 provider 稳定生成回答

- **WHEN** 未配置真实 provider
- **THEN** 系统 MUST 使用 deterministic fake provider
- **AND** 相同 grounded text 输入 MUST 生成稳定输出
- **AND** 默认验证 MUST NOT 发起真实网络请求

#### Scenario: 旧调用方保持兼容

- **WHEN** 调用方构造 request 时不提供 output mode 或 structured instruction
- **THEN** request MUST 使用 `grounded_text`
- **AND** FakeModelProvider MUST 保持现有带 citation 的稳定回答行为

#### Scenario: Fake provider 不伪造结构化结果

- **WHEN** FakeModelProvider 收到合法 `json_object` request
- **THEN** provider MUST 返回稳定 unsupported-mode error
- **AND** provider MUST NOT 伪造 Planner 或 Patch JSON

#### Scenario: 显式配置 OpenAI-compatible provider

- **WHEN** `REPOPILOT_MODEL_PROVIDER=openai_compatible` 且 base URL、API key 和 model 均已配置
- **THEN** 系统 MAY 调用 OpenAI-compatible chat completions 接口
- **AND** 请求 MUST 使用脱敏边界，不记录 API key 或完整 prompt

#### Scenario: 非法结构化请求不发出 HTTP

- **WHEN** JSON mode 缺少合法 structured instruction 或 output token 上限无效
- **THEN** provider MUST 返回稳定 request validation error
- **AND** HTTP client MUST NOT 被调用

## ADDED Requirements

### Requirement: Provider 结构化输出与业务 schema 分层

OpenAI-compatible provider 在 `json_object` mode 下 SHALL 发送 JSON object response format、
调用方提供的 JSON example 和 output token 上限。Provider MUST 只校验 response content 非空、
可解析且顶层为 JSON object；Provider MUST NOT 校验 Long Task 或 Patch 业务字段。调用方 MUST
继续负责业务 schema、step、citation、路径和 diff 校验。

#### Scenario: Provider 接受基础合法 JSON object

- **WHEN** JSON mode response content 是可解析的顶层 JSON object
- **THEN** provider SHALL 返回 success 和原始 content
- **AND** 业务字段正确性 MUST 由调用方判断

#### Scenario: Provider 拒绝非 object JSON

- **WHEN** JSON mode response 是 array、scalar、空 content 或非法 JSON
- **THEN** provider MUST 返回安全 error
- **AND** 调用方 MUST NOT 把该 response 当作有效业务结果

## MODIFIED Requirements

### Requirement: Provider audit 必须脱敏

系统 SHALL 为 provider 调用记录内部 audit summary。该 summary MUST 只记录 provider name、model、
status、latency 或 error class、fallback reason。Provider response MAY 额外携带 request-local
`ProviderCallMetrics`，包含 latency、requested/returned model、system fingerprint、finish reason
和 token usage；缺失 usage 或 metrics MUST NOT 破坏合法业务输出。

`stop` SHALL 视为正常完成。`length`、`content_filter`、`tool_calls` 和
`insufficient_system_resource` MUST 视为 provider error。缺失或未知 finish reason MUST 在 metrics
中标记为 unavailable/unknown，但共享兼容层 MUST NOT 仅因此拒绝合法 content。

Provider audit、公开响应和持久化 audit MUST NOT 记录完整 prompt、完整模型输出、完整 Evidence Pack、
API key、reasoning content、本机绝对路径、system fingerprint 或 token 明细。Provider metrics MUST
NOT 进入 `/chat` 顶层字段或 `/chat.tool_calls`。

#### Scenario: Provider metrics 缺失不破坏回答

- **WHEN** provider 返回合法 content 但缺少 usage、system fingerprint 或 finish reason
- **THEN** 合法业务输出 SHALL 保持可用
- **AND** 缺失指标 SHALL 标记为 partial 或 unavailable

#### Scenario: 已知非完成 finish reason 安全失败

- **WHEN** provider 返回 `length`、`content_filter`、`tool_calls` 或
  `insufficient_system_resource`
- **THEN** provider MUST 返回空业务输出和安全 error class
- **AND** response-local metrics MAY 保留脱敏 finish reason 与 usage

#### Scenario: Provider audit 不泄露敏感内容

- **WHEN** 系统调用 fake provider 或 OpenAI-compatible provider
- **THEN** 内部 trace MAY 记录允许的 provider 调用摘要
- **AND** `/chat` 顶层响应和 `tool_calls` MUST NOT 包含 metrics、prompt、API key、完整模型输出或
  完整 Evidence Pack
