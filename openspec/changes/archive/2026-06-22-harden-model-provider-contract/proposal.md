## Why

RepoPilot 已提供可选 OpenAI-compatible provider，但当前共享请求契约只能表达 grounded text，
Long Task Planner 与 Model Patch AuthoringProvider 只能把各自 JSON 指令重复拼进普通 query，
provider 也缺少结构化输出前置校验、finish reason 和脱敏调用指标。真实 provider 联调前必须先把
这些共享边界收紧，否则 JSON 任务、错误降级和后续 eval 指标都无法稳定验收。

## What Changes

- 为 `ModelProviderRequest` 增加向后兼容的 `output_mode` 和调用方提供的
  `StructuredOutputInstruction`，禁止 provider 根据 `question_type` 猜测业务 schema。
- 在任何 HTTP 调用前校验结构化输出 instruction；非法 mode、缺失 instruction、非法 JSON example
  或非法 token 上限均 fail closed，且不得发出网络请求。
- 让 provider 只负责 JSON object 基础解析；Planner 与 Patch 继续负责各自业务字段、step、
  citation、路径和 diff 校验。
- 删除 Planner/Patch query 中重复的 JSON 格式指令，并要求 Planner 在解析前显式检查 provider
  status。
- 增加可选、脱敏的 `ProviderCallMetrics`，并定义 thinking、finish reason、usage 缺失和兼容端点
  的失败语义。
- 保持默认 fake provider、默认 Patch wiring、`/chat` contract 和默认离线验证不变。
- 本 change 不执行真实网络 smoke/eval，不创建 V24；live eval 由后续独立 change 承担。

## Capabilities

### New Capabilities

- 无。

### Modified Capabilities

- `grounded-answer-model-provider`：扩展共享 Model Provider 请求、响应、配置、错误和 metrics 契约。
- `long-task-agent-execution`：Planner 使用显式结构化输出 instruction，并在业务解析前检查 provider
  status。
- `safe-patch-authoring`：Model Patch AuthoringProvider 使用显式结构化输出 instruction，保持业务
  schema、citation 和 diff 校验职责。

## Impact

- Code: `app/providers/model_provider.py`, `app/longtask/planner.py`,
  `app/patching/provider.py`
- Tests: provider、grounded answer、Long Task、Patch Authoring、AgentLoop/API 回归
- Specs: 上述三个长期 capability 的 delta specs
- Harness/docs: 当前阶段 allowed files、review checklist，以及事实发生变化后的 PROGRESS/HANDOFF
- API/dependencies/storage: 无公开 API、依赖或持久化 schema 变化
