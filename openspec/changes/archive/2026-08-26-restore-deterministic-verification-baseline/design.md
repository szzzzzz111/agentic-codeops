## Context

本 change 基于 live `origin/main` OID
`2c0d0d4e749e16e43d867931c58c6a82be56cf13`，在新 worktree
`/private/tmp/agentic-codeops-restore-verification.01a03bfc` 规划。原脏 worktree 不在 editable surface。

原生 baseline 使用仓库现有 Python 3.12.13 解释器：pytest 9.1.1 得到
`916 passed, 3 failed`；Ruff 0.16.0 得到 `96 errors`，跨 56 文件。主机没有 PowerShell，系统
`python3` 是 3.9.6 且未安装 pytest/Ruff。这证明 PATH 裸命令与 PowerShell-only entry 都不能作为可重复
验证语义。

## Goals / Non-Goals

**Goals**

- 对 JSON object response 施加明确、确定性的 nesting 上限，并安全拒绝超限内容。
- 让产品 Verification Runner 与仓库 verify entry 使用启动它们的同一 Python 解释器。
- 让 pytest/Ruff 缺失成为明确失败，而不是 skip 或环境偶然性。
- 在 macOS/Linux/Windows 上共享同一 Python canonical verification sequence。
- 修正 predecessor final packet/current push 的事实偏差。

**Non-Goals**

- 当前 change 不清理 56 文件的 Ruff baseline；后继机械 change 负责，且在其完成前不进入下一产品阶段。
- 不引入 JSON Schema 或校验 Long Task/Patch 业务字段。
- 不改变 provider prompt、真实模型启用方式、默认 fake/offline 或 audit payload。
- 不增加任意验证 argv、shell、自动 patch/apply/verify/promote/Git action。
- 不处理 Verification Runner 子进程树 containment。
- 不激活 replay v2 或引入持久化 Operator approval。

## Decisions

### 1. Raw JSON nesting scanner precedes `json.loads`

增加固定 `MAX_JSON_NESTING_DEPTH = 128`。对 `json_object` response 在 `json.loads` 前做单遍 raw-text
扫描：只在字符串外统计 `{`/`[` 与 `}`/`]`，正确处理 quote 与 backslash escape；深度首次超过 128
立即返回现有 `ProviderResponseValidationError`。scanner 只负责资源/结构深度 ceiling，不取代 JSON parser，
不尝试验证括号匹配、类型或业务 schema。

选择 128 是为了给控制面 JSON 留出远高于正常 payload 的空间，同时避免把 CPython 当前 decoder/recursion
实现细节当合同。深度精确定义为“包含顶层 object 的同时打开 container 数”：顶层 `{` 是 1，128 可接受，
129 必须拒绝。边界测试覆盖 object/array、字符串内结构字符，以及 closing quote 前连续 1/2/3/4 个
backslash 的奇偶语义：奇数表示 quote escaped，偶数表示 quote 结束；随后紧跟的 128/129 层结构仍必须正确
计数。若 plan review 要求不同常量，必须在实施前冻结并重算 packet。

拒绝通过临时修改 `sys.setrecursionlimit` 触发 `RecursionError`：它是进程全局状态、并发不安全且跨解释器
不稳定。拒绝只 catch `RecursionError`：当前 Python 3.12 已证明 1100 层 response 可能解析成功。

### 2. Whitelisted argv uses an isolated current interpreter

`pytest` 映射为 `[sys.executable, "-I", "-m", "pytest"]`，`ruff` 映射为
`[sys.executable, "-I", "-m", "ruff", "check", "."]`，`verify` 映射为
`[sys.executable, "-I", "scripts/verify.py"]`。仍使用 argv list、`shell=False`、固定 cwd、timeout、输出截断与
脱敏；用户不能提供额外参数。

对 standalone `pytest`/`ruff`，`run_whitelisted_verification` 在真正 tool spawn 前先启动一个受控的当前解释器
isolated-mode probe；probe 与真正 tool argv 都带 `-I`，从 import search path 排除 caller cwd、repository cwd、
user site 与 `PYTHONPATH`。probe 在 isolated child 内执行 `importlib.util.find_spec()`，只用退出码表达 module
available/unavailable，stdout/stderr 一律丢弃；module 缺失或 probe 异常时不启动真正 tool subprocess，返回
`unavailable` 与稳定、脱敏的 `verification_tool_unavailable:<label>`。不得用当前 RepoPilot 进程内的
`find_spec()` 代替 isolated probe，因为该进程可能已包含 repository root/PYTHONPATH。
即使 module 在 preflight 后执行失败，通用 output redactor 也必须在现有 repo/local/secret 投影前精确替换
`sys.executable` 与 `Path(sys.executable).resolve()`，防止 `/Library`、`/Applications`、`/workspace` 或 `/nix`
等未被前缀 regex 覆盖的解释器路径进入 answer/tool-call/persistent audit。

