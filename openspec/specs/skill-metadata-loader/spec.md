# skill-metadata-loader Specification

## Purpose

记录已实现的 Skill Metadata Loader 边界：仅发现 `.agents/skills/*/SKILL.md`，仅解析 frontmatter 中的 `name`、`description` 和相对仓库 `path`，不接入 `/chat`，不读取或返回完整正文，不执行 skill。
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

Loader MUST NOT 执行 skill、在 metadata discovery 阶段加载完整 skill 正文、通过 `load_skill_metadata(repo_path)` 返回完整 skill 正文、把 skill 内容注入 prompt 或返回本机绝对路径。完整 skill 正文只能通过明确的按需 content loading 入口读取。

#### Scenario: 存在技能正文

- **WHEN** `SKILL.md` 在 frontmatter 后包含正文内容
- **THEN** `load_skill_metadata(repo_path)` 返回的 metadata 不包含正文内容

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

当前 Skill Metadata Loader 和 Content Loader MUST NOT 接入 `/chat`、`CodeAgent`、`ToolExecutor`、真实 LLM 选择或 skill 执行。Progressive disclosure 仅表示调用方显式按需读取已选定 skill 的完整内容，不表示自动选择或执行 skill。

#### Scenario: 聊天请求

- **WHEN** `/chat` 处理用户请求
- **THEN** 它不使用技能元数据或技能内容进行决策

### Requirement: 按需读取技能完整内容

系统 SHALL 提供 `load_skill_content(repo_path, skill_path)`，按相对仓库路径读取完整 `SKILL.md` 内容，用于 metadata-first 之后的 progressive disclosure。Content Loader SHALL 返回结构 `{"path": "<relative path>", "content": "<full SKILL.md text>"}`。

#### Scenario: 读取已发现技能内容

- **WHEN** 调用方传入仓库路径和 `.agents/skills/review/SKILL.md`
- **THEN** Loader 返回 `path` 为 `.agents/skills/review/SKILL.md` 且 `content` 为该 `SKILL.md` 完整 UTF-8 文本内容的结果

#### Scenario: 返回内容保留 frontmatter 和正文

- **WHEN** `SKILL.md` 同时包含 YAML frontmatter 和正文
- **THEN** Loader 返回的 `content` 包含 frontmatter 和正文

#### Scenario: 输出不泄露本机绝对路径

- **WHEN** Loader 返回完整技能内容结果
- **THEN** 结果中的路径字段仍为相对 `repo_path` 的路径

#### Scenario: 不解析 frontmatter

- **WHEN** Content Loader 读取包含 YAML frontmatter 的 `SKILL.md`
- **THEN** Loader 不解析或验证 frontmatter 字段，只返回完整文本内容

### Requirement: 技能内容读取限制在技能目录

Content Loader MUST 只允许读取当前仓库内 `.agents/skills/<skill>/SKILL.md` 文件，并拒绝其它路径。

#### Scenario: 拒绝路径逃逸

- **WHEN** 调用方传入包含 `..` 并指向仓库外的路径
- **THEN** Loader 拒绝读取

#### Scenario: 拒绝非技能文件

- **WHEN** 调用方传入 `README.md` 或 `.agents/skills/review/notes.md`
- **THEN** Loader 拒绝读取

#### Scenario: 拒绝缺失技能文件

- **WHEN** 调用方传入不存在的 `.agents/skills/missing/SKILL.md`
- **THEN** Loader 抛出明确错误

#### Scenario: 拒绝符号链接目录绕过

- **WHEN** `.agents/skills/<skill>` 是符号链接目录或解析后不在仓库内
- **THEN** Loader 拒绝读取

### Requirement: 技能内容读取有规模上限

Content Loader SHALL 对完整 `SKILL.md` 内容读取设置明确字符上限，避免无界读取。

#### Scenario: 技能内容在限制内

- **WHEN** `SKILL.md` 内容长度未超过读取限制
- **THEN** Loader 在 `content` 字段返回完整内容

#### Scenario: 技能内容超出限制

- **WHEN** `SKILL.md` 内容长度超过读取限制
- **THEN** Loader 抛出明确错误且不返回部分内容

