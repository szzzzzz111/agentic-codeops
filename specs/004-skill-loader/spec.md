# 规格：V4 Skill Metadata Loader

## 目标

V4 引入 DeepAgents 风格的 Skill Metadata Loader，用于发现仓库内声明式技能目录，并读取每个 `SKILL.md` 的最小元数据。V4 的核心目标不是让 Agent 执行技能，而是建立可验证、可审计、可渐进扩展的技能发现边界。

V4 只处理 metadata-first 阶段：发现 `.agents/skills/*/SKILL.md`，解析 `name`、`description` 和 `path`，为后续 progressive disclosure、skill content loader 和 skill-aware agent loop 留出接口。

## 技能目录约定

V4 只发现以下目录结构：

```text
.agents/
  skills/
    example-skill/
      SKILL.md
```

每个技能目录最多对应一个 `SKILL.md`。发现结果中的 `path` 必须是相对仓库根目录的路径，例如：

```text
.agents/skills/example-skill/SKILL.md
```

## Metadata 约定

`SKILL.md` 使用 YAML frontmatter 描述最小元数据：

```markdown
---
name: example-skill
description: 用一句话说明技能适用场景。
---

# Example Skill

这里是技能正文。V4 不读取或使用正文。
```

V4 只解析 frontmatter 中的：

- `name`
- `description`

V4 生成的技能 metadata 至少包含：

```json
{
  "name": "example-skill",
  "description": "用一句话说明技能适用场景。",
  "path": ".agents/skills/example-skill/SKILL.md"
}
```

## Loader 行为

- 只在给定 `repo_path` 内查找 `.agents/skills/*/SKILL.md`。
- 只返回技能 metadata，不返回完整 `SKILL.md` 正文。
- `path` 使用相对仓库路径，不返回本机绝对路径。
- 缺少 `.agents/skills` 目录时返回空列表。
- 单个技能 metadata 缺失、frontmatter 未闭合或格式不合法时，V4 当前直接抛出结构化异常，避免静默忽略坏配置。
- 后续引入日志、trace audit 或 skill audit 后，可以把坏 skill 调整为“记录日志并跳过”，但这不属于 V4。
- 返回顺序应稳定，优先按相对路径排序。

## 安全要求

- 不执行 skill。
- 不读取完整 skill 正文。
- 不把 skill 正文注入 prompt。
- 不接入 `/chat` 决策。
- 不接真实 LLM。
- 不自动修改代码。
- 不执行 shell 命令。
- 不加入 RAG、Memory、Reflection、eval 或复杂多 Agent。
- 不实现 PermissionPolicy、ApprovalGate 或 SandboxRunner。
- 继续限制所有文件访问在 `repo_path` 内，不泄露本机绝对路径。

## 验收标准

- 给定包含 `.agents/skills/*/SKILL.md` 的临时仓库，Loader 能返回技能 `name`、`description` 和相对 `path`。
- 多个技能返回稳定排序。
- 没有 `.agents/skills` 目录时返回空列表。
- `path` 不包含本机绝对路径。
- V4 不读取或返回完整 skill 正文。
- 异常 frontmatter 受读取行数和字符数限制，不会无限读完整正文。
- V4 不改变 `/chat` 请求和响应行为。
- 既有 V1/V2/V3 测试继续通过。
- `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` 通过；如果当前环境无法运行某项检查，应明确说明原因。

## 非目标

- Skill 执行。
- Skill 正文加载。
- Progressive disclosure。
- 根据用户消息选择 skill。
- 将 skill 接入 `CodeAgent` 或 `/chat`。
- 真实 LLM 接入。
- 自动修改代码、补丁生成或自动修复。
- shell 工具或测试运行工具。
- 权限系统、人工审批流或沙箱执行。
- trace 持久化审计。
- RAG、Memory、Reflection 或 eval。
