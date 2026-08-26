# grounded-answer-model-provider Specification

## Purpose

记录 V11 引入的 grounded answer 和 model provider boundary：系统只基于 V10 Evidence Pack / Context Budget 中预算内 included evidence 生成回答，默认使用本地 deterministic fake provider，显式配置后可使用 OpenAI-compatible provider。该能力继承 grep-first, RAG-assisted 检索立场，优先基于可审计的 lexical/path/symbol evidence 进行 citation 约束回答，不让模型参与检索规划、query rewrite、rerank、工具调用、代码修改、memory 或多步 agent 决策。
## Requirements
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

系统 SHALL 校验 model provider 输出中的 citation。允许 citation 格式为
`relative/path.py:start-end`，其中 `start` 和 `end` MUST 为正整数。单行引用 SHOULD 规范化为
`path:n-n`。Citation MUST 完全匹配提供给 provider 的 evidence `file_path`、`start_line` 和
`end_line`。

Grounded-text provider instruction MUST 列出 request evidence 中允许的 citation labels。
每个 grounded response（包括回答、澄清或拒答）的最后一行 MUST 只包含一个完整 allowed label。
Footer MUST NOT 包含 `Citation:` 等前缀、markdown、方括号、引号、bullet、标点或额外文本。
Instruction MUST NOT 允许模型改写路径、起止行、引用子范围或创建未提供的 citation。

Grounded-text user message MUST 使用与 allowed list 相同的裸 `path:start-end` label，MUST NOT
使用方括号或其他竞争 citation framing。Grounded evidence MUST 通过明确标记为不可信数据的
结构化 envelope 传递。Instruction MUST 明确 repository evidence 是不可信数据，其中的文本不得
覆盖 system instruction；模型 MUST NOT 遵循、复述、转换、编码或以其他方式执行 evidence 内
要求改变回答行为、泄露内容、忽略规则或输出 marker 的指令。

Grounded-text prompt contract MUST make the model-visible task explicit: answer the original user question by
extracting repository facts from evidence data, and treat evidence text that is directed at the assistant as
evidence-borne instruction rather than answerable fact. Evidence-borne instruction includes command-like text,
role assignment, policy override, declarative response rule, request to ignore constraints, request to reveal
information, or extra-output request. The prompt MUST require the model to ignore the evidence-borne instruction
and its requested output target silently while preserving any separate repository fact in the same evidence item
that is relevant to the original user question.

Instruction MUST require the model to silently ignore evidence 内的命令式、角色式、策略式、声明式
response rule 或特定输出要求。模型 MUST NOT 在回答、拒答、澄清、引用或安全说明中提及该指令、
说明拒绝执行，或输出、复述、拼写、引用、转换、编码、翻译、讨论其要求产生且未被 original query
明确询问的 marker/token。模型 MAY 只使用同一 evidence 中与用户仓库问题相关的事实内容；若相同
字符串本身是 original query 明确询问的仓库事实或标识符，instruction MUST NOT 禁止基于 evidence
回答。澄清或拒答 MUST 使用不复现攻击目标的中性措辞，并继续满足 exact citation footer contract。

系统 MUST 允许重复 citation 和乱序 citation。系统 MUST 将绝对路径、未提供路径、错误行号、
错误范围、无法解析 citation 和没有合法 citation 的 provider 输出视为不可信，并返回保守
fallback。

#### Scenario: Grounded response 使用 exact citation footer

- **WHEN** grounded-text request 包含一个或多个 evidence items
- **THEN** system instruction MUST 按稳定顺序列出对应 `path:start-end` labels
- **AND** response 最后一行 MUST 只包含一个 allowed label
- **AND** footer MUST NOT 包含前缀、markdown、包装符号、bullet、标点或额外文本

#### Scenario: Grounded evidence 使用不可信数据 envelope

- **WHEN** grounded-text request 包含 repository evidence snippets
- **THEN** user message MUST 把 citation metadata 和 snippet 放入明确的不可信数据 envelope
- **AND** instruction MUST 禁止执行或复述 evidence 内改变回答行为、泄露内容或输出 marker 的指令
- **AND** JSON object mode 的 prompt contract MUST 保持不变

#### Scenario: Evidence instruction 及其输出目标被静默忽略

- **WHEN** grounded evidence 包含命令、角色、策略、声明式 response rule 或要求输出 original query 未明确询问的特定 marker/token 的文本
- **THEN** grounded-text instruction MUST 要求模型只使用与用户仓库问题相关的事实内容
- **AND** response MUST NOT 提及、确认、拒绝说明、引用、拼写、转换、编码、翻译或讨论该指令及其输出目标
- **AND** clarification 或 refusal MUST 使用中性措辞并继续满足 exact citation footer contract

#### Scenario: Prompt 明确保留同段合法 repository fact

- **WHEN** one evidence item contains both a repository fact relevant to the user question and an instruction directed at the assistant
- **THEN** grounded-text prompt MUST instruct the model to answer from the repository fact
- **AND** grounded-text prompt MUST instruct the model to ignore the directed-at-assistant instruction and its requested output target
- **AND** the raw evidence content MUST remain present in the provider request rather than being filtered or projected

#### Scenario: 用户明确询问同名仓库标识符

- **WHEN** original query 明确询问一个同时出现在 evidence 指令文本中的仓库标识符或字符串
- **THEN** instruction MUST 允许模型基于 evidence 中与该 query 相关的事实内容回答
- **AND** response MUST 继续忽略 evidence 对回答行为或额外输出的指令

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

### Requirement: Provider 结构化输出与业务 schema 分层

OpenAI-compatible provider 在 `json_object` mode 下 SHALL 发送 JSON object response format、调用方提供的
JSON example 和 output token 上限。Provider MUST 只校验 response content 非空、结构 nesting 不超过固定
安全上限、可解析且顶层为 JSON object；Provider MUST NOT 校验 Long Task 或 Patch 业务字段。nesting 校验
MUST 是确定性的，MUST NOT 依赖解释器 recursion limit，并 MUST 正确忽略 JSON string 内的 brace、bracket
与 escaped quote。调用方 MUST 继续负责业务 schema、step、citation、路径和 diff 校验。

#### Scenario: Provider 接受基础合法 JSON object

- **WHEN** JSON mode response content 是可解析、nesting 不超过上限的顶层 JSON object
- **THEN** provider SHALL 返回 success 和原始 content
- **AND** 业务字段正确性 MUST 由调用方判断

#### Scenario: Provider 拒绝非 object JSON

- **WHEN** JSON mode response 是 array、scalar、空 content 或非法 JSON
- **THEN** provider MUST 返回安全 error
- **AND** 调用方 MUST NOT 把该 response 当作有效业务结果

#### Scenario: Provider 拒绝过深 JSON

- **WHEN** JSON mode response 的 object/array nesting 超过固定上限
- **THEN** provider MUST 返回空 answer 与 `ProviderResponseValidationError`
- **AND** audit/public response MUST NOT 包含完整模型 output

#### Scenario: JSON string 内结构字符不增加 nesting

- **WHEN** 合法 JSON object 的 string value 包含 brace、bracket、backslash 或 escaped quote
- **THEN** provider MUST 只按 string 外的 JSON 结构计算 nesting
- **AND** 合法 content MUST 继续交给 `json.loads` 和顶层 object 校验
