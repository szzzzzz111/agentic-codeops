## Why

`revalidate-deepseek-provider-conformance` 执行了一次真实 live gate，但 8 个 provider-attempt 全部记录为
`availability=unavailable`，且用户从 provider 侧确认没有看到请求。该结果说明被测 provider 很可能
没有被公平触达，不能被解释为 provider conformance FAIL。

现有 live evaluator 会把 transport/provider-call failure 折叠成普通 metrics gate 失败，并在符合
conformance failure allowlist 时生成 evaluated-failure record。这会让“没有测到对象”与“对象未通过
测试”在 tracked evidence 语义上混淆。

## What Changes

- 增强 live evaluator 的 provider-contact / transport failure 分类。
- 在脱敏 report 中为 provider-call failure 记录 allowlist 字段，例如 `phase`、`error_class`、
  `status_class`，不保存 URL、payload、prompt、raw exception、API key 或完整 HTTP body。
- 当任一 required live provider attempt 属于 transport/sandbox/provider-contact blocker，或缺少可评价
  provider contact 时，整轮归类为 `transport_blocked` / evaluation integrity blocker。单个 confirmed
  provider response 只能证明该 case 可评价，不能证明整轮 eval 可评价。
- `transport_blocked` 不生成 PASS attestation，也不生成 evaluated-failure record；只保留本地脱敏
  report，并固定输出 `BLOCKED live model provider eval: transport_blocked`、退出码 1。
- live gate 执行环境 contract 明确要求 network-capable/escalated shell；普通 sandbox shell 不得启动
  live gate 去消耗认证机会。缺少显式 live-network confirmation 时固定输出
  `SKIP live model provider eval: live_network_not_confirmed`、退出码 0。

## Capabilities

### New Capabilities

无产品 runtime 能力新增。

### Modified Capabilities

- `live-model-provider-eval`：区分 provider conformance failure 与 transport/integrity blocker，并避免
  将 provider-contact 未证实的运行写成 tracked provider conformance evidence。

## Impact

- OpenSpec:
  `openspec/changes/classify-live-eval-transport-blockers/**`
- Evaluator/runtime under change:
  `evals/live_model_provider/**`、`scripts/run_live_model_eval.ps1`
- Tests:
  `tests/test_live_model_provider_eval.py`
- Process/Harness:
  `.harness/allowed_files.md`、`.harness/review_checklist.md`
- Docs:
  `docs/PROGRESS.md`、`HANDOFF_TO_NEXT_CHAT.md`
- Default CI / `scripts/verify.ps1`:
  保持离线 deterministic，不依赖网络、密钥或真实模型输出。
