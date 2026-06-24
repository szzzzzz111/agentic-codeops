# 当前 Review 清单

Active change：`revalidate-deepseek-provider-conformance`。风险级别：high。当前状态：
paused after trustworthy conformance FAIL。

## 已合回 remediation

- [x] `classify-live-eval-transport-blockers` 已归档并合回当前 revalidation 分支。
- [x] Transport/sandbox/provider-contact blocker 不再生成 PASS attestation 或 evaluated-failure record。
- [x] 任一 required live provider attempt 缺少可评价 provider contact 时，整轮 outcome 为 `transport_blocked`。
- [x] 缺少 `REPOPILOT_LIVE_NETWORK_CONFIRMED=1` 时 runner 在 git/provider 调用前 SKIP/0。
- [x] Local report diagnostics 只允许 `phase`、`error_class`、`status_class`，且 `error_class` 已做 safe code token 收敛。
- [x] `build_evaluated_failure_record()` 已增加 provider-contact 完整性防线。
- [x] Remediation deterministic evidence：focused evaluator tests `64 passed`；full verify `398 passed, 1 skipped`；OpenSpec all `21 passed, 0 failed`。
- [x] Remediation review：internal review、independent adversarial review 和 Stage Debt Sweep 已完成；无剩余 P0/P1 blocker。

## 最新 live rerun evidence

- [x] 用户确认后，在 network-capable/escalated shell 中运行 exactly one live gate。
- [x] `.env.live` 只检查 key presence，不打印 value。
- [x] Process environment 显式设置 `REPOPILOT_LIVE_NETWORK_CONFIRMED=1`。
- [x] Live 前 tracked worktree clean；tested commit 为 `16da45b7230b654ba308f4104e9f45abad92eb3a`。
- [x] Runner stdout 为 `FAIL live model provider eval: prompt_injection_executed`，不是 PASS/SKIP/BLOCKED/ERROR。
- [x] Failure record 存在：
  `docs/evals/live-model-provider/failures/20260624-110532.json`。
- [x] Local sanitized report 存在：
  `.repopilot/live-eval/20260624-110532.json`。
- [x] Report SHA-256 与 failure record 一致：
  `2a9b6d8f464719228beb8a693403f59fa35605f9a644ca2b367b737723e3a0d2`。
- [x] Evidence shape：10 planned cases，8 provider calls。
- [x] Provider contact：所有 provider-backed cases 均为 `availability=available`、`finish_reason=stop`、usage complete。
- [x] Failed gates：仅 `prompt_injection_executed`。
- [x] PASS attestation 未生成。
- [x] Redaction：未发现 API key、完整 URL、prompt、EvidencePack、raw answer、traceback、HTTP payload、reasoning content 或 raw fingerprint；`system_fingerprint_status` 是允许的脱敏状态字段。

## 当前结论

- [x] 旧 `20260624-013028` artifact 仍解释为旧 contract 下 provider-contact-unverified transport/integrity blocker。
- [x] 新 `20260624-110532` artifact 是可信 provider conformance FAIL pause-site evidence。
- [x] PASS attestation 仍是唯一 provider certification evidence。
- [x] 当前 change 不得 archive、merge to `main` 或 push as complete。
- [x] 不在当前 revalidation change 内修 runtime/evaluator/tests/profile/rubric。
- [x] 若要修复 `prompt_injection_executed`，必须新建独立 OpenSpec remediation；若要 FAIL-baseline closeout，也必须正式 reshape contract。
- [x] 默认 verify/CI 仍离线 deterministic。
- [x] 未创建 V24。
