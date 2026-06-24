## Context

当前 paused revalidation run 的本地报告显示 8 个 provider-attempt 全部为 `availability=unavailable`，
finish reason、returned model 和 usage 均为空。用户从 provider 侧确认未看到请求，因此这次运行并未
公平触达被测 DeepSeek endpoint。

既有 evaluator 的 tracked failure record 只适合表达“完整评测触达 provider 后 provider/system 未通过
conformance gate”。它不应承载“transport/sandbox/proxy 层阻断，provider 未被测到”的语义。

本 change 风险级别为 high：虽然代码改动范围较小，但它影响 live evaluator 的 evidence lifecycle，
决定何时可以生成 tracked evidence，且涉及真实网络执行前的安全边界。

## Goals / Non-Goals

**Goals:**

- 区分 conformance FAIL 与 transport/integrity blocker。
- 从既有 provider audit allowlist 派生 provider-call failure 的脱敏诊断字段，帮助定位 HTTP 前/HTTP/
  response parsing 阶段的问题；不修改 `app/**` provider runtime。
- 阻止 provider-contact 未证实的 run 生成 PASS attestation 或 evaluated-failure record。
- 明确 live gate 必须在 network-capable/escalated shell 执行；普通 sandbox shell 应 fail closed /
  skip before live calls。
- 保持 deterministic tests 与默认 verify 离线。

**Non-Goals:**

- 不修复 DeepSeek、代理、网络或用户本地 shell 配置。
- 不改变 fixture、rubric、质量 baseline、Prompt Injection gate、citation gate 或 provider pricing。
- 不降低任何 hard gate。
- 不 retry、不切换模型、不增加 live case。
- 不回改历史 failure record 或本地 report。
- 不创建 V24。

## Decisions

### 1. Transport blocker 是 evaluation integrity outcome

当 evaluator 无法证明 provider 至少完成一次真实响应时，run 不进入 provider conformance verdict。
典型触发包括：

- 所有应发起 live provider call 的 case 都返回 `availability=unavailable`；
- 所有这些 metrics 均缺少 `finish_reason`、`returned_model` 和完整 usage；
- provider response audit 显示 status 非 success 且错误来自 allowlisted transport/provider-call phase；
- `/chat` subprocess smoke 与 evaluator-local provider 均出现相同 provider-contact failure。

该 outcome 可命名为 `transport_blocked` 或等价 integrity status，但不得落入
`CONFORMANCE_FAILURE_GATES`。

### 2. 脱敏诊断字段必须 allowlist

可保存字段：

- `phase`：例如 `provider_http_request`、`provider_http_status`、`provider_response_parse`、
  `provider_response_validation`。
- `error_class`：Python exception class 或 evaluator-defined class name。
- `status_class`：例如 `http_4xx`、`http_5xx`、`timeout`、`network_error`、`parse_error`、
  `validation_error`。

禁止保存：

- API key、完整 URL、headers、payload、prompt、EvidencePack、raw answer、raw exception message、
  traceback、HTTP body、diff、reasoning content、原始 fingerprint。

### 3. Tracked evidence rules

- PASS：仍只生成 PASS-only attestation。
- Conformance FAIL：只有 provider-contact 已确认且 failure 属于 conformance gates，才可生成
  evaluated-failure record。
- Transport/integrity blocker：不生成 attestation，不生成 evaluated-failure record，只生成本地脱敏
  report；exit code 采用 fail/error 语义并在 stdout 明确输出 blocker 状态与 report path。

### 4. Live execution environment contract

live gate 必须由明确 network-capable/escalated shell 执行。普通 sandbox shell 不允许启动认证 run。
执行前至少需要一个确定性 guard，证明当前 shell 被明确标记为 live-capable；该 guard 不得发送模型请求、
不得打印密钥，不得把默认 verify 改成网络依赖。

具体实现可采用显式环境开关，例如 `REPOPILOT_LIVE_NETWORK_CONFIRMED=1`，由 live wrapper 或人工
network-capable shell 设置。缺失时 runner 在 provider calls 前返回 SKIP/ERROR/transport-blocked
（实现阶段按 tests 固化），并且不生成 tracked evidence。

## Risks / Trade-offs

- [误把真实 provider FAIL 判为 blocker] → blocker 检测要求所有 live provider attempts 均无可用
  response；部分 provider response 可用时仍按 case-level gates 判定。
- [诊断字段泄漏] → 只保存 allowlist code，不保存 message/body/url/payload。
- [默认 verify 误触网] → deterministic tests 使用 fake provider、mock transport 或 fake subprocess。
- [历史证据语义混乱] → 历史 record 不回改；新文档说明它暴露分类缺口，不作为 provider 认证结论。

## Migration Plan

1. 提交 planning/Harness baseline。
2. TDD 增加 transport blocker RED tests。
3. 最小实现分类与脱敏字段。
4. 跑 focused evaluator tests、full deterministic verify、OpenSpec strict/all、stage docs、diff check。
5. 完成 internal review、independent adversarial review、Stage Debt Sweep。
6. Archive 后合入 revalidation 分支；旧 revalidation live evidence 作废，后续需在 network-capable shell
   重新执行认证。

## Open Questions

无。具体 exit code / stdout label 在 implementation 阶段由 tests 固化，但必须满足“不生成 tracked
evidence、不被描述为 conformance FAIL”的核心 contract。
