# 执行约束规则

本文件记录当前仓库通用 Harness 约束，不绑定单一历史版本。阶段级允许文件和 review 项以 `.harness/allowed_files.md`、`.harness/review_checklist.md` 为准。

## 当前定位

RepoPilot 是面向代码仓库分析任务的可控 Code Agent Harness。项目目标不是替代通用 AI 编程助手，而是让 Agent 的工具调用、安全边界、执行追踪、测试、review 和 handoff 可验证、可审计、可交接。

## 当前已实现边界

当前稳定主链路：

```text
API -> ChatService(trace_id) -> CodeAgent -> ToolExecutor -> file_tools
```

- API 只处理 HTTP 请求和响应。
- `ChatService` 创建请求级 `trace_id` 并编排 Agent。
- `CodeAgent` 做最小确定性决策和结果组织。
- `ToolExecutor` 统一收口工具调用，当前只包装只读 `search_code`。
- `file_tools` 提供安全只读仓库工具，不处理 HTTP 或 Agent 决策。
- Trace 当前是请求级 `trace_id`，不是持久化审计系统。

## 阶段推进规则

- 每次开始新阶段前，先确认当前分支、工作区状态和最近提交。
- 每次进入新阶段前，先更新 `.harness/allowed_files.md` 和 `.harness/review_checklist.md`，再写 specs 或代码。
- 每次提交前，检查 `git status --short --branch`、`git diff --name-only` 和 `git diff --check`。
- 每次提交后，如要进入下一阶段，先确认 handoff、progress、specs、harness 是否同步。
- 不要在一个 commit 中混入上一阶段收尾和下一阶段实现。
- 如果发现 handoff、progress、specs、harness 任一文件仍指向旧分支或旧阶段，先修文档，再继续实现。

## 项目级 OpenSpec 使用原则

- 本仓库可以使用 OpenSpec 作为项目级 SDD 工作流，用于 proposal、design、tasks、spec delta 和 archive。
- OpenSpec 只约束 RepoPilot 的开发流程，不是 RepoPilot runtime 功能。
- Codex 仅使用本仓库内 `.codex/skills` 和仓库文档执行 OpenSpec 流程；不要要求安装 `C:\Users\...\ .codex\prompts` 等全局 prompts。
- OpenCode 可以使用仓库内 `.opencode`。
- GitHub Copilot 当前不保留仓库内 `.github` OpenSpec 提示文件；如需启用，必须单独说明原因并更新 allowed files。
- 不要因为接入 OpenSpec 而引入 MCP server、plugin runtime、skill 执行、动态工具注册或 `/chat` 决策变更。
- Superpowers 只作为 Codex 开发本仓库的项目级能力卡片，不是 RepoPilot 对外暴露的 skill 系统。

## TDD 与验证规则

- 先写规格、任务和验收标准，再开放实现文件。
- 实现阶段必须配套测试；不能只靠手动检查或 LLM review。
- 默认验证命令：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify.ps1
```

- 验证至少应覆盖 `pytest` 和 `ruff check .`。
- 如果验证无法运行，最终说明必须写清楚原因。

## 禁止项

- 不接真实 LLM，除非当前阶段明确开放。
- 不自动修改代码，除非当前阶段明确开放。
- 不执行 shell 工具，除非当前阶段明确开放并经过新的安全设计。
- 不绕过 `ToolExecutor` 增加高风险工具。
- 不把工具逻辑堆到 API 层、`main.py` 或具体 router 中。
- 不把 Roadmap 能力写成已实现。
- 不提前实现 PermissionPolicy、ApprovalGate、SandboxRunner、Reflection、eval、RAG、Memory 或复杂多 Agent。
- 不提交缓存文件、虚拟环境、本地环境变量或临时产物。

## 连续执行授权与正式 Review 门

- “一路实现到合并/推送”等连续执行授权只授权动作序列，不授权跳过正式 code review、Stage Debt Sweep、验证或 closeout gate。
- 正式 code review 必须发生在最终 runtime/tests 变更之后，并在 archive/merge 前给出可见的 findings 或明确的零 findings 结论。
- 测试通过、零散自检和 checklist 自行勾选不能替代正式 code review 证据。
- merge 后发现 P0/P1 时，必须恢复 closeout 阻断，持久化 findings，并在修复复核前禁止下一阶段。
