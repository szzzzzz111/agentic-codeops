# 项目进度

RepoPilot 当前定位为面向代码仓库分析任务的可控 Code Agent Harness。它不试图替代通用 AI IDE，而是围绕 Agent 工具调用边界、只读安全工具、执行追踪、可验证测试、review checklist 和 handoff 机制，构建可审计、可扩展的代码智能体执行框架。

## 当前状态

- 当前工作分支：`feature/v6-agent-harness-kernel`；基线分支 `main`
- 当前阶段：V6 `v6-agent-harness-kernel` 已完成实现、验证、用户验收、提交和 OpenSpec 归档；暂无活跃开发阶段
- 当前主流程：`/chat` 已通过 `CodeAgent -> AgentLoop -> ToolRegistry -> ToolExecutor -> search_code` 使用只读仓库搜索；`/chat` 顶层响应结构保持不变
- 当前工具层：`list_files`、`read_file`、`search_code` 已实现
- 当前 V4/V5 状态：已实现 Skill Metadata Loader、Skill Content Loader；skill-aware loop 仅作为历史 draft/偏差记录，不作为当前 V6 主线；仍不执行 skill
- 当前 OpenSpec 状态：已初始化项目内 OpenSpec、OpenCode 和 `.codex/skills`；不安装 Codex 全局 prompts；不保留 `.github` OpenSpec 生成物

## 流程偏差记录

- 2026-05-17，用户要求“先进行一个项目的状态理解，然后再进行 v6 的阶段开发”。本轮应先输出项目状态理解、提出 V6 阶段规划和边界，并等待用户确认后再进入实现。
- 实际执行中，Codex 直接从状态理解推进到 V6 OpenSpec、测试、代码实现、文档更新和验证，越过了用户确认门。
- 历史 V6 skill-aware 空 draft 已清理；当前 V6 Kernel 变更已在用户 review 后保留、改造、提交并归档。
- 后续同类请求中，如果用户要求“先理解状态”或“先规划”，Codex 必须停在总结/方案确认点，不得自动进入实现。
- 2026-05-17，用户确认“V6 得重新开发”后，Codex 再次把该确认理解为可直接写代码，已创建 `v6-agent-harness-kernel` OpenSpec、harness 边界、测试和部分运行时代码。这再次越过了“先给 plan 审查，再实现”的确认门。
- 二次偏差处理：用户已在 review plan 后确认“没问题就进行开发，按计划来”，当前 `v6-agent-harness-kernel` 草稿改为保留并按计划改造。后续硬规则仍保留：凡是阶段重做/重新开发请求，Codex 只能先产出阶段 plan、OpenSpec/harness 边界和审查摘要；除非用户明确说“开始实现/写代码/按这个计划开发”，不得修改运行时代码或测试。

## 路线重定向：加速但保持轻量工程化

用户希望 RepoPilot 后续不只是玩具项目，而是更偏工程化的 Agent Harness；同时由于主要由个人使用 AI 开发，不能走重型企业平台路线。后续工程化应优先体现在边界、审计、验证、可替换接口和交接文档，而不是堆中间件或堆代码量。

原则：

- 工程化但轻量：先用内存、JSON、SQLite 或简单文件存储打通接口，只有在阶段需要时才引入 PostgreSQL、Milvus、Elasticsearch、Kafka 等外部依赖。
- 纵向切片优先：每个阶段都交付一条可运行闭环，而不是只堆抽象层。
- Harness 边界优先：Provider、Router、AgentLoop、ToolRegistry、ToolExecutor、Memory、RAG、Skill、Trace 分层明确。
- 可审计优先：model/tool/skill/memory 调用都要有结构化摘要和脱敏策略。
- 可验证优先：每个阶段都要有最小测试和默认验证命令。
- 可进化 Skill：skill 不是一次性 prompt 文件，后续应逐步支持 metadata、content、selection、tool limits、version、review 和演进记录。

建议后续路线：

