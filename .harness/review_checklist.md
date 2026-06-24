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

- [ ] RED test 覆盖 grounded-text prompt 缺少明确 repository-fact extraction/data-boundary contract。
- [ ] RED test 覆盖 hostile raw evidence 仍在 payload 中，而 attack target 不进入 system prompt blacklist。
- [ ] RED test 覆盖同名合法 repository identifier 例外。
- [ ] Regression test 覆盖 `json_object` prompt assembly 不变。
- [ ] GREEN implementation 只修改 grounded-text prompt construction。
- [ ] 未加入 output sanitizer、marker blacklist、evidence filtering/projection/suppression 或额外 provider call。

## Verification

- [ ] `pytest tests/test_model_provider.py -q` 通过。
- [ ] 相邻回归测试按实际 touched paths 运行并通过。
- [ ] `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` 通过。
- [ ] `openspec validate harden-grounded-prompt-injection-live-behavior --strict` 通过。
- [ ] `openspec validate --all` 通过。
- [ ] `powershell -ExecutionPolicy Bypass -File scripts/check_stage_docs.ps1` 通过。
- [ ] `git diff --check` 通过。

## Formal review

- [ ] Internal review 覆盖 prompt contract、no-filter boundary、citation footer、JSON mode isolation、paused revalidation semantics。
- [ ] Independent adversarial review 覆盖 prompt-injection bypass、false safety、marker blacklist、over-constraint、network isolation 和 evaluator gate weakening。
- [ ] Stage Debt Sweep 覆盖 changed provider prompt/tests 及直接 grounded-answer citation fallback dependencies。
- [ ] 所有 P0/P1/P2 finding 已关闭并重新验证。

## Closeout / revalidation handoff

- [ ] Remediation 归档前未运行真实 live gate。
- [ ] Archive 后如 runtime/tests 再变化，重新执行 verification 和 formal review。
- [ ] 合回 `codex/revalidate-deepseek-provider-conformance` 后，旧 live evidence 标记为 stale，因为 runtime prompt 已变化。
- [ ] renewed live gate 只能在用户明确确认后按 revalidation contract 执行：clean tree、exactly one full gate、no retry、no model switch、no extra diagnostics。
- [ ] 未创建 V24。
