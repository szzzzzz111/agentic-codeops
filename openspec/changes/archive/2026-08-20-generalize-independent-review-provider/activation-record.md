# Independent Review Gate Activation Record

## Authority And Timing

- Authority：本 change 实现开始前已经存在的 manual RepoPilot plan-review contract，以及用户对本项目实现工作的确认。
- Activation scope：`scripts/validate_independent_review.py` 的机械一致性 gate、fixed receipt-set path 和
  host/activation required external checks。
- Activation point：2026-08-20，在 receipt template、validator、workflow/spec/skills wiring、首轮独立实现
  review findings 修复和新增负样本完成之后；不适用于本 change 已经发生的 pre-implementation plan review。
- Earliest governed event：本 change 的 remediation final implementation review；后续适用的 plan/final independent
  review 继续受此合同约束。

## Activation Preconditions Observed

- Receipt template 已包含 activation authority record、external gate checks、review history、structured findings 和
  gate verdict。
- Validator 已覆盖 fixed relative receipt path、safe stage id、canonical project-relative artifacts、artifact/packet
  hashes、slot/reviewer identity consistency、declared context/visibility、content-hashed original receipt lineage、
  contradictory/open conclusions 和 structured errors/nonzero exit。
- Focused workflow/validator test suite：`32 passed`，包含同一 reviewer remediation re-review 后新增的
  incomplete original receipt、partial finding closure、missing original artifact fields 反例，以及原首轮
  `no_findings` slot 使用空 `closed_finding_ids` 刷新最终 baseline 的正样本。
- Changed Python files Ruff：PASS。
- OpenSpec strict active-change validation：PASS。
- `openspec validate --all`：`23 passed, 0 failed`。
- `git diff --check`：PASS。

## Claim Ceiling

Repository validator 只证明 `mechanical_consistency_only` 并固定输出 `gate_ready=false`。它不能证明 receipt 字段
确实来自宿主 dispatch，也不能证明本记录的真实时间顺序。因此每次 gate 仍必须由宿主控制器核对 native dispatch
metadata，并由 pre-change process authority 核对 activation sequence。只写入 `host_tool_metadata` 或 `active` 字样
不能关闭 gate。

本记录不追溯声明新 validator 曾经验证本 change 的 plan review，也不授权 archive、commit、merge 或 push。