- V6：Agent Harness Kernel + Router Kernel。已建立 `RequestRouter`、`ToolRegistry`、`AgentLoop` 和 `TraceEvent` 四个最小运行时骨架；`ProviderAdapter`、`ContextBuilder`、`SkillRegistry` 和 `SessionStore` 留到后续阶段，不在 V6 写运行时代码。历史 `v6-skill-aware-agent-loop` draft 只作为流程偏差记录和 skill 子能力参考。
- V7：Permission + Approval Gate。引入工具风险等级、allow/deny/ask 策略和高风险动作确认。
- V8：Repo RAG Engineering。吸收 ragent 和 Agentic RAG for Dummies 的工程化链路，先做 repo-local 文档解析、chunk、hybrid search、query rewrite、rerank 和 citation。
- V9：Three-layer Memory。吸收 mem0 和 AGI-assistant 思路，区分 STM、LTM 和 PREF，并记录 memory audit。
- V10：ReAct / Long Task Agent。加入计划、任务状态、pause/resume、compact、scratch space 和长 trace。
- V11：Subagents + Worktree。加入 explorer/worker/reviewer、隔离工作区、结果 handoff 和冲突检测。
- V12：Personal Assistant Gateway。探索 always-on、heartbeat/cron、connector、通知和人工审批。

## 已完成

### V1：Agent 服务入口和可追踪请求结构

- FastAPI 应用可启动。
- `POST /chat` 接收 `user_id`、`session_id`、`message`、`repo_path`。
- 每次请求生成唯一 `trace_id`。
- 返回 `answer`、`related_files`、`tool_calls`。
- V1 建立 Agent 服务入口和可追踪响应结构，`related_files`、`tool_calls` 作为后续审计字段保留。
- pytest 覆盖 `/chat` 基础行为和 `trace_id` 不重复。

### V2：安全只读仓库工具层

- `list_files(repo_path)`：列出仓库内允许访问的文本文件。
- `read_file(repo_path, file_path, max_chars=12000)`：读取仓库内文本文件并限制长度。
- `search_code(repo_path, keyword, max_results=20)`：搜索关键词并限制结果数。
- 文件工具限制访问在 `repo_path` 内。
- 提供路径逃逸防护，跳过敏感文件、隐藏目录、忽略目录和二进制文件。
- V2 工具只读，不写文件、不删文件、不执行 shell。
- 新增 `tests/test_file_tools.py`。

### Harness V0

- 新增 `AGENTS.md` 作为 Agent 入口地图。
- 新增 `docs/ARCHITECTURE.md` 记录架构边界。
- 新增 `docs/AGENT_RULES.md` 记录 Agent 工作规则。
- 新增 `docs/FEATURE_LIST.json` 记录可验收功能清单。
- 新增 `HANDOFF_TO_NEXT_CHAT.md` 作为跨 session 交接文档。
- 新增 `scripts/verify.ps1` 作为本地验证入口。

### V3：统一工具执行边界和最小 Agent Loop

- V3 legacy specs 已迁移到 `openspec/specs/agent-loop-tool-execution/spec.md`。
- 新增轻量 `ToolExecutor`，当前只包装 `search_code`。
- `CodeAgent` 使用最小确定性规则提取关键词，并通过 `ToolExecutor` 调用只读搜索。
- `/chat` 返回真实 `related_files` 和 `tool_calls` 摘要。
- V3 的意义是把工具调用统一收口，给后续权限、审批、沙箱、trace audit、eval 和 reflection 留扩展点，不是让 Agent 变成通用 AI 编程助手。
- 新增 `UNIQUE_BUG_TOKEN` 命中、无命中、敏感文件不泄露和错误摘要脱敏测试。

## 最近验证

- 2026-05-12：`powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`：通过
- `pytest`：24 passed
- `ruff check .`：All checks passed
- 2026-05-12：`openspec validate retire-legacy-specs`：通过
- 2026-05-12：`openspec validate --all`：5 passed
- 2026-05-12：`git diff --check`：通过，仅有 CRLF 换行提示
- 2026-05-12，V5 实现验证：`powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`：通过
- 2026-05-12，V5 实现验证：`pytest`：30 passed, 1 skipped
- 2026-05-12，V5 实现验证：`ruff check .`：All checks passed
- 2026-05-12，V5 归档验证：`openspec validate --all`：通过
- 2026-05-17，V6 规格验证：`openspec validate v6-skill-aware-agent-loop`：通过
- 2026-05-17，V6 实现验证：`pytest tests/test_chat_api.py`：8 passed
- 2026-05-17，V6 全量验证：`powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`：通过
- 2026-05-17，V6 全量验证：`pytest`：32 passed, 1 skipped
- 2026-05-17，V6 全量验证：`ruff check .`：All checks passed
- 2026-05-17，V6 diff 验证：`git diff --check`：通过，仅有 CRLF 换行提示
- 2026-05-18，V6 Kernel plan 验证：`openspec validate v6-agent-harness-kernel`：通过
- 2026-05-18，V6 Kernel 小切片验证：`pytest tests/test_agent_harness_kernel.py`：9 passed
- 2026-05-18，V6 `/chat` 回归验证：`pytest tests/test_chat_api.py`：6 passed
- 2026-05-18，V6 局部 lint：`ruff check app/harness app/agents/code_agent.py tests/test_agent_harness_kernel.py`：All checks passed
- 2026-05-18，V6 全量验证：`powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`：通过；`pytest` 39 passed, 1 skipped；`ruff check .` All checks passed
- 2026-05-18，V6 diff 验证：`git diff --check`：通过，仅有 CRLF 换行提示
- 2026-05-18，V6 最终全量验证：`powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`：通过；`pytest` 42 passed, 1 skipped；`ruff check .` All checks passed
- 2026-05-18，V6 归档验证：`openspec validate --all`：5 passed

