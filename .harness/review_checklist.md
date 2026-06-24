# 当前 Review 清单

Active change：`harden-grounded-prompt-injection-live-behavior`。风险级别：high。

## Planning gate

- [x] 已确认当前分支为独立 remediation 分支，不直接在 paused revalidation change 内修 runtime。
- [x] OpenSpec proposal/design/spec/tasks 已同步，且只修改 `grounded-answer-model-provider` capability。
- [x] Writable scope 与 `.harness/allowed_files.md` 一致。
- [x] Planning self-review 已检查 proposal、design、spec、tasks、implementation plan 和 Harness 边界无矛盾。
- [x] `openspec validate harden-grounded-prompt-injection-live-behavior --strict` 通过。
- [x] `openspec validate --all` 通过。
- [x] `powershell -ExecutionPolicy Bypass -File scripts/check_stage_docs.ps1` 通过。
- [x] `git diff --check` 通过。

## TDD evidence

- [x] RED test 覆盖 grounded-text prompt 缺少明确 repository-fact extraction/data-boundary contract。
- [x] RED test 覆盖 hostile raw evidence 仍在 payload 中，而 attack target 不进入 system prompt blacklist。
- [x] RED test 覆盖同名合法 repository identifier 例外。
- [x] Regression test 覆盖 `json_object` prompt assembly 不变。
- [x] GREEN implementation 只修改 grounded-text prompt construction。
- [x] 未加入 output sanitizer、marker blacklist、evidence filtering/projection/suppression 或额外 provider call。

## Verification

- [x] `pytest tests/test_model_provider.py -q` 通过。
- [x] 相邻回归测试按实际 touched paths 运行并通过。
- [x] `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` 通过。
- [x] `openspec validate harden-grounded-prompt-injection-live-behavior --strict` 通过。
- [x] `openspec validate --all` 通过。
- [x] `powershell -ExecutionPolicy Bypass -File scripts/check_stage_docs.ps1` 通过。
- [x] `git diff --check` 通过。

## Formal review

- [x] Internal review 覆盖 prompt contract、no-filter boundary、citation footer、JSON mode isolation、paused revalidation semantics。
  - Result：未发现 P0/P1/P2。确认只改 `grounded_text` prompt construction；raw evidence 仍经 JSON envelope 进入 user prompt；attack target 仅存在于 test evidence/user prompt，不进入 system prompt blacklist；`json_object` branch 未接入新文案；evaluator/gate/evidence schema 未修改。
- [x] Independent adversarial review 覆盖 prompt-injection bypass、false safety、marker blacklist、over-constraint、network isolation 和 evaluator gate weakening。
  - Result：OpenCode read-only adversarial review 未发现 P0/P1/P2。Residual：deterministic tests 不能证明真实模型服从，需后续 revalidation live gate；`policies` 依赖 directed-at-assistant qualifier，若模型忽略 qualifier 可能过度保守，作为 live 行为观察即可。
- [x] Stage Debt Sweep 覆盖 changed provider prompt/tests 及直接 grounded-answer citation fallback dependencies。
  - Inspected：`app/providers/model_provider.py`、`tests/test_model_provider.py`、`app/answering/grounded_answer.py`、`evals/live_model_provider/cases.py` prompt-injection raw response gate、`.harness/*`、`docs/PROGRESS.md`、`HANDOFF_TO_NEXT_CHAT.md`。
  - Result：未发现新增阻断债务；未发现 output sanitizer、marker blacklist、evidence filtering/projection、evaluator weakening、默认网络依赖或 stale evidence 完成态表述。
- [x] 所有 P0/P1/P2 finding 已关闭并重新验证。

## Closeout / revalidation handoff

- [ ] Remediation 归档前未运行真实 live gate。
- [ ] Archive 后如 runtime/tests 再变化，重新执行 verification 和 formal review。
- [ ] 合回 `codex/revalidate-deepseek-provider-conformance` 后，旧 live evidence 标记为 stale，因为 runtime prompt 已变化。
- [ ] renewed live gate 只能在用户明确确认后按 revalidation contract 执行：clean tree、exactly one full gate、no retry、no model switch、no extra diagnostics。
- [ ] 未创建 V24。
