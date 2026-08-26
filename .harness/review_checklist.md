# 当前 Review 清单

Archived OpenSpec change：`openspec/changes/archive/2026-08-26-restore-deterministic-verification-baseline/`。

Risk：`high / L3`。Plan review 与 implementation review 均要求 internal review + 两个互相隔离的
独立 reviewer slots；首轮 reviewer 使用 `fork_turns="none"`，审同一 content-addressed packet，且不能读取
其他 slot 结论。Repo receipt/validator 只证明 `mechanical_consistency_only`；宿主另行核对 dispatch provenance、
direct-user authority、live Git target 与 push outcome。

## Scope 与前置事实

- [x] 仅在 `/private/tmp/agentic-codeops-restore-verification.01a03bfc` 实施；原脏 worktree 无变化。
- [x] Planning base、live `origin/main` 与 authorized old tip 均为
  `2c0d0d4e749e16e43d867931c58c6a82be56cf13`。
- [x] Endpoint fetch/push 唯一、相等且 SHA-256 均为
  `775bee2fb56e792fc9057a93c77c948cdd627c0cc4afa23497d41f7c6276d16c`。
- [x] 首次 baseline 保留：Python 3.12.13；pytest `916 passed, 3 failed`；Ruff
  `96 errors / 56 files`；当前主机没有 PowerShell。
- [x] Ruff 初始 96 项拆入后继 `clear-repository-ruff-baseline` 机械阶段；当前 changed-file Ruff 修复可能
  减少其数量，因此 implementation 后必须重测 residual inventory，不把“96”写成永恒计数。
- [x] 本阶段与后继 Ruff 阶段都完成前，不宣称 full baseline restored，不进入 model patch authoring。

## Plan Review Gate

- [x] Internal review 已检查 proposal/design/tasks/spec deltas/Harness 交叉一致性；三个 P1 plan findings 已修复。
- [x] Active change strict PASS；OpenSpec all non-strict `25 passed, 0 failed`。
- [x] OpenSpec all strict 的唯一既有 warning 是未修改
  `openspec/specs/verified-patch-promotion/spec.md` Purpose 少于 50 字符；不把它报成当前 change failure/PASS。
- [x] Plan slot A/B 首轮审同一 frozen packet，`fork_turns="none"` 且互不可见。
- [x] 如有 finding，same-slot remediation 后 A/B final receipt 绑定同一 final packet。
- [x] `validate_independent_review.py --phase plan --required-slots 2` mechanical PASS，宿主另验 dispatch provenance。

## Provider JSON fail-closed

- [x] TDD RED 明确证明当前 1100 层 JSON response 会被错误接受。
- [x] Provider 使用确定性、与解释器 recursion limit 无关的 JSON nesting 上限；scanner 正确忽略字符串内
  brace/bracket 与 escape，`json.loads` 仍负责语法和顶层 object 校验。
- [x] 深度定义为“包含顶层 object 的同时打开 container 数”；128 允许、129 拒绝。
- [x] 上限边界、深层 object/array、字符串内结构字符，以及 string closing quote 前连续 1/2/3/4 个
  backslash 的 escape parity 均有测试；偶数 backslash 后 quote 必须结束 string，后续 129 层不能被忽略。
- [x] 超限结果为现有安全 `ProviderResponseValidationError`，answer 为空，audit 不包含完整 output。
- [x] 默认 fake/offline、grounded text、finish reason、metrics 与 caller-owned business schema 不变。

## 当前解释器与缺工具失败语义

- [x] Verification Runner 的 `pytest`、`ruff`、`verify` argv 均绑定 `sys.executable` 并使用 `-I`
  isolated mode，不依赖 PATH 中裸 `python`、`pytest`、`ruff` 或 PowerShell。
- [x] 两个 helper-script 测试改用 `sys.executable`，仍分别验证 nonzero/redaction 与 timeout/truncation，
  不把 runtime `unavailable` 行为改成假成功。
- [x] `scripts/verify.py` 是平台等价 canonical entry：固定顺序运行当前解释器的 pytest、Ruff、stage-doc
  scan 与 skill-eval scan，driver/scanner argv 都带 `-I`，任一步非零立即非零退出；hostile `PYTHONPATH`
  不能在 required checks 前返回零。
- [x] `scripts/verify.ps1`、`scripts/check_stage_docs.ps1` 与 `scripts/check_skill_evals.ps1` 都只作薄入口，
  调用对应 Python canonical driver；找不到 Python 时明确非零失败，不维护第二套扫描逻辑。
