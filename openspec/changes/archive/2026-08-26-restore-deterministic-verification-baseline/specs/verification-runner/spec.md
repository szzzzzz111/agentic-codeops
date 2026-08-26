## MODIFIED Requirements

### Requirement: Verification Runner 只执行明确验证请求

系统 SHALL 只在用户发送明确验证请求时触发 Verification Runner。验证请求 MUST 解析为白名单命令标签，
MUST NOT 接受任意 shell 文本、附加参数、管道、重定向或环境变量注入。

白名单 SHALL 只包含 `pytest`、`ruff` 和 `verify` 三个稳定标签。三个标签 MUST 使用运行 RepoPilot 的当前
Python `sys.executable`：`pytest` 映射为 `-I -m pytest`，`ruff` 映射为 `-I -m ruff check .`，`verify` 映射为
`-I scripts/verify.py` canonical entry。所有 Python driver/scanner invocation MUST 使用 isolated mode；
pytest/Ruff 的 module resolution MUST NOT 从
repository cwd、caller cwd、user site 或 `PYTHONPATH` 加载同名 module/package。系统 MUST NOT 依赖 PATH 中裸
`pytest`、`ruff`、`python` 或 PowerShell。
系统 MAY 支持中英文触发词，但 MUST 在执行前归一化为白名单标签。

V18 Patch + Verify Loop 中的 verification label MUST 复用同一白名单语义。组合确认中的 verification label
非白名单、含参数、含 shell 语法或缺失时，系统 MUST 拒绝整个组合请求，MUST NOT 先 apply patch 后再拒绝
verification。

#### Scenario: 明确验证请求触发当前解释器命令

- **WHEN** 用户发送 `运行 pytest`
- **THEN** 系统 SHALL 将请求解析为 `pytest` 标签
- **AND** argv SHALL 使用当前 `sys.executable -I -m pytest`
- **AND** 系统 MAY 进入 `verification_run` 权限审批链路

#### Scenario: 任意 shell 文本被拒绝

- **WHEN** 用户发送包含管道、重定向、环境变量赋值或额外 shell 参数的验证请求
- **THEN** 系统 MUST 拒绝执行
- **AND** 系统 MUST 返回支持的白名单命令标签摘要

#### Scenario: 组合确认中的非法验证标签拒绝整个组合

- **WHEN** 用户发送 `确认 patch patch_abc 并运行 ruff --fix`
- **THEN** 系统 MUST 拒绝整个组合请求
- **AND** 系统 MUST NOT 执行 `patch_apply`
- **AND** 系统 MUST NOT 运行验证

### Requirement: 验证执行必须限制 cwd、timeout 和输出

系统 SHALL 只通过 `ToolExecutor.verification_run(...)` 执行验证。runner MUST 使用 argv list 执行命令，
MUST NOT 使用 shell 字符串执行。执行 cwd MUST 限制为 resolved `repo_path`。

runner SHALL 为每次验证设置固定 timeout。stdout 和 stderr MUST 各最多保留 4000 字符。`/chat.answer` 中
验证输出摘要总计 MUST 最多保留 6000 字符，并 MUST 标记 `truncated=true/false`。timeout、命令缺失、
非零退出码和 runner 异常 MUST 返回结构化失败摘要，而不是破坏 `/chat` 请求。

pytest probe/执行 SHALL 使用受控 environment：MUST 删除继承的 `PYTEST_ADDOPTS` 与 `PYTEST_PLUGINS`，并
MUST 固定 `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`。repository-owned pytest configuration MAY 正常生效，但 ambient
environment MUST NOT 把 required run 改成 collect-only 或注入自动 plugin。standalone 与 canonical entry
MUST 复用同一规则。

白名单 `pytest` 与 `ruff` MUST 在真正 tool spawn 前用当前解释器的 isolated subprocess 预检对应 module；
probe 与真正 tool invocation MUST 使用 `-I`，以排除 caller/repository cwd、user site 与 `PYTHONPATH`。
module 缺失或 probe 失败时 MUST NOT spawn 真正 tool，MUST 返回 `unavailable` 与稳定
`verification_tool_unavailable:<label>`；preflight MUST NOT 使用可受 repository cwd/PYTHONPATH 影响的进程内
`find_spec()`。所有 subprocess output 在进入 answer、tool-call 或 persistent audit 前，除既有
repo/local/secret redaction 外，还 MUST 精确遮蔽当前 `sys.executable` raw path 与 resolved path。

#### Scenario: 非零退出码返回失败摘要

- **WHEN** 白名单验证命令以非零退出码结束
- **THEN** 系统 SHALL 返回 failed 状态、exit code 和截断后的输出摘要
- **AND** `/chat` 请求本身仍返回稳定 schema

#### Scenario: 验证命令超时

- **WHEN** 白名单验证命令超过固定 timeout
- **THEN** 系统 MUST 终止命令
- **AND** 系统 SHALL 返回 timed out 摘要

#### Scenario: Standalone verification module 缺失

- **WHEN** 当前解释器找不到 `pytest` 或 `ruff` module
- **THEN** runner MUST 在 spawn 前返回 `unavailable`
- **AND** stderr summary SHALL 只包含稳定 tool-unavailable marker，不得包含解释器绝对路径

