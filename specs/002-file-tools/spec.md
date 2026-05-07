# 规格：V2 安全仓库文件工具

## 目标

增加一个小而安全的文件工具层，用于仓库检查。V2 中这些工具不会连接到 API 或智能体循环，只作为 V3 的可复用基础。

## 工具

### `list_files(repo_path: str) -> list[str]`

返回 `repo_path` 下类似文本的仓库文件，路径相对 `repo_path`。

### `read_file(repo_path: str, file_path: str, max_chars: int = 12000) -> str`

读取 `repo_path` 内的文本文件，最多返回 `max_chars` 个字符。

### `search_code(repo_path: str, keyword: str, max_results: int = 20) -> list[dict]`

在 `repo_path` 内搜索文本文件，返回包含文件路径、行号和行文本的匹配片段。

## 安全要求

- 所有文件访问必须限制在 `repo_path` 内。
- 拒绝 `../` 等路径穿越。
- 跳过 `.git`、`__pycache__`、`.venv` 和 `node_modules`。
- 跳过隐藏目录。
- 不读取 `.env`、`.npmrc`、`.pypirc`、`.netrc`、密钥文件、证书文件或凭据类文件。
- 不写文件。
- 不删除文件。
- 不执行 shell 命令。
- 忽略二进制文件。
- 限制 `read_file` 输出大小。
- 限制 `search_code` 返回结果数量。

## 非目标

- 真实 LLM 接入。
- 智能体循环。
- 技能加载器。
- 反思检查。
- 评测。
- 自动修改代码。

## 验收标准

- `list_files` 返回普通代码文件。
- `list_files` 跳过敏感文件和忽略目录。
- `read_file` 可以读取 repo 内文件。
- `read_file` 拒绝 repo 外文件。
- `read_file` 拒绝敏感文件。
- `search_code` 返回匹配文件路径、行号和行文本。
- `search_code` 找不到关键词时返回空列表。
- `search_code` 不返回敏感文件内容。
- `pytest` 通过。
- 安装 ruff 后，`ruff check .` 通过。
