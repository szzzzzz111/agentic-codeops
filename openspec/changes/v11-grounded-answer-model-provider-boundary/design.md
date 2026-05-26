## Context

当前主链路是：

```text
API -> ChatService(trace_id) -> CodeAgent -> AgentLoop
  -> QueryUnderstanding/SearchPlan
  -> ToolRegistry -> PermissionPolicy -> ApprovalGate
  -> ToolExecutor(repo_rag) -> HybridRepoRetriever -> EvidencePack/ContextBudget
     -> LexicalRepoRetriever + EmbeddingRepoRetriever -> file_tools
```

V10 已经在 successful retrieval 后构建内部 Evidence Pack，并记录 `evidence_pack_summarized` trace。V11 只在 retrieval 完成后增加回答生成边界，不改变 query understanding、retrieval、permission、approval 或 safe file tools。

## Goals / Non-Goals

**Goals:**

- 用预算内 included evidence 生成 grounded answer。
- 定义 `ModelProvider` 边界，默认 fake provider，显式配置启用 OpenAI-compatible provider。
- 允许通过 `REPOPILOT_MODEL_PROVIDER=fake|openai_compatible`、`REPOPILOT_MODEL_BASE_URL`、`REPOPILOT_MODEL_API_KEY`、`REPOPILOT_MODEL_NAME` 和 `REPOPILOT_MODEL_TIMEOUT_SECONDS` 配置 provider。
- 校验模型输出 citation，只允许引用提供给 provider 的 evidence citation。
- 在内部 trace/audit 中记录 provider name、model、status、latency/error class 和 fallback reason。
- 保持 `/chat` 顶层响应 contract 不变。

**Non-Goals:**

- 不让模型参与检索规划、query rewrite 或 rerank。
- 不让模型回查工具或读仓库文件。
- 不实现 memory、context compression、SandboxRunner、skill execution、多 agent 或 ReAct loop。
- 不把小米 MiMo/Mino 写死到主链路；它只是 OpenAI-compatible provider 的一种配置。
- 不支持厂商特有参数如 `enable_thinking`；后续可单独扩展。

## Decisions

### Decision 1: Grounded Answer 独立成回答生成子模块

新增 `app/answering/`，负责把 `EvidencePack` 转成 provider input、调用 provider、校验 citation、生成 fallback 和 provider audit summary。该模块不直接读取仓库、不执行工具、不做权限决策。

### Decision 2: Provider 默认 fake，真实 provider 显式启用

默认 provider 为 deterministic fake provider，以保证 `pytest`、`ruff` 和 `scripts/verify.ps1` 不依赖网络、密钥或模型输出稳定性。真实 OpenAI-compatible provider 仅在环境变量显式配置后启用。

### Decision 3: Provider 输入只包含预算内证据

Provider 只接收 original query、question type、included evidence snippets 和 citation metadata。`omitted` / `truncated` snippets 不传入 provider；相关 counts 仅用于内部 audit。

### Decision 4: Citation 校验是硬边界

允许 citation 格式为 `relative/path.py:start-end`。单行引用规范化为 `path:n-n`。解析时允许 citation 后紧跟中文/英文标点、括号或空白，但 citation 本体必须完全匹配已提供 evidence 的 `file_path/start_line/end_line`。

重复 citation 和乱序 citation 允许。引用未提供路径、绝对路径、错误行号、错误范围或无法解析格式，视为越界。有 included evidence 但模型输出没有合法 citation 时降级为保守 fallback。

### Decision 5: Audit 摘要脱敏

Provider audit 只记录 provider name、model、status、latency/error class 和 fallback reason。不得记录完整 prompt、完整模型输出、完整 Evidence Pack、API key、本机绝对路径或内部 trace 细节。`tool_calls` 继续只包含工具调用摘要，不包含 provider prompt 或 response。

### Decision 6: `httpx` 是显式批准的运行时依赖

V11 允许将 `httpx` 加入 `[project].dependencies`。OpenAI-compatible provider 使用 `httpx`，测试必须通过 mock transport 覆盖，不把真实网络调用放入默认验证。

## Error Behavior

- 无 included evidence：不调用真实 provider，返回无法基于仓库证据回答的 fallback。
- Provider timeout、HTTP error、异常响应或未知异常：返回 fallback，并记录 error class。
- Provider 输出无合法 citation 或存在越界 citation：返回 fallback，并记录 fallback reason。
- ToolExecutor / repo retrieval error：沿用现有工具失败回答，不伪造 grounded answer。

## Rollback

V11 不做持久化迁移。若 provider boundary 有问题，可回退到 V10 的 retrieval answer 生成路径；`/chat` schema 无需迁移。
