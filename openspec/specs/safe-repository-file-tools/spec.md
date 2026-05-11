# safe-repository-file-tools Specification

## Purpose
TBD - created by archiving change migrate-legacy-specs-to-openspec. Update Purpose after archive.
## Requirements
### Requirement: 列出安全仓库文件

系统 SHALL 提供只读 `list_files(repo_path)` 工具，返回 `repo_path` 内允许访问的类文本文件，路径 MUST 相对 `repo_path`。

#### Scenario: 普通文件被列出

- **WHEN** 仓库包含普通源码文件
- **THEN** `list_files` 返回这些文件的相对路径

#### Scenario: 不安全文件被跳过

- **WHEN** 仓库包含忽略目录、隐藏目录、敏感文件或二进制文件
- **THEN** `list_files` 不返回这些条目

### Requirement: 读取安全仓库文件

系统 SHALL 提供只读 `read_file(repo_path, file_path, max_chars)` 工具，只读取 `repo_path` 内文本文件，并限制返回内容长度。

#### Scenario: 仓库内文件被读取

- **WHEN** `read_file` 目标是 `repo_path` 内允许访问的文件
- **THEN** 它返回最多 `max_chars` 个字符的 UTF-8 文本内容

#### Scenario: 路径逃逸被拒绝

- **WHEN** `read_file` 目标路径位于 `repo_path` 之外
- **THEN** 工具拒绝该请求

#### Scenario: 敏感文件被拒绝

- **WHEN** `read_file` 目标是 `.env` 或密钥材料等敏感文件
- **THEN** 工具拒绝该请求

### Requirement: 搜索安全仓库文件

系统 SHALL 提供只读 `search_code(repo_path, keyword, max_results)` 工具，搜索允许访问的文本文件，并返回文件路径、行号和行文本。

#### Scenario: 关键词命中返回位置

- **WHEN** 允许访问的文件包含搜索关键词
- **THEN** `search_code` 返回包含 `file_path`、`line_number` 和 `line_text` 的结果

#### Scenario: 关键词未命中返回空结果

- **WHEN** 没有允许访问的文件包含关键词
- **THEN** `search_code` 返回空列表

#### Scenario: 敏感内容不返回

- **WHEN** 敏感文件包含关键词
- **THEN** `search_code` 不返回该敏感文件内容

### Requirement: 文件工具保持只读

仓库文件工具 MUST NOT 写文件、删文件或执行 shell 命令。

#### Scenario: 工具能力边界

- **WHEN** 文件工具被调用
- **THEN** 它们只列出、读取或搜索允许访问的仓库文本文件