## OpenSpec 项目级工作流

- 新增项目内 OpenSpec 目录说明：
  - `openspec/README.md`
  - `openspec/changes/README.md`
  - `openspec/changes/archive/README.md`
  - `openspec/specs/README.md`
- 保留项目内 `.codex/skills`，用于 Codex 在本仓库理解 OpenSpec 工作流。
- 保留项目内 `.opencode`，用于 OpenCode OpenSpec commands 和 skills。
- 不保留 `.github` OpenSpec prompts/skills；Copilot 对接不通过仓库内 `.github` 生成物维护。
- 不安装 Codex 全局 prompts，不要求写入 `C:\Users\...\ .codex\prompts`。
- OpenSpec 只作为本仓库开发流程，不是 RepoPilot runtime 功能。
- 不因为 OpenSpec 接入而引入 MCP server、plugin runtime、skill 执行、动态工具注册或 `/chat` 决策变更。

## Legacy Specs OpenSpec 迁移与归档

- 新增 OpenSpec change：`migrate-legacy-specs-to-openspec`。
- 迁移规划目标是把 legacy `specs/00x-*` 的已验收 V1-V4 行为映射为长期 OpenSpec capabilities。
- 已归档 `migrate-legacy-specs-to-openspec`，并生成长期 `openspec/specs/`。
- 旧 `specs/00x-*` 已退役并删除；历史迁移记录保留在 `openspec/changes/archive/2026-05-11-migrate-legacy-specs-to-openspec/`。
- 已归档 `retire-legacy-specs` 到 `openspec/changes/archive/2026-05-12-retire-legacy-specs/`，并在 `harness-development-workflow` 记录 `openspec/specs/` 是长期规格入口。
- `openspec/specs/<capability>/` 作为长期规格入口仅保留当前 capability 的 `spec.md`；活跃 change 的 `proposal.md`、`design.md`、`tasks.md` 和 spec delta 保留在 `openspec/changes/<change-name>/`，归档后再进入 `openspec/changes/archive/`。
- OpenSpec 正文优先使用中文；capability 目录名、命令、函数名和字段名保持英文工程约定；规范句保留 `SHALL` / `MUST` / `MUST NOT` 关键词以通过 OpenSpec 校验。
- 新增 capabilities：
  - `chat-api`
  - `safe-repository-file-tools`
  - `agent-loop-tool-execution`
  - `skill-metadata-loader`
  - `harness-development-workflow`
- `openspec validate migrate-legacy-specs-to-openspec`：通过。
- `openspec list`：No active changes found。
- `openspec list --specs`：显示 5 个 capabilities。

## V4：Skill Metadata Loader

- V4 legacy specs 已迁移到 `openspec/specs/skill-metadata-loader/spec.md`。
- 新增 `app/tools/skill_loader.py`，发现 `.agents/skills/*/SKILL.md`，解析 `name`、`description` 和相对仓库 `path`。
- 新增 `tests/test_skill_loader.py`，覆盖 metadata 命中、无 skills 目录、多技能稳定排序、不返回完整正文、不泄露本机绝对路径、缺失 metadata、非法 frontmatter 行和异常 frontmatter 读取限制。
- V4 不执行 skill，不读取完整 skill 正文，不做 progressive disclosure，不接入 `/chat` 决策。
- V4 当前对坏 `SKILL.md` 采用 fail fast 策略；后续有日志、trace audit 或 skill audit 后，可调整为记录日志并跳过坏 skill。
- V4 仍不接真实 LLM、不自动修改代码、不执行 shell、不做 RAG、Memory、Reflection、eval 或复杂多 Agent。

## V5：Skill Content Loader / progressive disclosure

