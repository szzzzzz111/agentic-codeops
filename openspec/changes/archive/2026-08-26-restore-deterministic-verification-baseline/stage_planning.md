# Stage Planning

## Stage Summary

- Stage: `restore-deterministic-verification-baseline`
- Goal: 修复三个已复现 pytest failure，固定当前解释器与缺工具 fail-closed 的验证语义，并纠正 predecessor
  final packet 事实；Ruff baseline 作为紧随其后的独立机械 stage 清零，两个 stages 后才 merge/push。
- User-visible outcome: JSON 结构过深会安全失败；pytest/Ruff/verify 不再依赖 PATH 偶然性或静默跳过工具；
  在后继 Ruff stage 后，全仓 pytest/Ruff/canonical verify 可重复全绿。
- Planning base: `2c0d0d4e749e16e43d867931c58c6a82be56cf13`
- Active OpenSpec change: `restore-deterministic-verification-baseline`

## Scope

- In scope: provider JSON depth ceiling、Verification Runner current-interpreter argv、portable verify/doc/skill
  entry、相关 tests/spec/docs、predecessor packet facts。
- Out of scope: Ruff 96 清理（独立 successor）、model patch authoring、patch inspection/rejection、CLI worktree
  lifecycle、process-tree containment、replay v2、persistent approval、background/durable/subagent/connectors、
  product-level Git automation。
- Durable decisions affected: JSON object provider depth contract、verification label argv/entry contract、验证
  工具缺失失败语义、predecessor final packet/push facts。
- Assumptions: RepoPilot structured control JSON 正常不会接近 128 nesting；当前解释器就是启动 RepoPilot/
  verify driver 的 `sys.executable`；跨平台 scan 能逐项保持现有 PowerShell 检查集合。

## Risk Classification

- Level: `high / L3`
- Reason: provider response acceptance 与验证失败语义是安全/真实性边界；错误可能接受资源型恶意 JSON、
  跳过测试/lint 或误报 PASS。
- Required review: internal + two independent slots for plan and implementation，首轮空上下文隔离。
- Grilling Gate: 不适用；不新增易被误解为 runtime 的 MCP/Skill/subagent/connector/background 概念。

## Acceptance Criteria

- Functional: 深度含顶层 container；129+ nesting JSON fail closed，128 nesting 合法 object 可解析；
  strings/escapes 与 closing quote 前 1/2/3/4 backslash parity 不误计。
- Boundary: JSON business schema、provider default/audit/prompt、verification whitelist/shell/cwd/timeout/redaction
  不变；不触碰原脏 worktree。
- Failure behavior: standalone missing pytest/Ruff 在真正 tool spawn 前返回稳定、脱敏 unavailable；所有 Python
  driver/scanner argv 使用 `-I`；isolated
  probe/tool 使用 `-I`，允许 repo-local venv installed tool，但不从 repo cwd/PYTHONPATH 加载同名
  module/package；entry interpreter 缺失明确非零；无
  warning-and-skip；executable raw/resolved paths 不进入任何 projection；deep response 返回现有 error class与空 answer。
- Documentation: current facts 使用 final packet `7ecc…` 与 pushed commit `2c0d0d4…`；历史 receipts 不重写。
- Evidence: focused/adjacent/full pytest 绿；changed-file Ruff 绿；OpenSpec、portable scans、diff check 绿；重测
  residual Ruff；full Ruff/canonical verify 的最终全绿由 successor mechanical stage完成，之前 overall phase
  不完成且不 merge/push。当前 host 运行 Python platform-equivalent entry；PowerShell runtime 因工具缺失为
  `NOT_OBSERVED`，只保留 wrapper 静态/结构证据，不报跨平台运行 PASS。

## TDD And Verification

- First RED cases: 现有 1100 层 provider failure；新增 128/129/strings boundaries；runner exact argv；verify
  missing module 与 scan missing marker。
