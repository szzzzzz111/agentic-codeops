# 当前 Review 清单

Active OpenSpec change：无。`revalidate-deepseek-provider-conformance` 已归档。

## Revalidation closeout evidence

- [x] `harden-grounded-prompt-injection-live-behavior` remediation 已归档并合回 revalidation 分支。
- [x] 旧 `20260624-110532` live evidence 已标记为旧 runtime pause-site evidence，不作为当前 certification。
- [x] Post-remediation deterministic preflight 通过：
  - focused evaluator tests：64 passed
  - full `scripts/verify.ps1`：400 passed, 1 skipped
  - revalidation OpenSpec strict：passed
  - OpenSpec all before archive：20 passed, 0 failed
  - stage docs 与 `git diff --check`：passed
- [x] 用户确认后运行 exactly one renewed live gate；未 retry、未切换模型、未增加 live case、未发送额外诊断请求。
- [x] Renewed live gate PASS：
  - stdout：`PASS live model provider eval`
  - attestation：`docs/evals/live-model-provider/20260624-124206.json`
  - local report：`.repopilot/live-eval/20260624-124206.json`
  - report SHA-256：`bd5010d556061fdb77243da16e4a305790f5416f3bcaa5a3382fe84d2170cdbb`
  - tested commit：`8b018b84ae8c39eff3b18aeda98ac4a106b9d65d`
  - 10 cases / 8 calls / quality 5/5
  - aggregate：4638 tokens、12629 ms、cost ¥0.00334040
- [x] Provider-backed cases all had `availability=available`、`finish_reason=stop`、complete usage。
- [x] No-answer and secret-filter were zero-call PASS cases。
- [x] No same-timestamp failure record was created。
- [x] Key-level redaction review found only allowed token aggregate keys and `system_fingerprint_status`; no API key,
  full URL, raw prompt, EvidencePack, raw answer, raw response, HTTP payload, headers, diff, reasoning content or raw fingerprint。
- [x] PASS attestation 已提交，且是 tested commit/profile/rubric/model 的唯一 provider certification evidence。
- [x] `revalidate-deepseek-provider-conformance` 已归档到
  `openspec/changes/archive/2026-06-24-revalidate-deepseek-provider-conformance/`。
- [x] Archive 后验证通过：
  - full `scripts/verify.ps1`：400 passed, 1 skipped
  - OpenSpec all：19 passed, 0 failed
  - stage docs：passed
  - `git diff --check`：passed
- [x] 未创建 V24。

## Remaining closeout

- [ ] Commit archive closeout.
- [ ] Merge to `main` only with user authorization.
- [ ] Push only with user authorization.
- [ ] Write one final handoff after integration.
