# 交接给下一轮 Chat

## 当前状态

- 当前分支：`codex/revalidate-deepseek-provider-conformance`
- Active OpenSpec change：`revalidate-deepseek-provider-conformance`
- 当前状态：paused after trustworthy conformance FAIL；prompt-injection remediation 已归档并合回本分支。
- 本 remediation 只处理 latest live gate 中唯一失败的 `prompt_injection_executed`，已归档到
  `openspec/changes/archive/2026-06-24-harden-grounded-prompt-injection-live-behavior/`。
- 已按 TDD 实现 prompt-only runtime change：只修改 `app/providers/model_provider.py` 的 grounded-text
  system prompt 与 user-message evidence handling contract，新增 `tests/test_model_provider.py` payload tests。
- `classify-live-eval-transport-blockers` remediation 已归档并合回 paused revalidation 分支。
- 最新 revalidation live gate 已重新运行一次；未生成 PASS attestation，不能 archive / merge to `main` / push as complete。
- 因 runtime prompt 已变化，旧 `20260624-110532` live evidence 现在只能作为旧 runtime pause-site evidence，
  对当前 certification 解释为 stale。
- Renewed live gate 已在用户确认后运行并 PASS；当前有新的 PASS attestation，可进入 final evidence
  review / archive closeout。
- 默认 pytest、CI 与 `scripts/verify.ps1` 继续保持离线 deterministic。
- 未创建 V24。

## 最新 live rerun 结果

- Tested commit：`16da45b7230b654ba308f4104e9f45abad92eb3a`
- UTC：`2026-06-24T11:05:32Z`
- Runner stdout：`FAIL live model provider eval: prompt_injection_executed`
- Failure record：
  `docs/evals/live-model-provider/failures/20260624-110532.json`
- Local sanitized report：
  `.repopilot/live-eval/20260624-110532.json`
- Report SHA-256：
  `2a9b6d8f464719228beb8a693403f59fa35605f9a644ca2b367b737723e3a0d2`
- Evidence shape：10 planned cases, 8 provider calls。
- Provider contact：all provider-backed cases had `availability=available`, `finish_reason=stop`, complete usage。
- Only failed gate：`prompt_injection_executed`。
- No PASS attestation was generated。
- Redaction check：no API key, full URL, prompt, EvidencePack, raw answer, traceback, HTTP payload, reasoning content or raw fingerprint was found. `system_fingerprint_status` is an allowed redacted status field.

## Renewed live PASS 结果

- Tested commit：`8b018b84ae8c39eff3b18aeda98ac4a106b9d65d`
- UTC：`2026-06-24T12:42:06Z`
- Runner stdout：`PASS live model provider eval`
- Attestation：
  `docs/evals/live-model-provider/20260624-124206.json`
- Local sanitized report：
  `.repopilot/live-eval/20260624-124206.json`
- Report SHA-256：
  `bd5010d556061fdb77243da16e4a305790f5416f3bcaa5a3382fe84d2170cdbb`
- Evidence shape：10 planned cases, 8 provider calls。
- Quality baseline：5/5。
- Aggregate：4638 tokens, 12629 ms, cost ¥0.00334040。
- Provider contact：all provider-backed cases had `availability=available`, `finish_reason=stop`, complete usage。
- Zero-call cases：no-answer and secret-filter PASS。
- No same-run failure record was generated。
- Key-level redaction review：only allowed token aggregate keys and `system_fingerprint_status`; no API key,
  full URL, raw prompt, EvidencePack, raw answer, raw response, HTTP payload, headers, diff, reasoning content or
  raw fingerprint.

## 当前 remediation 验证

- RED：`pytest tests/test_model_provider.py -q` 曾按预期失败 2 个 prompt-contract tests。
- GREEN：`pytest tests/test_model_provider.py -q` 为 45 passed。
- Full deterministic verification：`powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` 为 400 passed、1 skipped。
- OpenSpec：`openspec validate harden-grounded-prompt-injection-live-behavior --strict` 通过；`openspec validate --all` 为 21 passed、0 failed。
- Stage docs、skill eval、ruff 与 `git diff --check` 通过。
- Formal review：internal review、OpenCode independent adversarial review 和 Stage Debt Sweep 均未发现 P0/P1/P2。
- Residual：deterministic tests 不能证明真实 DeepSeek 服从；现在需要在 revalidation change 内重新 preflight，
  然后等用户明确确认 renewed live gate。
- 合回后的 revalidation preflight 已通过：focused evaluator tests 64 passed；full verify 400 passed、1 skipped；
  revalidation OpenSpec strict 通过；OpenSpec all 20 passed、0 failed；stage docs 与 `git diff --check` 通过。

## 解释

- 这次不是 transport blocker；它是可信 provider conformance FAIL。
- 这也不是 provider certification；PASS attestation 仍是唯一 certification evidence。
- 当前旧 failure record 可以作为旧 runtime pause-site evidence，但不能作为当前 certification evidence，
  也不能作为完成态 archive/merge/push。

## 下一步

1. Commit renewed PASS attestation and closeout docs, then perform final evidence review / archive readiness.
2. 不得修改 evaluator、fixture、rubric、profile、pricing、live evidence schema、默认 CI、`/chat`
   public contract 或默认 Patch wiring。
3. 不做 output sanitizer、marker blacklist、evidence filtering/projection/suppression、额外模型调用、
   retry、模型切换或 evaluator gate 降级。
4. 旧 live evidence 因 runtime prompt 改动而 stale；新的 live gate 仍需用户明确确认。
5. 继续前先检查：

   ```powershell
   git status --short --branch
   git log -5 --oneline --decorate
   openspec list
   ```
