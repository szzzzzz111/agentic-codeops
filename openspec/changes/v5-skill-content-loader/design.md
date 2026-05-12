## Context

RepoPilot 当前 V4 已实现 `load_skill_metadata(repo_path)`，它只发现 `.agents/skills/*/SKILL.md` 并读取 YAML frontmatter 中的 `name`、`description` 和相对路径 `path`。这满足 metadata-first，但还没有 progressive disclosure 的第二步：当调用方已经通过 metadata 选定一个 skill 后，按需读取该 skill 的完整 `SKILL.md`。

V5 仍是工具层能力，不改变 `/chat` 决策链路。它的边界是“读取内容”，不是“选择 skill、执行 skill、接 LLM 或注入 prompt”。

## Goals / Non-Goals

**Goals:**

- 在 `app/tools/skill_loader.py` 中提供 `load_skill_content(repo_path, skill_path)`，按相对仓库路径读取完整 `SKILL.md`。
- 复用 V4 的仓库根目录解析、路径归一化和 repo 内访问限制。
- 确保只能读取 `.agents/skills/<skill>/SKILL.md`，并拒绝路径逃逸、非 skill 路径、缺失文件和不安全路径。
- 保持 `load_skill_metadata(repo_path)` 的输出边界不变，不返回完整正文。
- 增加 focused tests 覆盖正常读取和安全拒绝场景。

**Non-Goals:**

- 不把 skill content 接入 `/chat`、`CodeAgent` 或 `ToolExecutor` 决策。
- 不执行 skill，不调用真实 LLM，不自动把 skill 内容塞进 prompt。
- 不实现 skill 选择、skill audit、日志降级跳过坏 skill、RAG、Memory、Reflection、eval、PermissionPolicy、ApprovalGate 或 SandboxRunner。
- 不改变 `load_skill_metadata(repo_path)` 的 metadata fail-fast 策略；该策略只适用于 metadata discovery。
- Content loader 只做完整文件读取，不解析 frontmatter，不验证 `name` / `description`，不引入新的 skill 格式规则。

## Decisions

- 新增独立函数读取内容，而不是扩展 `load_skill_metadata` 返回字段。
  - 原因：metadata 列表需要继续保持轻量、安全、可审计，避免一次 discovery 泄露完整正文。
  - 替代方案：给 metadata 增加 `content` 字段；拒绝，因为这会破坏 V4 边界。
- 以 metadata 返回的相对 `path` 作为 content loader 输入。
  - 原因：调用方可以先 discovery，再按选定 `path` progressive disclosure，符合分层读取模型。
  - 替代方案：按 `name` 读取；拒绝，因为 `name` 来自 frontmatter，不天然等同于目录身份，且可能重复。
- Content loader 只接受 `.agents/skills/<skill>/SKILL.md` 形态。
  - 原因：避免读取 `.agents/skills` 外的任意文件，也避免将该函数变成通用文件读取入口。
  - 替代方案：复用 `read_file` 读取任意相对路径；拒绝，因为 skill loader 应保持专用边界。
- 输出完整文本内容和相对路径，不输出本机绝对路径。
  - 原因：调用方需要正文进行后续 prompt 构造或展示，但审计输出仍不应泄露本机路径。
- Content loader 返回结构为 `{"path": "<relative path>", "content": "<full SKILL.md text>"}`。
  - 原因：显式返回相对路径便于调用方和测试确认读取对象，同时避免暴露本机绝对路径。
  - 替代方案：只返回字符串；拒绝，因为调用方需要稳定地关联内容与 metadata path。

## Risks / Trade-offs

- [Risk] 新函数可能被误用为 `/chat` 自动注入 skill 的入口 → Mitigation: OpenSpec、tests 和 harness 明确 V5 不接入 `/chat`，实现阶段只改 tool 和 tests。
- [Risk] 路径校验不足会扩大读取范围 → Mitigation: 测试覆盖 `..` 路径逃逸、非 `.agents/skills` 路径、非 `SKILL.md` 文件和符号链接目录。
- [Risk] 完整正文可能很大 → Mitigation: V5 可沿用明确的最大读取字符限制；超限 fail fast，避免无界读取。
- [Risk] 过早引入复杂解析器或动态 skill runtime → Mitigation: 本阶段只做 UTF-8 文本读取和路径约束，不新增依赖。
