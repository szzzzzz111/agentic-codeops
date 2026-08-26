## MODIFIED Requirements

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
