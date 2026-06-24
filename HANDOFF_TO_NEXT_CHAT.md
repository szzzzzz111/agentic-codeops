# 交接给下一轮 Chat

## 当前状态

- 当前分支：`codex/revalidate-deepseek-provider-conformance`
- Active OpenSpec change：`revalidate-deepseek-provider-conformance`
- 当前状态：paused，等待用户决定是否在 network-capable shell 中重新运行 DeepSeek provider conformance gate。
- `classify-live-eval-transport-blockers` remediation 已归档并合回当前分支。
- 默认 pytest、CI 与 `scripts/verify.ps1` 继续保持离线 deterministic。
- 未创建 V24。

## 已完成

- Remediation 已实现并归档：
  - 缺少 `REPOPILOT_LIVE_NETWORK_CONFIRMED=1` 时，在 git/provider 读取前返回
    `SKIP live model provider eval: live_network_not_confirmed` / exit 0。
  - 任一 required live provider attempt 出现 transport/sandbox/provider-contact blocker 时，整轮返回
    `BLOCKED live model provider eval: transport_blocked` / exit 1。
  - `transport_blocked` 只允许本地脱敏 report，不生成 PASS attestation，不生成 evaluated-failure record。
  - evaluated-failure record builder 本身也校验所有 required provider cases 具备可评价 provider contact。
  - local report diagnostics 只允许 `phase`、`error_class`、`status_class`；`error_class` 已收敛为安全 code token。
- Remediation evidence：
  - Focused evaluator tests：`64 passed`
  - Full deterministic verify：`398 passed, 1 skipped`
  - OpenSpec strict/all：`21 passed, 0 failed`
  - Stage docs check passed；`git diff --check` clean（仅 CRLF normalization warnings）。
  - Internal review、independent adversarial review、Stage Debt Sweep 已完成，无 P0/P1 blocker。
- 旧 revalidation live artifact
  `docs/evals/live-model-provider/failures/20260624-013028.json` 现在应解释为旧 contract 下的
  provider-contact-unverified transport/integrity blocker 现场证据，不是 DeepSeek provider certification，也不是可靠 provider conformance FAIL 结论。

## 下一步

1. 先检查实时状态：

   ```powershell
   git status --short --branch
   git log -5 --oneline --decorate
   openspec list
   ```

2. 若用户要继续重新认证，必须先明确确认当前 shell 是授权的 network-capable execution。
3. 运行 live gate 前必须确保：
   - clean tracked working tree；
   - 五个必需 provider env key 已存在且不打印 value；
   - `REPOPILOT_LIVE_NETWORK_CONFIRMED=1` 已设置；
   - 不 retry、不切换模型、不增加 live case、不发送额外诊断请求。
4. 若 live gate PASS，按 `revalidate-deepseek-provider-conformance` 的 PASS outcome handling 生成/复核 attestation。
5. 若 live gate BLOCKED/FAIL/SKIP/ERROR，按当前 OpenSpec outcome semantics 处理；不要在 revalidation change 内修改 runtime/evaluator/tests/profile/rubric。
