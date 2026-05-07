# 交接给下一轮 Chat

## 当前分支

```text
feature/v2-file-tools
```

## 当前项目状态

RepoPilot 当前已经完成 V1 API 骨架和 V2 安全文件工具层。`/chat` 仍使用模拟 `CodeAgent`，V2 文件工具还没有接入智能体循环。

## 本轮重点

- 文档统一中文化。
- 清理 git 中被跟踪的 Python 缓存文件。
- 新增 `.gitignore`。
- 新增最小 Harness V0：
  - `AGENTS.md`
  - `docs/ARCHITECTURE.md`
  - `docs/AGENT_RULES.md`
  - `docs/PROGRESS.md`
  - `docs/FEATURE_LIST.json`
  - `HANDOFF_TO_NEXT_CHAT.md`
  - `scripts/verify.ps1`

## 已验证

```text
pytest: 13 passed
```

`ruff` 当前环境未安装。`scripts/verify.ps1` 会在找不到 ruff 时提示跳过。

## 下一轮建议

下一轮进入 V3 前建议：

1. 确认 V2 改动已 commit。
2. 从 `dev` 或当前集成点创建 `feature/v3-agent-loop`。
3. 先写 `specs/003-agent-loop/`。
4. 引入轻量 `ToolExecutor`。
5. 让 `CodeAgent` 通过 `ToolExecutor` 调用 `search_code` / `read_file`。
6. `/chat` 返回真实 `related_files` 和 `tool_calls`。

## 不要做

- 不接真实 LLM。
- 不自动修改代码。
- 不执行 shell 工具。
- 不加入复杂多 Agent。
- 不提前做 RAG、Memory、Reflection 或 eval。