- Positive/negative/safety cases: 合法浅/边界 JSON、过深 object/array、strings/escape/backslash parity；
  nonzero/missing/timeout；tool missing、repo/PYTHONPATH shadow module/package/bootstrap、repo-local venv installed
  tool、`PYTEST_ADDOPTS=--collect-only` marker、executable redaction、external cwd、subcheck failure、完整 scan parity matrix。
- Focused verification: `tests/test_model_provider.py`、`tests/test_verification_runner.py`、
  `tests/test_verify_scripts.py`。
- Full verification trigger: runtime/tests/scripts changed，必须 full pytest；本 stage 重测 residual Ruff debt，
  successor 后必须 full Ruff + canonical verify。

## Review Plan

- Internal review target: depth scanner correctness、current-interpreter/audit leakage、portable scan parity、Ruff split
  的 gate 表述、事实 hash 不误写。
- External review: required，两个空上下文 slots。
- Independent counterexamples requested: braces/escapes/backslash parity、boundary off-by-one、missing/shadow module false
  success、repo-local venv compatibility、PATH/PYTHONPATH/PowerShell drift、scan check omission、局部 PASS 冒充
  full baseline、allowlist/authority drift。
- Stage Debt Sweep paths: changed provider/runner/tests/scripts，AgentLoop/chat/long-task/patch/worktree callers，
  provider/verification specs 与 current-fact docs。
- Delivery review: archive 后的完整 staged semantic subject 必须重新冻结并由同两个 implementation slots 刷新；
  ready 后只有 review-set/delivery-binding 两文件 mechanical evidence tail 可追加。

## Files And Durable Facts

- Allowed files: `.harness/allowed_files.md` 的 exact/prefix 集合。
- Review checklist additions: `.harness/review_checklist.md` 的 provider/verification/docs/full-phase gates。
- Durable docs whose owned facts change: README、ARCHITECTURE、AGENT_RULES、FEATURE_LIST、PROGRESS、HANDOFF、
  test commands、两份 long-term specs（archive sync）。
- Facts intentionally queried live: branch、HEAD、origin endpoint、remote main、active change、tool versions。

## Human Confirmation

- Internal plan review: three P1 findings closed（PowerShell duplicate scans、Ruff residual count、premature
  merge/push）；active strict 与 all non-strict PASS。All-strict 仅命中未修改 verified-patch-promotion Purpose
  过短的 inherited warning，不计当前 PASS。
- Decision: Ruff 96 跨 56 files，拆成 successor mechanical stage；本 stage 不加 ignore。
- Recommendation: 先关闭三个行为 failure 与 canonical entry，再机械清 lint；两个 stages 后才进入 model patch authoring。
- Authority activation state: direct-user overall implementation/push 已确认；当前 pre-change v1 stage 主动
  收窄为 `archive` ceiling（允许 v1 implement/commit/archive，阻断 merge/push），epoch/record 待 final plan
  packet 后冻结。Successor 需独立 plan/authority。
- Authority cohort: pre-change v1；replay v2 dormant。
- Host-retained authority inputs: stage=`restore-deterministic-verification-baseline`; risk=`high`;
  planning base/authorized tip=`2c0d0d4…cf13`; ceiling=`archive`; remote=`origin`; fetch/push SHA-256=
  `775bee2f…d16c`; target=`main`; epoch/record/scope hash 待 final allowlist 后冻结。
- Replay activation status: `dormant blocked_on_external_host_capability`。
- Replay host capability: `provider_neutral.stage_state_cas/v1` unavailable。
- Invalidation triggers: scope/non-goal/risk/base/action/endpoint/branch/tip 或 final plan packet 漂移。
- Trust boundary: 当前解释器 site/package installation 受信；interpreter supply-chain 完整性不在本阶段 claim 内。
- Implementation starts only after: internal + A/B plan review final receipts 同 packet、mechanical validator PASS、
  current direct-user confirmation与 v1 implement authority preflight。
