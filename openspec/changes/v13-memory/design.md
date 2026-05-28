## Context

当前主链路是：

```text
API -> ChatService(trace_id) -> CodeAgent -> AgentLoop
  -> QueryUnderstanding/SearchPlan -> QueryRewriteProvider
  -> ToolRegistry -> PermissionPolicy -> ApprovalGate
  -> ToolExecutor(repo_rag) -> HybridRepoRetriever -> Reranker -> EvidencePack/ContextBudget
     -> GroundedAnswerGenerator -> ModelProvider
     -> LexicalRepoRetriever + EmbeddingRepoRetriever -> file_tools
```

V13 在 `AgentLoop` 内增加 Memory 边界。Memory 是 RepoPilot 本地状态能力，不是仓库代码修改能力；默认只写目标 repo 的 `.repopilot/memory.sqlite3`，并且 `.repopilot/` 必须被 git 忽略。

## Goals / Non-Goals

**Goals:**

- 实现真实 SQLite-backed PREF/LTM 和进程内 STM。
- 支持明确 memory 聊天指令，并在命中时确认优先、不执行 repo 检索。
- 普通请求读取 PREF/LTM 并记录内部 memory audit。
- 让 PREF 影响回答表达偏好，但不覆盖 repo evidence 和 citation validation。
- 保持 `/chat` 顶层响应 contract 不变。

**Non-Goals:**

- 不实现向量 memory、mem0 集成、外部数据库、自动 LLM 总结、跨 repo 智能召回或 context compression。
- 不新增公开 memory 管理 API 或 `/chat` 必需顶层字段。
- 不让 Memory 绕过 `ToolExecutor`、`PermissionPolicy`、`ApprovalGate`、Evidence Pack 或 grounded answer citation validation。

## Decisions

### Decision 1: Repo-local SQLite 是默认持久存储

V13 使用 stdlib `sqlite3`，默认数据库路径为 `Path(repo_path) / ".repopilot" / "memory.sqlite3"`。该目录是本地状态目录，不属于仓库代码；`.gitignore` MUST 包含 `.repopilot/`。

如果 repo 不存在、无法 resolve 或 `.repopilot/` 不可写，memory 指令 MUST 返回脱敏的无法写入回答，且 MUST NOT 继续执行 repo_search。普通 repo_search 中 memory 读取失败时，系统 MUST 继续检索并记录 `memory_unavailable` audit。

### Decision 2: repo_key 使用稳定规范化路径 hash

`repo_key` MUST 按以下顺序计算：

1. 使用 `Path(repo_path).resolve()` 解析真实绝对路径。
2. 将 resolved path 转换为 POSIX 分隔符字符串。
3. Windows 下对该字符串执行 lower-case。
4. 对规范化字符串计算稳定 hash。

内部存储 MAY 保存完整 hash；audit MUST NOT 暴露原始绝对路径或 DB 路径。

### Decision 3: Memory 类型和隔离维度

Memory kind 固定为 `STM`、`LTM`、`PREF`。

- `PREF`: 按 `user_id` 隔离，可跨 repo 复用表达偏好。
- `LTM`: 按 `user_id + repo_key` 隔离，保存用户明确要求记住的项目事实。
- `STM`: 按 `user_id + session_id` 隔离，使用进程内 store 保存短期会话信息。

### Decision 4: 明确指令优先于 repo_search

Memory parser 先将全角冒号 `：` 归一化为半角 `:`。支持：

- `记住: ...`
- `请记住...`
- `忘记: ...`
- `请忘记...`
- `remember: ...`
- `forget: ...`

命中 memory 指令后，AgentLoop MUST 直接返回确认式回答，`related_files=[]`，`tool_calls=[]`，并且 MUST NOT 调用 `repo_rag`。

### Decision 5: 记忆格式和分类

写入内容优先使用 `key=value`。无 `=` 时作为 note 存储，并由内容生成稳定 key。

分类规则：

- `stm:` 或 `会话:` 写入 STM。
- `pref:` 或 `偏好:` 写入 PREF。
- `project:` 或 `项目:` 写入 LTM。
- 未标注时，包含“默认”、“喜欢”、“以后”等偏好词则写入 PREF。
- 其他未标注内容写入 LTM。

同一 scope、kind、key 的新值 MUST 覆盖旧值，并在 audit 中记录 `replaced=true`。STM 使用进程内 `InMemorySessionMemoryStore` 写入 `user_id + session_id` scope；PREF/LTM 使用 SQLite。

### Decision 6: 删除先 key 后内容包含

删除指令先按 key 精确匹配删除。找不到 key 时，再按 value 内容包含匹配删除。回答返回删除数量；audit 只记录 kind、scope、deleted_count 和 status，不记录完整删除内容。

### Decision 7: Memory 只影响表达偏好

V13 MAY 使用 PREF 影响回答表达，例如中文优先、简洁度偏好。代码事实仍 MUST 来自 repo retrieval、Evidence Pack 和 citation validation。LTM 可进入内部 memory summary，但不得作为 grounded answer 合法 citation 的来源。

## Error Behavior

- memory command 写入/删除失败：返回脱敏失败回答，不执行 repo_search。
- 普通请求 memory read 失败：记录 `memory_unavailable`，继续 repo_search。
- SQLite 初始化失败：同 memory read/write 失败处理。
- parser 未命中明确 memory 指令：走原有 route 逻辑。

## Rollback

V13 不修改 `/chat` 响应 schema。若 Memory 出现问题，可禁用 AgentLoop 的 MemoryManager 注入，回到 V12 行为；repo-local `.repopilot/` 本地状态可由用户删除。
