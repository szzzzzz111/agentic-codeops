# Internal Plan Review

Review subject：proposal、design、tasks、两份 delta specs、stage planning、Harness allowlist/checklist，及直接
相关 provider/runner/scripts/spec current facts。结论只覆盖 plan contract，不证明 implementation、tests、live
authority、archive、candidate、merge 或 push。

## Findings And Dispositions

### IR-P1-001 — 两套 scan 实现会让 canonical semantics 再次漂移

- Trigger：原计划新增 Python stage-doc/skill-eval scans，但保留两个 PowerShell scans 的独立逻辑。
- Consequence：单独运行 PowerShell scan 时可能漏掉 Python canonical entry 的 required checks，产生平台相关
  假 PASS。
- Disposition：`fix / closed`。Allowlist 加入两个 PowerShell scan；design/tasks/spec/checklist 统一要求三个
  PowerShell scripts 都是 thin wrappers，只有 Python 保存检查逻辑。

### IR-P1-002 — “Ruff 仍为 96”不是实现后的稳定事实

- Trigger：provider/runner/tests 本身包含初始 Ruff findings，而本阶段要求 changed-file Ruff 绿。
- Consequence：实现会改变全仓 residual count；继续写固定 96 会让 successor inventory 与 canonical verify
  证据漂移。
- Disposition：`fix / closed`。96 只保留为首次 baseline；implementation 后重跑 full Ruff 并把 exact residual
  inventory 交给 successor，不预设数量。

### IR-P1-003 — 当前 stage 单独 push 会早于 overall full-green gate

- Trigger：原 tasks 允许当前行为 stage ff-merge/push，而 full Ruff/canonical verify 明确留给 successor。
- Consequence：`origin/main` 会在 overall acceptance 未满足时收到一个仍红的中间态，违背用户“全部门禁后
  push”的确认。
- Disposition：`fix / superseded by first-round remediation`。初次先收窄到 `commit`，但 slot A 正确指出 v1
  `archive` gate 会被该 ceiling 阻断；最终修正为 v1 `archive` ceiling，允许 implement/commit/archive、阻断
  merge/push。Successor 以新的 plan/authority 从 post-archive local candidate 开始，full
  pytest/Ruff/canonical verify 全绿后才把两阶段 commits 一起 ff-only merge/lease push。

### IR-P2-004 — OpenSpec all-strict 有一个 checkout 既有 warning

- Evidence：active change strict PASS；`validate --all` 为 25/25 PASS；`validate --all --strict` 仅因未修改
  `openspec/specs/verified-patch-promotion/spec.md` Purpose 少于 50 字符而 24/25。
- Disposition：`defer / non-blocking for current plan`。该路径不属于当前直接依赖，不能顺手扩大 scope；
  报告 exact claim ceiling，不声称 all-strict PASS。

## First-Round Independent Review

Frozen packet：`b8c9cfaf5ea9744dd40e435e841a49ff01da44e037189b1f49b9575fbd966163`。
两席均由 host 以 `fork_turns="none"` 分别 dispatch；首轮互不可见，超时 recovery 复用原实例且不改变 round。

### Slot A — `/root/plan_review_a`

- `RVPA-P1-001` `fix / closed in remediation`：v1 `commit` ceiling 不能通过 archive；改为 v1 `archive`
  ceiling，并要求 dry-run exact action matrix。
- `RVPA-P1-002` `fix / closed in remediation`：module-missing stderr 可能泄露不在 prefix regex 内的
  `sys.executable`；增加 standalone preflight、stable unavailable 与 raw/resolved executable redaction/
  projection tests。
- `RVPA-P2-003` `fix / closed in remediation`：portable scans 代表性测试不足；冻结完整 old-to-new parity
  failure-family matrix。
- First-round verdict：`blocked`。

### Slot B — `/root/plan_review_b`

- `B-PLAN-P1-001` `fix / closed in remediation`：string closing quote 前 backslash 奇偶未冻结；增加 1/2/3/4
  parity 与 128/129 trailing structure cases，并精确定义 top-level depth。
- `B-PLAN-P1-002` `fix / closed in remediation`：与 A 独立发现 standalone module-missing executable path
  leakage；同一 preflight/redaction/projection remediation 关闭。
