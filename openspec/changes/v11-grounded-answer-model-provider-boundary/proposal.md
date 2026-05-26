## Why

V10 已经把 hybrid repo RAG 结果整理为内部 Evidence Pack，并用 Context Budget 限制可进入后续上下文的 snippets。但 `/chat` 的回答仍停留在“检索了关键词并列出 citation”的机械摘要，尚未把证据组织成可读、可审计的 grounded answer。

V11 需要在不改变 `/chat` 顶层 contract 的前提下，建立 Grounded Answer / Model Provider Boundary：默认使用本地 deterministic fake provider 保持验证稳定，并允许通过显式配置启用 OpenAI-compatible provider，用于小米 MiMo/Mino 等兼容接口。

## What Changes

- 新增 Grounded Answer 生成边界：只消费 V10 预算内 included evidence snippets 和 citation metadata。
- 新增 Model Provider 边界：默认 fake provider；可选 OpenAI-compatible provider。
- 将 `httpx` 明确提升为运行时依赖，用于可选真实 provider；默认验证不得依赖网络或真实 key。
- 对模型输出执行 citation 校验；无证据、无合法 citation、越界 citation、provider 失败时返回保守 fallback。
- 将 provider 调用摘要写入内部 trace/audit，但不暴露完整 prompt、完整模型输出、完整 Evidence Pack、API key 或本机绝对路径。
- 保持 `/chat` 顶层响应 contract：`trace_id`、`answer`、`related_files`、`tool_calls`。
- 明确不做 query rewrite、rerank、memory、context compression、SandboxRunner、skill execution 或多 agent orchestration。

## Capabilities

### New Capabilities

- `grounded-answer-model-provider`: 记录 grounded answer、provider boundary、citation validation 和 provider audit 规则。

### Modified Capabilities

- `agent-loop-tool-execution`: 默认 Kernel 仍保持确定性，但允许 V11 provider boundary 在显式配置下调用真实 model provider。
- `chat-api`: `/chat` schema 不新增必需顶层字段，但 `answer` 可由 grounded answer pipeline 生成。

## Impact

- Code: `app/answering/**`, `app/providers/**`, `app/harness/kernel.py`, `app/agents/code_agent.py`, `pyproject.toml`
- Tests: `tests/test_model_provider.py`, `tests/test_grounded_answer.py`, `tests/test_agent_harness_kernel.py`, `tests/test_chat_api.py`
- Docs: `README.md`, `docs/ARCHITECTURE.md`, `docs/PROGRESS.md`, `docs/FEATURE_LIST.json`, `HANDOFF_TO_NEXT_CHAT.md`
- OpenSpec / Harness: `openspec/changes/v11-grounded-answer-model-provider-boundary/**`, `openspec/specs/grounded-answer-model-provider/spec.md`, `openspec/specs/agent-loop-tool-execution/spec.md`, `openspec/specs/chat-api/spec.md`, `.harness/allowed_files.md`, `.harness/review_checklist.md`
- Dependencies: `httpx` becomes a runtime dependency; real provider remains opt-in via environment variables.
