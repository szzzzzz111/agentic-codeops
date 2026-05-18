# 交接给下一轮 Chat

## 分支状态

```text
当前工作分支：feature/v6-agent-harness-kernel
当前基线分支：main
当前活跃 OpenSpec change：无
```

## 当前项目状态

RepoPilot 当前定位为面向代码仓库分析任务的可控 Code Agent Harness，不是替代通用 AI IDE 的编程助手。V1-V5 已进入 `main` 历史；V6 当前已重定向为 `v6-agent-harness-kernel`，目标是 Agent Harness Kernel + Router Kernel。

重要流程偏差：本轮用户要求先做项目状态理解，再进行 V6 阶段开发。Codex 实际越过了状态总结/阶段规划确认门，直接完成了 `v6-skill-aware-agent-loop` OpenSpec、测试、代码实现、文档更新和验证。该路线现在只作为历史 draft/偏差记录，不作为当前 V6 主线。

二次流程偏差：用户随后确认“V6 得重新开发”，Codex 又把该确认理解为可以直接实现，已切到 `feature/v6-agent-harness-kernel`，创建 `v6-agent-harness-kernel` OpenSpec/harness 边界，并新增 `app/harness/`、`tests/test_agent_harness_kernel.py` 与 `CodeAgent` 接入改动。之后用户完成 plan review，并确认“没问题就进行开发，按计划来”；当前 V6 Kernel 草稿已按批准后的计划保留并改造。

当前主链路：

```text
API -> ChatService(trace_id) -> CodeAgent -> AgentLoop -> ToolRegistry -> ToolExecutor -> file_tools
```

当前主链路仍以 `ToolExecutor.search_code` 为实际只读工具调用边界，前面增加了轻量 `AgentLoop` 和 `ToolRegistry` 调用前校验。

## 本轮完成

注意：当前 V6 已通过用户验收，已提交并归档；下一轮不应继续修改 V6，除非用户明确要求修复或返工。

- 从 `main` 创建过历史 draft 分支：`feature/v6-skill-aware-agent-loop`；该路线现在降级为历史偏差记录。
- 切换到当前工作分支：`feature/v6-agent-harness-kernel`。
- 创建当前 OpenSpec change：`openspec/changes/v6-agent-harness-kernel/`。
- 同步当前 V6 阶段 harness：
  - `.harness/allowed_files.md`
  - `.harness/review_checklist.md`
- 将 V6 plan 收敛并实现为四个最小运行时骨架：
  - `RequestRouter`
  - `ToolRegistry` 元数据和调用前校验
  - `AgentLoop`
  - `TraceEvent`
- 明确 `ProviderAdapter`、`ContextBuilder`、`SkillRegistry` 和 `SessionStore` 不在 V6 写运行时代码。
- 记录两次流程偏差：状态理解后提前实现、V6 重做后再次提前写代码。
- 按用户确认保留并改造 `app/harness/`、`tests/test_agent_harness_kernel.py` 和 `CodeAgent` 接入草稿，移除旧 Provider/Context/Skill/SessionStore runtime 方向。
- 提交 V6：`b1d6b03 Add V6 agent harness kernel`。
- 手动同步 V6 delta 到长期 specs，并归档到 `openspec/changes/archive/2026-05-18-v6-agent-harness-kernel/`。
- 清理历史 `v6-skill-aware-agent-loop` 空 active change 目录，避免 OpenSpec 继续误报活跃 change。

## V6 边界

已实现：

- `RequestRouter`：对输入请求做确定性路由，先只支持现有仓库搜索路径。
- `ToolRegistry`：登记只读低风险工具元数据，并在调用前校验工具存在、只读和风险等级；不负责 dispatch。
- `AgentLoop`：包装现有确定性搜索闭环，不引入真实 LLM 或复杂规划。
- `TraceEvent`：记录最小结构化事件，支撑后续审计。
- `AgentLoopRequest`、`RouteDecision`、`ToolSpec`、`TraceEvent` 和内部 `AgentLoopResult` 最小 contract。

V6 不做：

- 不实现 `ProviderAdapter`、`ContextBuilder`、`SkillRegistry`、`SessionStore` 运行时代码。
- 不接真实 LLM。
- 不执行 skill。
- 不自动修改代码。
- 不执行 shell 工具。
- 不提前做 RAG、Memory、Reflection、eval、PermissionPolicy、ApprovalGate、SandboxRunner、subagents 或长任务 Agent。

## 路线重定向建议

用户新增宏观要求：RepoPilot 要更偏工程化，不能只是玩具项目；但因为主要由个人使用 AI 开发，也不能走重型企业平台路线。后续应体现“轻量工程化”：

- 用清晰边界体现工程化，而不是堆服务数量。
- 用结构化 trace、tool_calls、memory audit 体现可审计。
- 用 OpenSpec、harness、pytest、ruff、verify 脚本体现可验证。
- 用 Provider/RAG/Memory/Skill 的接口化体现可替换。
- 默认实现保持轻量，外部依赖按阶段按需引入。

建议下一条主路线不是恢复历史 `v6-skill-aware-agent-loop` 小 draft，而是改成：

```text
V6  Agent Harness Kernel + Router Kernel
V7  Permission + Approval Gate
V8  Repo RAG Engineering
V9  Three-layer Memory
V10 ReAct / Long Task Agent
V11 Subagents + Worktree
V12 Personal Assistant Gateway
```

其中 V6 只建立 `RequestRouter`、`ToolRegistry`、`AgentLoop` 和 `TraceEvent` 四个最小运行时骨架；`ProviderAdapter`、`ContextBuilder`、`SkillRegistry` 和 `SessionStore` 留到后续阶段。当前 skill-aware draft 仅作为历史偏差和未来 skill 子能力参考。

## 本轮验证

- `openspec validate v6-agent-harness-kernel`：通过。
- `pytest tests/test_agent_harness_kernel.py`：9 passed。
- `pytest tests/test_chat_api.py`：6 passed。
- `ruff check app/harness app/agents/code_agent.py tests/test_agent_harness_kernel.py`：All checks passed。
- `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`：通过。
  - `pytest`：39 passed, 1 skipped。
  - `ruff check .`：All checks passed。
- `git diff --check`：通过，仅有 CRLF 换行提示。
- `openspec validate --all`：5 passed。
- 历史 `v6-skill-aware-agent-loop` draft 验证记录：`openspec validate v6-skill-aware-agent-loop`：通过。
- 历史 `v6-skill-aware-agent-loop` draft 验证记录：`pytest tests/test_chat_api.py`：8 passed。
- 历史 `v6-skill-aware-agent-loop` draft 验证记录：`powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`：通过。
  - `pytest`：32 passed, 1 skipped。
  - `ruff check .`：All checks passed。
- `git diff --check`：通过，仅有 CRLF 换行提示。

## 下一轮建议

1. 若要继续开发，先规划 V7：Permission + Approval Gate。
2. V7 开始前同步 `.harness/allowed_files.md` 和 `.harness/review_checklist.md`。
3. 不要把 Provider、RAG、Memory、Skill execution 或 SessionStore 提前塞进 V7，除非新 plan 明确改路线。
