## MODIFIED Requirements

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

#### Scenario: Reviewed repository Ruff baseline is clean

- **WHEN** canonical entry 对 reviewed repository candidate 运行 required Ruff check
- **THEN** Ruff SHALL 在不增加 ignore、`noqa` blanket 或规则降级的前提下返回零
- **AND** canonical entry SHALL 继续运行后续 required scanners，而不是把 Ruff 标为 skipped
