# RepoPilot

RepoPilot 是一个面向代码仓库理解、受控 Patch 和验证闭环的本地 Coding Agent Harness。

它不是通用 AI IDE 或 AI 编程助手的替代品，而是把代码智能体执行过程收束在可观察、可审批、
可验证、可审计的本地边界内：先用仓库证据回答问题，再把修改请求收束为 patch proposal /
合法 pending patch 边界，经明确确认后隔离执行，并用固定验证命令和 SQLite 审计闭环交接。

## 核心能力

- Agent Loop：`POST /chat` 背后的轻量编排层，统一处理 memory、long task、assistant status、
  patch、verification、audit recovery、worktree lifecycle 和 repo search。
- repo-local hybrid RAG：deterministic query understanding、lexical search、本地 deterministic
  embedding、multi-query rewrite 和 rerank；默认不依赖外部向量库或网络。
- Evidence Pack / citation：内部 Evidence Pack 与字符级 Context Budget 约束 grounded answer，
  public response 保持 `trace_id`、`answer`、`related_files`、`tool_calls`。
- 受控 Patch + Verify：明确 patch 请求进入 proposal / validation 边界；合法 pending patch
  确认后才 apply，并可串联固定白名单 `pytest`、`ruff`、`verify`。
- Worktree 生命周期：确认后的 patch flow 在 detached locked worktree 中执行，支持 scoped
  inventory、inspection、re-verification、disposal/reconciliation 和 verified promotion。
- SQLite audit：repo-local `.repopilot/` 保存 memory、long task、patch、worktree 和脱敏 audit
  状态；公开查询只返回安全摘要。
- live model eval：独立 live provider evaluator、tracked PASS attestation / failure record 和脱敏
  本地报告；默认测试与 CI 仍保持离线 deterministic。

## 执行闭环

```text
User request
  -> AgentLoop
  -> repo-local hybrid RAG
  -> Evidence Pack / grounded answer
  -> patch proposal / pending patch boundary
  -> explicit confirm apply
  -> isolated worktree execution
  -> fixed-label verification
  -> verified promotion when explicitly confirmed
  -> redacted SQLite audit / status
```

## 快速开始

启动服务：

```bash
uvicorn app.main:app --reload
```

接口地址：

```text
http://127.0.0.1:8000
```

默认验证入口：

```bash
python -I scripts/verify.py
```

PowerShell host 可使用 `scripts/verify.ps1` 薄包装；实际检查顺序仍由同一个 Python 入口定义。

## 文档入口

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)：当前真实架构、边界和后续演进方向。
- [docs/PROGRESS.md](docs/PROGRESS.md)：阶段历史、验证记录和剩余债务。
- [docs/AGENT_RULES.md](docs/AGENT_RULES.md)：分支、修改、验证、review、文档职责和交接规则。
- [docs/FEATURE_LIST.json](docs/FEATURE_LIST.json)：可验收能力清单。
- [openspec/specs/](openspec/specs/)：长期 capability specs。
- [HANDOFF_TO_NEXT_CHAT.md](HANDOFF_TO_NEXT_CHAT.md)：下一轮 session 操作上下文。

## CLI

`repopilot` CLI 已实现为本地薄入口：它把命令映射为现有 `ChatService.handle_chat()`
请求，复用既有 AgentLoop、ToolExecutor、VerificationRunner、Worktree 和 Audit 边界；
不新增 `/chat` 字段，不改默认 CI，不引入网络依赖，也不绕过 patch 确认或验证白名单。

```text
repopilot ask "<question>"
repopilot patch "<request>"
repopilot patch confirm <patch_id>
repopilot patch confirm <patch_id> --verify verify
repopilot verify verify
repopilot status
repopilot audit latest
```

CLI 只接受固定验证标签 `verify`、`pytest`、`ruff`，拒绝附加 argv、管道、重定向、
环境变量注入和 unsafe patch id；patch id 必须匹配 `^patch_[A-Za-z0-9_]{1,122}$`。
CLI 不提供独立 Verified Patch Promotion 子命令；promotion 仅在既有 `/chat.answer`
交互中接受严格确认语法。

## 当前快照

- 已验收阶段：V1-V25 已归档；V25 `add-verified-patch-promotion` 已完成 runtime/tests、
  final verification、review triage、OpenSpec archive，并已合入和推送到 `main`。
- 当前 `/chat` contract：响应保留 `trace_id`、`answer`、`related_files`、`tool_calls`，
  不新增必需顶层字段。
- 当前主要运行时：hybrid repo RAG、grounded answer、Memory、Long Task Control Plane、
  Assistant Control Surface、Safe Patch Authoring、Verification Runner、Patch + Verify Loop、
  Persistent Audit / Recovery 和 V20-V25 worktree lifecycle。
- 当前 Verified Patch Promotion：仅精确确认的
  `confirm promote worktree <worktree_id>` / `确认提升 worktree <worktree_id>` 可提升当前
  scope 内 `verification_succeeded` + `applied_in_worktree` 的 retained worktree；写入源只使用
  stored controlled patch，并经既有审批 `patch_apply` 写入主工作区。
- 当前不默认接真实 LLM、外部 embedding/vector DB、真实 LLM rewrite/rerank、向量 memory、
  自动 memory 总结、后台任务、runtime subagents、connectors、notifications、自动
  commit/merge/push、branch/PR automation 或 `git worktree prune`。

## 请求示例

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "u001",
    "session_id": "s001",
    "message": "帮我分析 UNIQUE_BUG_TOKEN",
    "repo_path": "./mock_repo"
  }'
```

响应示例：

```json
{
  "trace_id": "trace_xxx",
  "answer": "基于仓库证据，问题 `帮我分析 UNIQUE_BUG_TOKEN` 的相关实现位于 app/example.py:1-3。",
  "related_files": ["app/example.py"],
  "tool_calls": [
    {
      "tool_name": "repo_rag",
      "keyword": "UNIQUE_BUG_TOKEN",
      "question_type": "code_location",
      "retrieval_mode": "hybrid",
      "status": "success",
      "result_count": "1"
    }
  ]
}
```

## 文档职责

README 只保留项目门面、快速开始、CLI 入口、当前能力快照和文档导航。详细模块说明、阶段历史、
验证 evidence、未清债务和长期规格分别由 `docs/ARCHITECTURE.md`、`docs/PROGRESS.md`、
`docs/FEATURE_LIST.json` 和 `openspec/specs/` 承担。

OpenSpec、Harness、review checklist、Codex/OpenCode skills、Superpowers、MCP 和 plugin
均是开发流程或外部协作范式，不是 RepoPilot runtime 能力。
