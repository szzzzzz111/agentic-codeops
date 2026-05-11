# skill-metadata-loader Specification

## Purpose
TBD - created by archiving change migrate-legacy-specs-to-openspec. Update Purpose after archive.
## Requirements
### Requirement: 发现技能元数据文件

系统 SHALL 提供 `load_skill_metadata(repo_path)`，用于发现仓库内 `.agents/skills/*/SKILL.md` 文件。

#### Scenario: 存在技能文件

- **WHEN** 仓库包含 `.agents/skills/example/SKILL.md`
- **THEN** Loader 将其视为技能元数据来源

#### Scenario: skills 目录不存在

- **WHEN** `.agents/skills` 不存在
- **THEN** Loader 返回空列表

### Requirement: 解析最小 frontmatter 元数据

Loader SHALL 只解析 YAML frontmatter 字段 `name` 和 `description`，并返回这些字段以及相对仓库路径 `path`。

#### Scenario: 有效元数据

- **WHEN** `SKILL.md` 包含有效的 `name` 和 `description` frontmatter
- **THEN** Loader 返回 `name`、`description` 和相对路径 `path`

#### Scenario: 稳定排序

- **WHEN** 存在多个技能
- **THEN** Loader 按路径稳定排序返回

### Requirement: 技能元数据输出有边界且安全

Loader MUST NOT 执行 skill、加载完整 skill 正文、返回完整 skill 正文、把 skill 内容注入 prompt 或返回本机绝对路径。

#### Scenario: 存在技能正文

- **WHEN** `SKILL.md` 在 frontmatter 后包含正文内容
- **THEN** 返回的 metadata 不包含正文内容

#### Scenario: 路径输出

- **WHEN** metadata 被返回
- **THEN** `path` 是相对 `repo_path` 的路径

### Requirement: 非法技能元数据 fail fast

Loader SHALL 在缺少必要 metadata、frontmatter 行格式非法、frontmatter 未闭合或 frontmatter 超出读取限制时 fail fast。

#### Scenario: 缺少 description

- **WHEN** `SKILL.md` 缺少 `description`
- **THEN** Loader 抛出错误

#### Scenario: 非法 frontmatter 行

- **WHEN** frontmatter 包含非空、非注释且不含 `:` 的行
- **THEN** Loader 抛出错误

#### Scenario: 未闭合 frontmatter 受限

- **WHEN** frontmatter 在读取限制前没有闭合
- **THEN** Loader 抛出错误且不会无界读取内容

### Requirement: 技能元数据加载器不是聊天决策逻辑

当前 Skill Metadata Loader MUST NOT 接入 `/chat`、`CodeAgent`、`ToolExecutor`、真实 LLM 选择、progressive disclosure 或 skill 执行。

#### Scenario: 聊天请求

- **WHEN** `/chat` 处理用户请求
- **THEN** 它不使用技能元数据进行决策