adversarial tests 在 fixture repository 与 hostile `PYTHONPATH` 分别放置退出 0 的 `pytest.py`/`ruff.py` 及同名
package，冻结 standalone labels 与 canonical entry 都不会加载它们、不会返回 success；正例覆盖 repo-local
virtualenv 中正常安装的 pytest/Ruff。probe failure 与真实工具 missing 共用 fail-closed unavailable contract。

pytest probe 与实际执行使用受控 environment：删除继承的 `PYTEST_ADDOPTS` 与 `PYTEST_PLUGINS`，并固定
`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`。repository-owned pytest config 仍正常读取，但 ambient env 不能把 required
run 改成 `--collect-only` 或注入自动 plugin。standalone/canonical 共用此规则；marker regression 证明测试体执行。

当前解释器及其 canonical site initialization/package installation 是本阶段的受信运行前提；`-I` 仍会处理该
解释器 site 的 `.pth`。本 change 不声称抵抗已被恶意篡改、可伪造 import metadata/loader 的 interpreter site，
也不做第三方工具供应链证明。若未来要把 interpreter site 设为不可信，需单独设计 `-S` bootstrap、跨平台 venv
root derivation、distribution integrity 与依赖加载合同，不能在本阶段的 accidental-shadow 修复里暗示已完成。

测试中需要执行临时 Python script 的两个 case 改用 `sys.executable`。这只消除测试的 PATH 偶然性，不改变
runner 对真正不存在的命令返回 `unavailable` 的合同。

### 3. One Python canonical verify sequence, thin platform wrappers

`scripts/verify.py` 通过 `Path(__file__).resolve().parent.parent` 冻结 canonical repository root；无论 caller
cwd，它都让所有 subprocess/scan 使用该 root。两个 Python scanners 同样从自身位置解析 root，并只为 tests
接受显式 project-root 参数。canonical entry 固定执行：

1. 以 `-I` isolated subprocess preflight 当前解释器可解析 `pytest` 与 `ruff`；任一缺失或 probe 异常时打印
   稳定、脱敏的 tool-unavailable 错误并退出 2；
2. `sys.executable -I -m pytest`；
3. `sys.executable -I -m ruff check .`；
4. `sys.executable -I scripts/check_stage_docs.py`；
5. `sys.executable -I scripts/check_skill_evals.py`。

子命令按首个非零状态立即失败。两个 Python scan 是现有 PowerShell scan 的等价移植，并用完整 parity
matrix 覆盖每个独立 failure family，而不是代表性抽样：stage-doc 包含 required files、spec Purpose
placeholder、HANDOFF markers/version-history/current-HEAD、workflow requirements、current-fact stale patterns、
PROGRESS next-step heading/stale/V24 与 README duplicated headings；skill-eval 包含 skill/eval missing、description
single-line/Use-or-Load/50-word、eval reference 与四个 required sections。`scripts/verify.ps1`、
`scripts/check_stage_docs.ps1` 与 `scripts/check_skill_evals.ps1` 都变成薄 wrapper，只解析显式参数或可用的
Python 解释器并以 `-I` 委托对应 Python driver；解析失败明确非零。产品 `verify` label 直接使用当前
`sys.executable` 调 canonical Python entry，所以不依赖 PowerShell。

拒绝保留“找不到 Ruff 就 warning-and-skip”：它会把未执行检查误报为完成。拒绝分别维护 Windows 与 POSIX
两套验证顺序：它们会继续漂移。

### 4. Ruff cleanup is a separate mechanical stage with an overall phase gate

初始 96 项中 55 项为 import ordering，剩余包含 BLE001、B023、TRY004 等语义敏感规则，跨
app/evals/tests 56 文件；它不是本 change 的窄直接依赖。当前 stage 的 changed-file Ruff 修复可能顺带关闭
这些文件上的初始 finding，因此 implementation 后必须重新生成 residual inventory，不能继续宣称固定为 96。
随后从本阶段 local candidate 开启 `clear-repository-ruff-baseline`：先 safe autofix，再逐项人工处理非
fixable 规则，禁止全局 ignore；每批运行相关 pytest，最终 full pytest/Ruff/canonical verify 全绿。

