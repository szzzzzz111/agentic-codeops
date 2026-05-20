## Context

RepoPilot 当前不是通用 AI IDE，而是面向代码仓库分析任务的可控 Code Agent Harness。V8 的目标不是一次性接入完整 RAG 平台，而是在现有只读工具边界内补上 repo-local RAG 的最小工程骨架。

## Design

### Query Understanding

`QueryUnderstanding` 是 deterministic 层，不调用 LLM。它根据用户消息提取：

- `question_type`: `code_location`、`implementation_explanation`、`call_relationship`、`test_or_validation`、`file_summary`、`unknown`
- `keywords`: 普通关键词和错误词
- `symbols`: 函数、类、常量、异常名、snake_case/camelCase 标识符
- `path_hints`: 文件名、扩展名、路径片段
- `max_results`: 当前固定为轻量默认值

`SearchPlan` 只描述检索计划，不执行检索，也不承担权限决策。`embedding`、`vector` 等能力状态词不会作为普通检索关键词进入 lexical retrieval，以避免把“是否实现向量能力”的路线问题误检索成代码问题。

### Lexical Repo RAG

Repo RAG 使用现有安全文件边界读取仓库文本文件，跳过敏感文件、隐藏目录、忽略目录和二进制文件。文本按小段 chunk：

- `chunk_id`: `file_path:start_line-end_line`
- `file_path`: 相对 repo 路径
- `start_line` / `end_line`: 1-based 行号
- `text`: chunk 文本

Lexical scorer 采用确定性加权：

- exact token match
- symbol match
- path / filename match
- keyword match

检索结果按分数排序并去重，输出 citation。V8 不做 embedding、rerank 或语义召回。

### Agent Loop Integration

`AgentLoop` 保持 V7 的权限/审批顺序：

```text
route -> query understanding -> registry lookup -> permission policy -> approval gate -> lexical repo RAG
```

`related_files` 来自 citation 文件路径。`tool_calls` 继续作为审计摘要，V8 repo-local lexical retrieval 的 `tool_name` 为 `repo_rag`，并记录本次检索的 query、question_type、retrieval_mode、status 和结果数。权限检查仍复用已注册的只读 `search_code` 能力边界。

### Capability Status Questions

当用户询问 embedding、Milvus、Elasticsearch、PgVector、Qdrant、memory 或 vector 等能力是否已实现时，`AgentLoop` 可以返回固定能力状态说明，明确 V8 只实现 lexical repo RAG。该分支不执行 repo retrieval，不返回 `related_files` 或 `tool_calls`。

### Reference Projects

以下项目只作为后续制定 plan 的参考资料，不是 RepoPilot runtime dependency：

- `ragent`: RAG 顺序、意图识别、多通道检索、证据组装。
- `agentic-rag-for-dummies`: hybrid retrieval、parent-child chunk、context compression。
- `mem0`: keyword/entity boost、semantic + lexical fusion、memory 路线。
- `AGI-assistant`: 分阶段架构、embedding fallback、STM/LTM/PREF。
- `openai-cs-agents-demo`: triage、guardrail、handoff，留给后续 agent routing。
- `learn-claude-code`、`build-your-own-openclaw`、`agents-from-scratch`、`DeepAgents`、`DeerFlow`、`Clawd-Code`: context、harness、task/subagent/memory 方向的远期参考，不进入 V8 主体。

## Non-Goals

- 不接 Milvus、Elasticsearch、PgVector、Qdrant 或 PostgreSQL。
- 不做 LLM rewrite、LLM intent classification、LLM rerank。
- 不新增 `/chat` 顶层字段。
- 不把参考项目写入 README 当前能力。
