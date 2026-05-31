# memory Specification

## Purpose

记录 V13 已实现的轻量 Memory 边界：RepoPilot 使用 repo-local SQLite 保存 PREF/LTM，使用进程内 STM 保存短期会话记忆，并通过明确聊天指令进行记住、忘记和内部审计。Memory 是本地状态能力，不是代码修改能力；默认不调用网络、真实 LLM、外部数据库或向量记忆服务。
## Requirements
### Requirement: 系统提供 repo-local SQLite Memory 存储

系统 SHALL 提供 Memory 存储能力，默认使用目标 repo 内 `.repopilot/memory.sqlite3` 保存持久记忆。`.repopilot/` MUST 被 git 忽略。Memory 存储 MUST 使用 Python stdlib `sqlite3`，默认 MUST NOT 引入外部数据库、网络服务或新增运行时依赖。

Memory schema MUST 至少包含 `id`、`kind`、`scope`、`user_id`、`repo_key`、`session_id`、`key`、`value`、`created_at` 和 `updated_at`。`kind` MUST 固定为 `STM`、`LTM` 或 `PREF`。

#### Scenario: SQLite 初始化

- **WHEN** MemoryStore 针对有效 repo_path 初始化
- **THEN** 系统在 `.repopilot/memory.sqlite3` 中创建所需 schema
- **AND** 初始化不需要网络、API key 或外部服务

### Requirement: repo_key 使用稳定规范化路径 hash

系统 SHALL 使用稳定规范化规则计算 `repo_key`。系统 MUST 先使用 `Path(repo_path).resolve()` 得到真实绝对路径，再转换为 POSIX 分隔符字符串。Windows 下系统 MUST 对规范化路径执行 lower-case。系统 MUST 对规范化字符串计算稳定 hash，并且 audit MUST NOT 暴露原始绝对路径或 DB 路径。

#### Scenario: 等价 repo path 产生同一 repo_key

- **WHEN** 同一 repo 通过相对路径、不同分隔符或 Windows 大小写差异传入
- **THEN** 系统为该 repo 计算稳定一致的 `repo_key`
- **AND** audit summary 不包含原始绝对路径

### Requirement: Memory 按类型和 scope 隔离

系统 SHALL 区分 `STM`、`LTM` 和 `PREF`。`PREF` MUST 按 `user_id` 隔离，`LTM` MUST 按 `user_id + repo_key` 隔离，`STM` MUST 按 `user_id + session_id` 隔离。V13 的 STM MAY 使用进程内存储；PREF 和 LTM MUST 使用 SQLite 持久化。

#### Scenario: 用户和 repo 隔离

- **WHEN** 两个用户或两个 repo 写入同名 LTM key
- **THEN** 系统 MUST 按 user 和 repo 分别读取对应值

### Requirement: Memory 指令明确解析并确认优先

系统 SHALL 支持明确 memory 指令，并在解析前将全角冒号 `：` 归一化为半角 `:`。系统 MUST 支持 `记住: ...`、`请记住...`、`忘记: ...`、`请忘记...`、`remember: ...` 和 `forget: ...`。命中 memory 指令后，系统 MUST 返回确认式回答，MUST NOT 执行 repo_rag。

#### Scenario: 全角冒号记住偏好

- **WHEN** 用户发送 `记住：pref:language=中文`
- **THEN** 系统写入 PREF memory
- **AND** 响应通过现有 `answer` 字段确认
- **AND** `related_files` 和 `tool_calls` 均为空

### Requirement: Memory 写入分类和覆盖稳定

系统 SHALL 优先解析 `key=value` 格式。无 `=` 时系统 MUST 作为 note 存储并生成稳定 key。`stm:` 或 `会话:` MUST 写入 STM；`pref:` 或 `偏好:` MUST 写入 PREF；`project:` 或 `项目:` MUST 写入 LTM；未标注且包含“默认”、“喜欢”或“以后”等偏好词时 MUST 写入 PREF；其他未标注内容 MUST 写入 LTM。同一 scope、kind、key 的新值 MUST 覆盖旧值。

#### Scenario: 同 key 覆盖

- **WHEN** 同一用户对同一 scope 两次写入同一 memory key
- **THEN** 后一次值覆盖前一次值
- **AND** audit summary 记录 replaced 状态但不记录完整 value

#### Scenario: stm 前缀写入会话记忆

- **WHEN** 用户发送 `记住：stm:topic=V13 Memory review`
- **THEN** 系统写入当前 `user_id + session_id` 的 STM
- **AND** 后续同 session 的 memory summary 包含 STM count

### Requirement: Memory 删除先按 key 后按内容匹配

系统 SHALL 支持忘记指令删除 memory。删除 MUST 先按 key 精确匹配；找不到 key 时，MAY 按 value 内容包含匹配。系统 MUST 返回删除数量，并且 audit MUST NOT 记录完整删除内容。

#### Scenario: forget 按 key 删除

- **WHEN** 用户发送 `forget: language`
- **THEN** 系统删除匹配 key 的 memory
- **AND** 响应说明删除数量

### Requirement: Memory audit 脱敏且不公开暴露

系统 SHALL 为 memory 读写删除生成内部 audit summary。Memory audit MUST NOT 包含完整 memory value、完整 prompt、完整 Evidence Pack、API key、本机绝对路径或 DB 路径。Memory audit MUST NOT 进入 `/chat` 顶层字段或 `tool_calls`。

#### Scenario: memory audit 不进入公开响应

- **WHEN** `/chat` 处理 memory 指令或普通请求读取 memory
- **THEN** 内部 trace MAY 包含 memory summary
- **AND** `/chat` 响应仍只要求 `trace_id`、`answer`、`related_files` 和 `tool_calls`
- **AND** `tool_calls` 不包含 memory 内容

### Requirement: Memory 失败不破坏 repo search 主链路

系统 SHALL 在 memory command 写入或删除失败时返回脱敏失败回答，并且 MUST NOT 继续执行 repo_rag。普通 repo_search 请求读取 memory 失败时，系统 MUST 继续执行 repo_search，并在内部 trace 中记录 memory unavailable。

#### Scenario: 普通请求 memory read 失败

- **WHEN** 普通 repo_search 请求读取 memory 失败
- **THEN** 系统继续执行 repo_rag
- **AND** 内部 trace 记录 memory unavailable
- **AND** 公开响应不泄露本机路径或 DB 路径

### Requirement: Memory 提供只读控制面摘要

系统 SHALL 为 Assistant Control Surface 提供只读 Memory 摘要。摘要 MAY 包含 PREF、LTM 和当前 STM 的数量。摘要 MUST NOT 包含完整 memory value，MUST NOT 暴露本机绝对路径或 DB 路径。

#### Scenario: 控制面读取 Memory 摘要不创建 DB

- **WHEN** Assistant Control Surface 请求读取 Memory 摘要，且 `.repopilot/memory.sqlite3` 不存在
- **THEN** 系统返回 PREF/LTM 计数为 0 的摘要
- **AND** 系统 MUST NOT 创建 `.repopilot/` 目录或 `memory.sqlite3`