- `B-PLAN-P1-003` `fix / closed in remediation`：Python canonical entry 未冻结 repo cwd；从 script path 解析
  canonical root，所有子检查固定 cwd，并从外部 cwd 回归。
- First-round verdict：`blocked`。

## Remediation Verdict

First-round P1/P2 已进入 plan contract。第一次 remediation re-review 中，A 关闭
`RVPA-P1-002`/`RVPA-P2-003`，但因 design 遗留 `commit` ceiling 继续阻断 `RVPA-P1-001`。B 关闭其三个首轮
findings，并新增：

- `B-PLAN-RR-P1-004` `fix / remediated, awaiting same-slot verification`：进程内 `find_spec()` 与普通 `-m`
  可能加载 repo/PYTHONPATH 中退出 0 的同名 pytest/Ruff，制造假 PASS。计划改为 probe/tool 均使用当前解释器
  `-I` isolated mode，只接受该解释器 canonical purelib/platlib，并加入 standalone/canonical shadow
  module/package adversarial tests。
- `B-PLAN-RR-P1-005` `fix / remediated, awaiting same-slot verification`：与 A 相同，design 同时冻结了
  `commit`/`archive` ceiling；现统一为 v1 `archive`。

第二次 semantics re-review 中 B 关闭上述两项且未发现新 P0/P1；A 关闭其原 findings，但新增
`RVPA-RR2-P1-004` `fix / remediated, awaiting same-slot verification`：简单拒绝 repo-root provenance 会误伤
`<repo>/.venv` 内的合法工具。计划保留 `-I`，改为信任 isolated interpreter 自身 `sysconfig` 报告的
canonical purelib/platlib roots；增加 repo-local venv 正例，同时拒绝 repo/PYTHONPATH/.pth 注入 shadow。

第三次 A re-review 关闭该兼容性 finding，但新增 `RVPA-RR3-P1-005`
`fix / remediated, awaiting same-slot verification`：`.pth` meta finder 可伪造 absent/`built-in`/`frozen` origin
绕过 containment。曾计划增加 concrete-origin containment，随后按 B 的反例收回这一过度复杂且无法抵抗 hostile
site hook 的方案。

同 packet 的 B refresh 指出 `-I` 仍执行 interpreter site `.pth`，后者可伪造可信-looking concrete origin；因此
“拒绝 hostile `.pth`”是未经实现支持的过度 claim。Disposition：`clarify / remediated, awaiting same-slot
verification`。本阶段现在把启动 RepoPilot 的当前解释器 canonical site/package installation 明示为受信前提，
最终最小合同只使用 `-I` 阻断 repo/caller cwd、user site 与 `PYTHONPATH` shadow；不声称 `-S` isolation 或
interpreter supply-chain integrity。原 sentinel-origin finding 因相关 provenance claim 被删除而关闭。

Fresh-context C/D 首轮在 packet `b8a1e0ae…54893` 各发现一个 P1：C 指出 outer verify/scanner/PowerShell
driver 未带 `-I`，hostile `PYTHONPATH` 可提前假成功；D 指出继承 `PYTEST_ADDOPTS=--collect-only` 可让 required
pytest 只收集不执行。Disposition 均为 `fix / remediated, awaiting same-slot verification`：所有 Python
driver/scanner 委托统一加 `-I`；standalone/canonical pytest 删除 `PYTEST_ADDOPTS`/`PYTEST_PLUGINS`，固定
`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`，加入 bootstrap 与 marker regressions。

Final clean F 首轮另指出 post-archive candidate 与 PowerShell claim 两项 P1。Disposition：`fix / remediated,
awaiting same-slot verification`。计划要求 archive 后对 exhaustive staged semantic packet 做同席 final refresh，
ready 后仅追加 review-set/delivery-binding evidence tail；当前 host 只执行用户允许的 Python platform-equivalent
gate，PowerShell wrapper runtime 明确 `NOT_OBSERVED`，不虚报 Windows PASS。

当前状态：`READY_FOR_SAME_SLOT_REMEDIATION_RE_REVIEW`，尚未授权 implementation。A/B 必须各自绑定新的
同一 final packet，并以 lineage 关闭全部 finding IDs；mechanical review-set validator 与 host dispatch provenance
均未完成。
