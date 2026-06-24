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

更严格地说，confirmed provider response 只能证明该 case 可评价，不能证明整轮 eval 可评价。
evaluated-failure record 只有在所有 required live provider attempts 都具备可评价 provider contact，
且失败来自 conformance gates 时才允许生成。任一 required live attempt 属于
transport/sandbox/provider-contact blocker，则整轮 outcome 为 `transport_blocked` / integrity blocker，
不得落入 `CONFORMANCE_FAILURE_GATES`，也不得生成 tracked conformance evidence。

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
- Conformance FAIL：只有所有 required live provider attempts 的 provider-contact 都已确认，且 failure
  属于 conformance gates，才可生成 evaluated-failure record。
- Transport/integrity blocker：不生成 attestation，不生成 evaluated-failure record，只生成本地脱敏
  report；stdout 固定为 `BLOCKED live model provider eval: transport_blocked`，exit code 固定为 1，
  并输出本地 report path。
- Missing network confirmation：在 provider calls 前停止，stdout 固定为
  `SKIP live model provider eval: live_network_not_confirmed`，exit code 固定为 0，不生成 tracked
  evidence。可不生成 report。
- Internal runner bug：继续输出 `ERROR live model provider eval: <ErrorClass>`，exit code 固定为 2，
  不生成 tracked evidence。

### 4. Live execution environment contract

live gate 必须由操作者明确声明/授权的 network-capable/escalated shell 执行。普通 sandbox shell 不允许
启动认证 run。执行前至少需要一个确定性 guard，确认操作者已声明当前 shell 应为 live-capable；该 guard
不得发送模型请求、不得打印密钥，不得把默认 verify 改成网络依赖。

具体实现可采用显式环境开关，例如 `REPOPILOT_LIVE_NETWORK_CONFIRMED=1`，由 live wrapper 或人工
network-capable shell 设置。该变量只表示显式授权/声明，不证明技术上真的通网；声明后仍未触达 provider
时，由 `transport_blocked` 捕获。缺失时 runner 在 provider calls 前返回
`SKIP live model provider eval: live_network_not_confirmed` / exit 0，并且不生成 tracked evidence。

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

无。Exit code 和 stdout label 已在本 design 中固定。
