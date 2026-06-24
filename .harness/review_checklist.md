# 当前 Review 清单

Active change：`revalidate-deepseek-provider-conformance`。风险级别：high。当前状态：
paused after trustworthy conformance FAIL；`harden-grounded-prompt-injection-live-behavior`
remediation 已归档并合回本分支。

## 已归档 remediation：Grounded prompt injection live behavior

- [x] Remediation change 已归档到
  `openspec/changes/archive/2026-06-24-harden-grounded-prompt-injection-live-behavior/`。
- [x] Remediation 已 fast-forward 合回 `codex/revalidate-deepseek-provider-conformance`。
- [x] Long-term spec `openspec/specs/grounded-answer-model-provider/spec.md` 已完成 archive sync。
- [x] Runtime change 仅限 `app/providers/model_provider.py` 的 `grounded_text` system prompt 与 user-message
  evidence handling contract。
- [x] Tests 仅新增/调整 `tests/test_model_provider.py` payload assertions。
- [x] 未修改 evaluator、fixture、rubric、profile、pricing、live evidence schema、`scripts/verify.ps1`、默认 CI、
  `/chat` public contract 或默认 Patch wiring。
- [x] 未加入 output sanitizer、marker blacklist、response rewriting、evidence filtering/projection/suppression、
  extra provider call、retry 或模型切换。
- [x] RED/GREEN：`pytest tests/test_model_provider.py -q` 曾按预期失败 2 个 prompt-contract tests，最终
  45 passed。
- [x] Full deterministic verification：`powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` 为
  400 passed、1 skipped。
- [x] OpenSpec strict/all：21 passed、0 failed；stage docs、skill eval、ruff 和 `git diff --check` 通过。
- [x] Internal review、OpenCode independent adversarial review 和 Stage Debt Sweep 均未发现 P0/P1/P2。

## Revalidation 恢复边界

- [x] `docs/evals/live-model-provider/failures/20260624-110532.json` 仍是旧 runtime 下的可信 conformance FAIL pause-site evidence，不是 provider certification。
- [x] Remediation 合回后，旧 live evidence 对 certification 解释已标记为 stale，因为 runtime prompt 已变化。
- [x] 重新运行 deterministic preflight。
  - Evidence：focused evaluator tests `64 passed`；full `scripts/verify.ps1` `400 passed, 1 skipped`；
    `openspec validate revalidate-deepseek-provider-conformance --strict` 通过；`openspec validate --all`
    `20 passed, 0 failed`；stage docs 与 `git diff --check` 通过。
- [x] 用户明确确认后，才能按 revalidation contract 运行 exactly one renewed live gate。
- [x] Renewed live gate 仍必须 no retry、no model switch、no extra diagnostics。
- [x] PASS attestation 仍是唯一 provider certification evidence。
  - Evidence：stdout `PASS live model provider eval`；attestation
    `docs/evals/live-model-provider/20260624-124206.json`；local report
    `.repopilot/live-eval/20260624-124206.json`。
  - Report SHA-256 matched attestation:
    `bd5010d556061fdb77243da16e4a305790f5416f3bcaa5a3382fe84d2170cdbb`。
  - Tested commit：`8b018b84ae8c39eff3b18aeda98ac4a106b9d65d`；10 cases；8 calls；
    quality baseline 5/5；aggregate 4638 tokens、12629 ms、cost ¥0.00334040。
  - Provider-backed cases all had `availability=available`、`finish_reason=stop`、complete usage；
    no-answer and secret-filter were zero-call PASS cases。
  - No same-timestamp failure record was created.
  - Key-level redaction review found only allowed token aggregate keys and `system_fingerprint_status`; no API key,
    full URL, raw prompt, EvidencePack, raw answer, raw response, HTTP payload, headers, diff, reasoning content or raw fingerprint.
- [ ] 未创建 V24。
