# 交接给下一轮 Chat

## 当前分支

```text
feature/v4-skill-loader
```

## 当前项目状态

RepoPilot 当前定位为面向代码仓库分析任务的可控 Code Agent Harness，不是替代通用 AI IDE 的编程助手。V1、V2、V3 已合并到 `main`、`dev` 和 `feature/v3-agent-loop`。当前本地分支是 `feature/v4-skill-loader`，已经快进同步到最新 `main`。

V3 已完成统一工具执行边界：`/chat` 现在会通过 `CodeAgent -> ToolExecutor -> search_code` 使用只读仓库搜索，并返回真实 `related_files` 和 `tool_calls`。当前 Trace 是由 `ChatService` 创建的请求级 `trace_id`，随 `/chat` 响应返回；还不是完整持久化审计系统。

当前 V4 尚未实现，只进入设计阶段。V4 设计参考 DeepAgents 的 skills 方案，尤其是目录化 `SKILL.md`、YAML frontmatter、metadata-first 和 progressive disclosure 的分层思路。

已将 `.harness/rules.md` 从旧 V1 规则更新为当前通用 Harness 规则，并把本次流程问题沉淀为规则：新阶段先同步 allowed files/checklist，提交前检查状态和 diff，不混合阶段 commit。

## 本轮重点

- V3 已完成并合并：
  - `feature/v3-agent-loop`
  - `dev`
  - `main`
- 新增 V3 Agent Loop specs：
  - `specs/003-agent-loop/spec.md`
  - `specs/003-agent-loop/plan.md`
  - `specs/003-agent-loop/tasks.md`
- 更新 V3 实现阶段 harness：
  - `.harness/allowed_files.md`
  - `.harness/review_checklist.md`
- 新增轻量 `ToolExecutor`，当前只包装 `search_code`。
- 更新 `CodeAgent`，使用最小确定性关键词提取并调用 `ToolExecutor`。
- 更新 `/chat` 测试，覆盖 `UNIQUE_BUG_TOKEN` 命中、无命中、敏感文件不泄露和错误摘要脱敏。
- 更新 README、`docs/PROGRESS.md` 和 `docs/FEATURE_LIST.json`。
- 收尾同步项目定位：RepoPilot 是可控 Code Agent Harness，核心价值是可控、可审计、可验证、可扩展。
- 更新 `docs/ARCHITECTURE.md`，将当前链路同步为 `API -> ChatService(trace_id) -> CodeAgent -> ToolExecutor -> file_tools`。
- 回填 V1/V2 tasks，并将 V3 plan 同步为完成叙事。
- 创建并同步 `feature/v4-skill-loader` 到最新 `main`，但尚未写 V4 specs 或实现代码。
- 更新 V4 计划阶段 harness，只允许写 V4 specs、harness、progress、handoff 和必要入口文档，不开放运行时代码或测试代码。

## 已验证

```text
powershell -ExecutionPolicy Bypass -File scripts/verify.ps1
pytest: 16 passed
ruff check .: All checks passed
```

## 下一轮建议

下一轮建议：

1. 先写 `specs/004-skill-loader/spec.md`、`plan.md` 和 `tasks.md`。
2. 将 `.harness/allowed_files.md` 和 `.harness/review_checklist.md` 从“V3 收尾文档同步”切换到 V4 设计/实现范围。
3. V4 建议目标是 DeepAgents 风格的 Skill Metadata Loader：发现 `.agents/skills/*/SKILL.md`，解析 `name`、`description`、`path`。
4. V4 不执行 skill，不读取完整 skill 正文，不做 progressive disclosure，不接入 `/chat` 决策，不接真实 LLM。
5. 后续可以拆分为：
   - V5：Skill Content Loader / progressive disclosure，按需读取完整 `SKILL.md`。
   - V6：Skill-aware Agent Loop，基于 skill metadata 选择相关 skill。
   - V7 或以后：trace/tool/skill audit、eval、Reflection、RAG。
6. 保持高风险能力统一经过 `ToolExecutor` 增量加入。
7. 不要把 PermissionPolicy、ApprovalGate、SandboxRunner、eval、Reflection、RAG 或 Memory 写成已实现。

## 不要做

- 不接真实 LLM。
- 不自动修改代码。
- 不执行 shell 工具。
- 不加入复杂多 Agent。
- 不提前做 RAG、Memory、Reflection 或 eval。
- 不提前实现 PermissionPolicy、ApprovalGate 或 SandboxRunner。
- V4 不执行 skill，不把 skill 内容塞进 prompt，不做 skill-aware agent loop。