- 当前分支：`feature/v5-skill-content-loader`。
- 已创建 OpenSpec change：`openspec/changes/v5-skill-content-loader/`。
- 已完成 OpenSpec artifacts：`proposal.md`、`design.md`、`specs/skill-metadata-loader/spec.md`、`tasks.md`。
- 已实现 `load_skill_content(repo_path, skill_path)`，在 metadata-first 之后按需读取完整 `SKILL.md`。
- Content Loader 返回 `{"path": "...", "content": "..."}`。
- Content Loader 只允许读取 `.agents/skills/<skill>/SKILL.md`，拒绝路径逃逸、非 skill 文件、缺失文件和符号链接目录绕过。
- Content Loader 有明确内容读取上限，超限 fail fast。
- Content Loader 不解析 frontmatter，不验证 `name` / `description`。
- V5 仍不接入 `/chat` 决策，不执行 skill，不接真实 LLM，不自动把 skill 内容注入 prompt。
- 已同步本阶段 `.harness/allowed_files.md` 和 `.harness/review_checklist.md`。
- `docs/FEATURE_LIST.json` 中 V5 条目已标记 `passes: true`。
- 已归档 `v5-skill-content-loader` 到 `openspec/changes/archive/2026-05-12-v5-skill-content-loader/`，并同步长期规格 `openspec/specs/skill-metadata-loader/spec.md`。

## V6：Agent Harness Kernel + Router Kernel（已提交并归档）

- 当前分支：`feature/v6-agent-harness-kernel`。
- 已提交：`b1d6b03 Add V6 agent harness kernel`。
- 已归档 OpenSpec change：`openspec/changes/archive/2026-05-18-v6-agent-harness-kernel/`。
- 用户已接受当前 V6 阶段实现；当前暂无活跃 OpenSpec change。
- 当前 V6 主线已从 `v6-skill-aware-agent-loop` 切换为 Agent Harness Kernel + Router Kernel。
- `v6-skill-aware-agent-loop` 是历史 draft/流程偏差记录，不作为当前阶段主线，不应继续作为实现入口；其空 active change 目录已清理。
- 当前小切片已建立四个最小运行时骨架：
  - `RequestRouter`：对输入请求做确定性路由，先只支持现有仓库搜索路径。
  - `ToolRegistry`：登记只读低风险工具元数据，并在调用前校验工具存在、只读和风险等级；不负责 dispatch。
  - `AgentLoop`：包装现有确定性搜索闭环，不引入真实 LLM 或复杂规划。
  - `TraceEvent`：记录最小结构化事件，支撑后续审计。
- 已固化最小 contract：`AgentLoopRequest`、`RouteDecision`、`ToolSpec`、`TraceEvent`、内部 `AgentLoopResult`。
- V6 不实现 `ProviderAdapter`、`ContextBuilder`、`SkillRegistry`、`SessionStore` 运行时代码；这些只作为后续阶段扩展方向。
- V6 不接 RAG、Memory、Reflection、eval、PermissionPolicy、ApprovalGate、SandboxRunner、subagents、长期任务或真实 LLM。

## 当前注意事项

- V2 工具只读，不写文件、不删文件、不执行 shell。
- V3 只做最小确定性关键词提取，测试使用 `UNIQUE_BUG_TOKEN`。
- 当前链路只调用只读 `search_code`，不自动读取普通代码文件完整内容；V6 Kernel 继续保留 `ToolExecutor` 作为实际工具调用边界。
- 当前不接真实 LLM、不自动修改代码、不执行 shell、不做 Reflection、eval、RAG、Memory 或复杂多 Agent。
- PermissionPolicy、ApprovalGate、SandboxRunner、trace audit、Skill 执行、eval 和 Reflection 仍是 Roadmap，不能写成已实现。
- 后续接入权限、审批、沙箱时，应通过 `ToolExecutor` 增量加入。
- 缓存文件已从 git 跟踪中移除，并由 `.gitignore` 忽略。

## 下一步建议

下一步建议：

- 长期规格入口已切换为 `openspec/specs/`。
- 后续新阶段继续使用 OpenSpec change；不要恢复旧 `specs/00x-*` 作为规格入口。
- 当前建议：下一步先规划 V7 Permission + Approval Gate；规划前同步 `.harness/allowed_files.md` 和 `.harness/review_checklist.md`。
- 后续可做 trace/tool/skill audit，为“坏 skill 记录日志并跳过”和更完整的审计记录提供基础。
- 继续保持不执行 skill，除非后续阶段明确开放。
