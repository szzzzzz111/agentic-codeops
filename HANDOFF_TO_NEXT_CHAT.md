# 交接给下一轮 Chat

## 分支状态

```text
当前工作分支：feature/v5-skill-content-loader
当前基线分支：main
已同步分支：dev、feature/retire-legacy-specs
V4 已同步合并到：feature/v4-skill-loader、dev、main
```

## 当前项目状态

RepoPilot 当前定位为面向代码仓库分析任务的可控 Code Agent Harness，不是替代通用 AI IDE 的编程助手。V1、V2、V3、V4 已合并到 `main`；项目级 OpenSpec 工作流已接入；legacy `specs/00x-*` 已退役，长期规格入口已切换到 `openspec/specs/`。

V3 已完成统一工具执行边界：`/chat` 通过 `CodeAgent -> ToolExecutor -> search_code` 使用只读仓库搜索，并返回真实 `related_files` 和 `tool_calls`。当前 Trace 是 `ChatService` 创建的请求级 `trace_id`，还不是完整持久化审计系统。

V4 已实现独立 Skill Metadata Loader，但未接入 `/chat` 决策，也不执行 skill。当前能力只发现 `.agents/skills/*/SKILL.md`，解析 `name`、`description` 和相对仓库 `path`，不读取或返回完整正文。

当前 V5 已完成并通过当前未提交工作区验证：Skill Content Loader / progressive disclosure，即调用方已经选定某个 skill 后，按相对路径按需读取完整 `SKILL.md`。V5 仍不做 skill-aware agent loop，不接入 `/chat` 决策，不执行 skill，不接真实 LLM，不自动把 skill 内容注入 prompt。

## 本轮完成

- 从 `main` 创建工作分支：`feature/v5-skill-content-loader`。
- 创建 OpenSpec change：`openspec/changes/v5-skill-content-loader/`。
- 完成 V5 OpenSpec artifacts：
  - `proposal.md`
  - `design.md`
  - `specs/skill-metadata-loader/spec.md`
  - `tasks.md`
- 同步 V5 阶段 harness：
  - `.harness/allowed_files.md`
  - `.harness/review_checklist.md`
- 更新长期进度和验收清单：
  - `README.md`
  - `docs/PROGRESS.md`
  - `docs/FEATURE_LIST.json`
- 同步 README 路线图：V5 改为 Skill Content Loader / progressive disclosure，trace audit、eval、reflection、RAG 后移。
- 实现 `load_skill_content(repo_path, skill_path)`：
  - 返回 `{"path": "...", "content": "..."}`
  - 只允许读取 `.agents/skills/<skill>/SKILL.md`
  - 拒绝路径逃逸、非 skill 文件、缺失文件和符号链接目录绕过
  - 设置内容读取上限
  - 不解析 frontmatter
- `docs/FEATURE_LIST.json` 已将 `v5-skill-content-loader` 标记为 `passes: true`。

## 本轮验证

- `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`：通过。
  - `pytest`：30 passed, 1 skipped
  - `ruff check .`：All checks passed
- `openspec validate v5-skill-content-loader`：通过。
- `git diff --check`：通过，仅有 CRLF 换行提示。
- 上述验证对应 2026-05-12 的当前未提交工作区；如果提交前继续修改实现、测试或文档，需要重新运行验证。

## V5 规划边界

已实现：

- 在 `app/tools/skill_loader.py` 增加按相对路径读取完整 `SKILL.md` 的 content loader。
- 在 `tests/test_skill_loader.py` 增加读取成功、返回结构、路径安全、读取上限和 metadata 行为不变的测试。

禁止实现：

- 不接入 `/chat`、`CodeAgent` 或 `ToolExecutor` 决策。
- 不执行 skill。
- Content Loader 不解析 frontmatter，不验证 `name` / `description`；metadata fail-fast 只属于 `load_skill_metadata(repo_path)`。
- 不接真实 LLM。
- 不自动把 skill 内容注入 prompt。
- 不恢复旧 `specs/00x-*`。
- 不引入 RAG、Memory、Reflection、eval、PermissionPolicy、ApprovalGate 或 SandboxRunner。

## 下一轮建议

1. 提交 V5 变更。
2. 提交后归档 `v5-skill-content-loader`。
3. 归档前后按需运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify.ps1
openspec validate v5-skill-content-loader
git diff --check
```

4. 下一阶段建议继续 V6：Skill-aware Agent Loop，基于 skill metadata 选择相关 skill，但仍不执行 skill。

## 不要做

- 不接真实 LLM。
- 不自动修改代码。
- 不执行 shell 工具。
- 不加入复杂多 Agent。
- 不提前做 RAG、Memory、Reflection 或 eval。
- 不提前实现 PermissionPolicy、ApprovalGate 或 SandboxRunner。
- V5 不做 skill-aware `/chat` 决策，不执行 skill。
