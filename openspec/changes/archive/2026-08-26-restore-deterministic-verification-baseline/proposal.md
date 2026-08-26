## Why

最新 `origin/main` 的确定性验证基线不闭合：全仓 pytest 可复现三个 failure，其中一个深层
JSON object response 被 provider 接受，另外两个 Verification Runner 测试依赖 PATH 中不存在的裸
`python`；仓库一键验证还会在 Ruff 缺失时 warning 后跳过，并把 `pytest`、`ruff` 与 PowerShell 解析交给
环境 PATH。与此同时，上一阶段 current-fact 文档仍把中间 packet `bce8…` 写成 final packet，实际正式
final packet 是 `7ecc…`。

首次 Ruff baseline 为 96 项、分布于 56 个文件。把它们塞进本次 provider/runner 行为修复会破坏小阶段
边界，因此本 change 只恢复行为与验证入口核心，随后在同一隔离分支从本阶段 local candidate 开始独立
机械 Ruff 清理阶段。在两者都完成前，不 merge/push、不声称 full repository verification baseline
restored，也不开始 model patch authoring。

## What Changes

- 为 JSON object response 增加确定性 nesting-depth fail-closed 校验，不依赖 Python 版本或进程 recursion limit；
  保留 `json.loads`、顶层 object 和 caller-owned business schema 边界。
- 让 Verification Runner 的 `pytest`、`ruff` 与 `verify` 固定使用当前 `sys.executable`；pytest/Ruff probe
  与执行使用 isolated mode，阻断 repo/PYTHONPATH 同名 module 假 PASS，并让 helper-script 测试同样使用
  当前解释器。
- 新增跨平台 Python 验证入口，以固定顺序运行 pytest、Ruff、stage-doc scan 和 skill-eval scan；缺少
  pytest/Ruff 或任一子检查失败时明确非零退出。三个 PowerShell 入口都只委托对应 Python driver，不再
  维护另一套扫描逻辑或跳过 Ruff；所有 Python driver/scanner 使用 isolated mode，pytest 不接受继承环境把
  required run 改成 collect-only。
- 同步验证入口与 provider fail-closed 的 OpenSpec/architecture/feature/docs 事实。
- 修正上一阶段 current-fact 文档中的 final packet 与已验证 push 事实，不改写历史 receipt 内容。

## Capabilities

### Modified Capabilities

- `grounded-answer-model-provider`: JSON object response 必须在受支持的结构深度内，超限安全失败。
- `verification-runner`: 三个白名单标签固定到当前解释器；canonical verify entry 跨平台、缺工具 fail closed。

## Impact

- Runtime：`app/providers/model_provider.py`、`app/verification/runner.py`。
- Tests：provider 深度边界、runner 当前解释器、跨平台 verify driver positive/negative cases。
- Scripts：Python canonical verify/stage-doc/skill-eval entry 与薄 PowerShell wrapper。
- Durable facts：README、ARCHITECTURE、AGENT_RULES、FEATURE_LIST、PROGRESS、HANDOFF、Harness commands。
- 不改变公开 API、默认 provider、网络默认、依赖、持久化、patch apply/promotion、Git 自动化或 replay v2。