两个 stages 都完成前，overall `restore-deterministic-verification-baseline` acceptance 未满足，model patch
authoring 继续停止。当前 stage 可 archive 并形成 local reviewed candidate，action ceiling 为 `archive`；
不得 merge/push，也不得把阶段内的局部验证表述为 full baseline PASS。后继机械 stage 使用新的精确 scope/
authority，在整体全绿后把两阶段 commits 一起 ff-only merge/lease push。

### 5. Predecessor hashes are current facts, not history rewrites

只修正 README/HANDOFF/PROGRESS/Harness current-fact sections 对 predecessor 的错误摘要：final review packet
为 `7eccf12cf3b8793c52a7e5146ffe6698746f69b19d212f0b0d272aebcf636500`，candidate/pushed commit 为
`2c0d0d4e749e16e43d867931c58c6a82be56cf13`。历史 review-set 中的 first-round/intermediate packet/receipt
hash 保持原样。

## Risk And Failure Semantics

- Scanner 若把字符串内 brace 算作 nesting 会拒绝合法 JSON；边界与 escape 测试阻断。
- Scanner 若尝试代替 parser 可能接受 malformed JSON；所有内容仍必须经过 `json.loads` 和顶层 dict 校验。
- `sys.executable` 是本机绝对路径；standalone isolated probe 避免 repo/PYTHONPATH 同名 module 冒充工具，
  同时允许 repo-local venv 的合法 installed tool。interpreter site 本身是明示的受信前提。probe 输出
  不进入用户投影，通用 redactor 仍精确遮蔽 executable raw/resolved forms；tests 必须覆盖 standalone、
  answer/tool-call/persistent audit、hostile shadow modules 与 repo-local venv 正例。
- Canonical entry 若继承 caller cwd 可能验证错目录；所有 Python entry 固定 script-derived repo root，并从
  外部 cwd 做 regression；所有 driver/scanner argv 使用 `-I`，hostile `PYTHONPATH` regression 不能提前假成功。
- pytest 若继承 `PYTEST_ADDOPTS=--collect-only` 可只收集不执行；standalone/canonical 清理 command-shaping
  `PYTEST_*` inputs，marker regression 证明测试体实际执行。
- Python verify port 若少检查一项会造成假 PASS；tests 与 Stage Debt Sweep 对照 PowerShell source 的完整集合。
- 当前 stage 的 canonical verify 仍会因重新测得的 residual Ruff inventory 非零；该失败是 successor gate，
  不得包装成 PASS，也不得在此时 merge/push。

## Authority And Delivery

- Risk：high / L3；plan 与 implementation 各两个独立 slots。
- Active cohort：pre-change `stage_authority/v1`；replay v2 dormant。
- Host-retained envelope：stage id、epoch/record hash、risk、scope digest、planning base、v1 `archive` ceiling、origin、
  fetch/push fingerprint、main、authorized old tip。Repository record/hash 只作 mechanical binding。
- scope/risk/base/action/endpoint/branch/tip 漂移使 authority 与 review packet 失效。
- V1 action ordering 固定为 `plan -> implement -> commit -> archive -> merge -> push`；`archive` ceiling 允许
  implement/commit/archive preflights并拒绝 merge/push。Post-archive finite candidate 仍调用较早 ordinal 的
  `required-action=commit`，不能借 dormant v2 重解释 ordering。
- P0/P1 未清零、OpenSpec/required verification/review gate 未满足时不 archive/commit；overall full verification
  未绿时不 merge/push。
- Pre-archive implementation review 不能覆盖 archive 产生的文件移动/spec sync。Archive 后必须重建 exhaustive
  staged subject packet，并由同两个 implementation reviewers 刷新；其 ready receipts 之后只允许写 schema-valid
  final review-set 与 delivery-binding 两文件 evidence tail，再做 exact staged-index/manifest check。任何其他
  semantic post-review 写入都使 final review 失效。
- 当前主机没有 PowerShell；本阶段以 `scripts/verify.py` 作为用户允许的 platform-equivalent executable gate。
  三个 PowerShell wrappers 只做静态/结构测试，运行态标记 `NOT_OBSERVED`，不声称 Windows/PowerShell PASS。
