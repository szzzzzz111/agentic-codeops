# 项目进度

RepoPilot 当前定位为面向代码仓库分析任务的可控 Code Agent Harness。它不试图替代通用 AI IDE，而是围绕 Agent 工具调用边界、只读安全工具、执行追踪、可验证测试、review checklist 和 handoff 机制，构建可审计、可扩展的代码智能体执行框架。

## 当前状态

- 当前工作分支：`feature/v5-skill-content-loader`；基线分支 `main` 已同步到 `dev`
- 当前阶段：V5 Skill Content Loader / progressive disclosure 已完成并通过验证，等待提交后归档
- 当前主流程：`/chat` 已通过 `CodeAgent -> ToolExecutor -> search_code` 使用只读仓库搜索
- 当前工具层：`list_files`、`read_file`、`search_code` 已实现
- 当前 V4 状态：已实现独立 Skill Metadata Loader，尚未接入 `/chat` 决策或 skill 执行
- 当前 OpenSpec 状态：已初始化项目内 OpenSpec、OpenCode 和 `.codex/skills`；不安装 Codex 全局 prompts；不保留 `.github` OpenSpec 生成物

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
- 2026-05-12，V5 当前未提交工作区实现验证：`powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`：通过
- 2026-05-12，V5 当前未提交工作区实现验证：`pytest`：30 passed, 1 skipped
- 2026-05-12，V5 当前未提交工作区实现验证：`ruff check .`：All checks passed
- 2026-05-12，V5 当前未提交工作区实现验证：`openspec validate v5-skill-content-loader`：通过
- 若提交前继续修改实现、测试或文档，必须重新运行上述验证。

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

## 当前注意事项

- V2 工具只读，不写文件、不删文件、不执行 shell。
- V3 只做最小确定性关键词提取，测试使用 `UNIQUE_BUG_TOKEN`。
- V3 当前只调用 `search_code`，不自动读取完整文件内容。
- 当前不接真实 LLM、不自动修改代码、不执行 shell、不做 Reflection、eval、RAG、Memory 或复杂多 Agent。
- PermissionPolicy、ApprovalGate、SandboxRunner、trace audit、Skill 执行、eval 和 Reflection 仍是 Roadmap，不能写成已实现。
- 后续接入权限、审批、沙箱时，应通过 `ToolExecutor` 增量加入。
- 缓存文件已从 git 跟踪中移除，并由 `.gitignore` 忽略。

## 下一步建议

下一步建议：

- 长期规格入口已切换为 `openspec/specs/`。
- 后续新阶段继续使用 OpenSpec change；不要恢复旧 `specs/00x-*` 作为规格入口。
- 当前建议：提交 V5 变更后归档 OpenSpec change。
- 也可以先做 trace/tool/skill audit，为后续“坏 skill 记录日志并跳过”提供基础。
- 继续保持不执行 skill、不接入 `/chat` 决策，除非后续阶段明确开放。
