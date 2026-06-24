# 当前 Review 清单

Active change：`revalidate-deepseek-provider-conformance`。风险级别：high。

## Scope

- [x] 仅重新执行既有 DeepSeek live conformance gate，不修改 runtime/evaluator/tests。
- [x] 历史 evaluated-failure record 保持不可变。
- [x] PASS-only attestation contract、hard gates 与退出码保持不变。
- [x] PASS attestation 是唯一认证证据；有效 FAIL record 仅为当前分支暂停现场证据。
- [x] `.env.live` wrapper 只做同进程 key presence，不打印值、不额外诊断。
- [x] 默认 verify/CI 保持离线 deterministic。
- [x] 不创建 V24。

## Pre-Live Verification

- [x] Planning/OpenSpec/Harness artifacts 完成 internal review；独立 plan review session `ses_10b1cdbe4ffeA5IpfyFePB2W44` 无剩余 P0-P2。
- [x] Review P1/P2 follow-up closed：FAIL record 写入边界已纳入 Harness，`.env.live` live wrapper 已明确。
- [x] Focused evaluator tests 通过：`pytest tests/test_live_model_provider_eval.py -q` = 57 passed。
- [x] Full deterministic verify 通过：`scripts/verify.ps1` = 391 passed, 1 skipped；ruff、stage docs、skill eval 通过。
- [x] OpenSpec strict/all、stage docs checks 与 `git diff --check` 通过：20/20 OpenSpec items passed，stage docs valid，diff check clean。
- [x] Live 配置五个必需 key 完整，值未打印；仅执行 key presence check，未发送 provider/model 诊断请求。
- [x] Final pre-live commit 已提交且 tracked tree clean。

## Formal Review

- Gate marker: `formal_review_evidence_gate`
- Policy marker: `continuous_authorization_does_not_replace_formal_review`
- Timing marker: `formal_review_after_final_runtime_tests`
- [x] Internal review covers commit identity、no retry、evidence exclusivity and historical evidence immutability；无阻断 finding。
- [x] Independent adversarial review covers stale evidence、false certification、redaction and network isolation；focused `opencode run` returned `No P0/P1/P2 blockers`，且未读取 `.env.live`。
- [x] `manual_stage_debt_sweep_completed`：仅检查 live runner/entrypoint 的直接依赖和 closeout docs，不扩展 runtime debt；无本 change 需处理 finding。
- [x] `formal_review_findings_closed`。

## Live And Closeout

- [ ] 用户明确确认后执行一次完整 8-call live gate。
- [ ] Outcome 由 stdout 与 evidence path 共同判定：PASS/SKIP 不能只看 exit 0，FAIL 不能只看 exit 1。
- [ ] PASS 时只有 attestation；有效 FAIL 时只允许当前分支暂停现场 failure record，不生成 attestation、不 archive/merge/push；exit 1 无 failure-record path 时视为 integrity-blocked evidence。
- [ ] Final evidence review verifies report hash、tested commit、UTC、profile/model、rubric、10 cases、8 calls、metrics、cost and redaction.
- [ ] Archive/merge/push 仅在 PASS attestation 与所有 review findings 关闭后执行。
- [ ] Archive sync 保留长期 spec 的全部 6 个 requirement，并加入独立 revalidation scenario。
- [x] `future_stage_only`：V24 不在本 change 内创建。
