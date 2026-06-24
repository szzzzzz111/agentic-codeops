## Why

Change 2 已证明 live evaluator readiness，但最终 DeepSeek run 的 8 个 provider 调用均记录为
`availability=unavailable`，因此没有生成 PASS attestation。随后进行的最小脱敏诊断已确认同一
配置下 DeepSeek endpoint 与 RepoPilot Provider 均可成功返回 `finish_reason=stop` 和完整 usage，
需要在不修改 evaluator/runtime 的前提下重新执行完整 conformance gate。

## What Changes

- 在新的 clean committed planning/closeout baseline 上复用现有
  `evals.live_model_provider.runner`，重新执行一次完整 DeepSeek 8-call live gate。
- PASS 时提交既有 schema 的 tracked attestation，并复核本地报告 hash、commit、UTC、
  profile/rubric、调用预算、hard gates、latency/token/cost。
- FAIL 时保留既有退出码和 evidence contract；有效 conformance FAIL 可提交 runner
  exclusive-create 的 tracked failure record 作为当前 revalidation 分支的暂停现场证据，但不得把
  provider 描述为已认证，也不得 archive、merge 到 `main` 或 push 为完成态，除非后续正式
  reshape 契约。
- 不修改 Provider runtime、evaluator、fixtures、rubric、profile、默认 Patch wiring、`/chat`
  contract、默认 CI、`scripts/verify.ps1` 或长期 capability specs。
- 不创建或规划 V24。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `live-model-provider-eval`：明确已归档 evaluator 可通过独立 revalidation change 在新的 clean
  commit 上重新评测并生成 PASS attestation；历史 FAIL evidence 保持不可变。

## Impact

- OpenSpec:
  `openspec/changes/revalidate-deepseek-provider-conformance/**`
- Process:
  `.harness/allowed_files.md`、`.harness/review_checklist.md`
- Evidence on PASS:
  `docs/evals/live-model-provider/<timestamp>.json`
- Evidence on valid conformance FAIL:
  `docs/evals/live-model-provider/failures/<timestamp>.json`，仅作为暂停现场证据，不是 provider
  certification evidence
- Docs:
  `docs/PROGRESS.md`、`HANDOFF_TO_NEXT_CHAT.md`
- Runtime/tests/API/default verification: 无变更。