#### Scenario: Repository-local 同名 module 不能冒充验证工具

- **WHEN** repository cwd 或 `PYTHONPATH` 中存在退出 0 的 `pytest.py`、`ruff.py` 或同名 package
- **THEN** isolated preflight 与真正 tool invocation MUST NOT 加载这些 shadow modules
- **AND** 系统 MUST NOT 因 shadow module 退出 0 而返回 success

#### Scenario: Ambient pytest options 不能把执行降为收集

- **WHEN** 父环境设置 `PYTEST_ADDOPTS=--collect-only`
- **THEN** standalone 与 canonical pytest MUST 忽略该继承值
- **AND** required test body MUST 实际执行，不得只收集后返回零

#### Scenario: Repo-local virtualenv 的 installed tool 仍受支持

- **WHEN** 当前 `sys.executable` 位于 repository 内的 virtualenv，且该环境正常安装 pytest/Ruff
- **THEN** isolated probe SHALL 接受该 installed tool
- **AND** repository 相对位置本身 MUST NOT 导致 unavailable

## ADDED Requirements

### Requirement: Current Interpreter Site Is An Explicit Trust Boundary

当前解释器的 site initialization 与 installed packages SHALL 是本阶段的受信运行前提。实现与文档 MUST NOT
把 hostile interpreter site 或第三方工具供应链完整性标为已验证。本 change 的 shadow-module 防护范围 SHALL
限于 caller/repository cwd、user site 与 `PYTHONPATH` resolution。

#### Scenario: 不夸大 isolated mode 的边界

- **WHEN** 报告本阶段 verification hardening 结果
- **THEN** 报告 MAY 声称 repo cwd/PYTHONPATH shadow 被阻断
- **AND** 报告 MUST NOT 声称 hostile interpreter site 或 installed loader 已被隔离

#### Scenario: 解释器路径被精确脱敏

- **WHEN** subprocess output 包含 `sys.executable` raw 或 resolved absolute path
- **THEN** answer、tool-call 与 persistent audit projection MUST NOT 包含该 path
- **AND** 既有 timeout、truncation、repo path 与 secret redaction MUST 保持有效

### Requirement: Canonical Repository Verification Fails Closed

仓库 SHALL 提供 `scripts/verify.py` 作为跨平台 canonical verification entry。它 MUST 从自身 canonical path
解析 repository root，使用自身 `sys.executable` 并让所有子检查固定以该 root 为 cwd；pytest/Ruff 的 probe 与
执行 MUST 使用 `-I` isolated mode；
入口按固定顺序运行
pytest、Ruff、stage documentation scan 与 skill eval structure scan；任一
检查非零 MUST 立即非零退出。`scripts/verify.ps1`、`scripts/check_stage_docs.ps1` 与
`scripts/check_skill_evals.ps1` MAY 作为薄平台 wrappers，但 MUST 委托对应 Python canonical entries，
MUST 使用 `-I`，MUST NOT 维护另一套 required-check 逻辑。canonical driver 启动两个 Python scanners 时也
MUST 使用 `-I`；hostile `PYTHONPATH` MUST NOT 在 required checks 前制造零退出。

pytest 或 Ruff module 缺失 MUST 返回明确的 tool-unavailable 错误和非零状态。入口 MUST NOT warning 后跳过
任何 required tool/check，也 MUST NOT 因 PowerShell 不可用而改变 canonical 验证集合。

#### Scenario: 所有 required checks 完成

- **WHEN** 当前 Python 同时提供 pytest/Ruff 且四类检查均返回零
- **THEN** canonical entry SHALL 返回零
- **AND** 输出 SHALL 说明每一类 required check 已执行

#### Scenario: Ruff 缺失时失败

- **WHEN** 当前 Python 无法 import Ruff
- **THEN** canonical entry MUST 返回非零并明确标识 Ruff unavailable
- **AND** MUST NOT 把静态检查标为 skipped 或把整体验证标为完成

#### Scenario: 平台 wrapper 使用同一 driver

- **WHEN** 用户从 PowerShell 运行 `scripts/verify.ps1`
- **THEN** wrapper SHALL 调用 `scripts/verify.py`
- **AND** Python 解析失败或 driver 非零 MUST 原样形成非零失败
- **AND** standalone stage-doc/skill-eval PowerShell wrappers SHALL 委托对应 Python scanners

#### Scenario: 从 repository 外启动 canonical entry

- **WHEN** caller 在 repository 外的 cwd 通过 absolute path 启动 `scripts/verify.py`
- **THEN** canonical entry SHALL 从自身 path 解析 repository root
- **AND** pytest、Ruff、stage-doc 与 skill-eval checks SHALL 全部固定到该 root

#### Scenario: Canonical entry 不接受 shadow tool 假成功

- **WHEN** repository 或 inherited `PYTHONPATH` 提供退出 0 的 pytest/Ruff 同名 module 或 package
- **THEN** canonical entry SHALL 使用 isolated interpreter 的 installed tools，而不是 cwd/PYTHONPATH shadow modules
- **AND** 若 isolated installed tool 不存在，entry MUST 明确非零失败而不是返回零