- [x] pytest 或 Ruff module 缺失时有明确、脱敏错误并 fail closed；无 warning-and-skip 分支。
- [x] Standalone/canonical pytest 删除继承的 `PYTEST_ADDOPTS`/`PYTEST_PLUGINS`，固定
  `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`；`PYTEST_ADDOPTS=--collect-only` regression 仍执行 marker test body。
- [x] Standalone `pytest`/`ruff` labels 在真正 tool spawn 前用当前解释器 isolated subprocess 预检 module；
  probe/tool 都使用 `-I`；module 缺失或 probe 异常返回稳定 unavailable。repo-local `.venv` 的正常 installed
  tool 必须通过；fixture repo 或 hostile `PYTHONPATH` 中退出 0 的 `pytest.py`/`ruff.py`、同名 package 不能被
  standalone/canonical entry 加载并制造假 PASS。作为
  defense-in-depth，output redactor 还必须精确遮蔽 `sys.executable` 及其 resolved path，覆盖 answer、tool-call
  与 persistent audit projection。
- [x] Python 版 stage-doc/skill-eval scan 与现有职责合同等价，且有 positive/negative tests；不减少 required
  files、markers、stale patterns 或 skill eval sections。
- [x] Stage-doc parity matrix 逐项覆盖：required files、spec Purpose placeholder、HANDOFF required markers、
  version-history/current-HEAD 禁止项、workflow required requirements、current-fact stale patterns、PROGRESS
  next-step heading/stale/V24、README duplicated headings。
- [x] Skill-eval parity matrix 逐项覆盖：skill/eval file missing、single-line description、Use/Load prefix、50-word
  ceiling、eval reference、Positive/Negative/Edge/Failure Traps sections。
- [x] `scripts/verify.py` 与两个 Python scanners 都从自身 path 解析 canonical repository root；无论 caller cwd，
  四类 subprocess/scan 都固定到该 root，且有从外部 cwd 绝对启动的 regression。
- [x] Verification output redaction、argv list、`shell=False`、cwd、timeout、白名单与公开 schema 保持不变。
- [x] 当前解释器 site/package installation 是受信前提；不把未实现的 interpreter supply-chain 防护报成 PASS。

## 文档与上一阶段事实修正

- [x] 只把 current-fact 文档中的旧 packet `bce8efe0…eea7` 修正为正式 final packet
  `7eccf12cf3b8793c52a7e5146ffe6698746f69b19d212f0b0d272aebcf636500`。
- [x] durable PROGRESS 准确记录 predecessor candidate/pushed commit
  `2c0d0d4e749e16e43d867931c58c6a82be56cf13`；历史 first-round/intermediate receipt hash 不篡改。
- [x] README/ARCHITECTURE/FEATURE_LIST/AGENT_RULES/test commands 只更新由本阶段改变的验证事实。
- [x] HANDOFF 不把当前未完成阶段、Ruff debt 或 push 状态预写成完成。

## 验证、review 与停止条件

- [x] Focused RED/GREEN：model provider、verification runner、verify scripts。
- [x] Adjacent：provider + long-task/patch authoring；verification runner + AgentLoop/chat/worktree reverification。
- [x] Full pytest 绿；changed-file Ruff 绿；全仓 Ruff residual 重新计数并精确列入后继机械阶段。
- [x] `scripts/verify.py` 在本阶段行为修复后只因重新测得的 residual Ruff inventory 非零，且不会跳过 Ruff；
  后继机械阶段后全绿。
- [x] OpenSpec active strict/all、stage docs、skill eval、`git diff --check` 全部通过。
- [x] 当前主机执行 `scripts/verify.py` platform-equivalent gate；PowerShell wrappers 做静态/结构测试，但因无
  PowerShell 其 runtime 明确 `NOT_OBSERVED`，不得报告为 Windows PASS。
- [x] Stage Debt Sweep 仅覆盖 changed runtime/tests、直接 caller、验证入口与事实所有者文档。
- [x] Pre-archive internal review 与两个独立 implementation slots 的 P0/P1 全部关闭并绑定同一 packet。
- [ ] Archive 后重建 exhaustive staged semantic packet并让同两个 implementation reviewers 刷新；final ready
  后只允许追加 review-set/delivery-binding 两文件 evidence tail，任何其他写入使 review 失效。
- [x] Replay v2 保持 dormant；authority v1 record 只作 mechanical binding。
- [ ] 当前 v1 stage 的 ceiling 为 `archive`，可通过 implement/commit/archive preflight但阻断 merge/push；
  只产出 post-archive local candidate。后继 Ruff stage 重新冻结 authority，并仅在
  full pytest/Ruff/canonical verify 全绿后一起 ff-only merge/lease push 两阶段 commit。
- [ ] scope/risk/base/target/endpoint/tip 漂移，或需要 allowlist 外写入时，停止并重新规划。
