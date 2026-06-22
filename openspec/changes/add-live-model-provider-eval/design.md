## Context

Change 1 已把共享 Model Provider 收敛为向后兼容的 grounded text / JSON object contract，并为
真实端点保留 response-local metrics。当前缺口是：没有可选 live runner 证明默认 `/chat` 启动链、
Grounded Answer、Long Task Planner 和显式注入 Patch Authoring 在真实 OpenAI-compatible
provider 上满足安全与结构契约。

本 change 属于 high risk，因为它涉及真实网络、API key、subprocess、成本报告、临时 patch
持久化和可归档的 live attestation。默认测试和 CI 必须继续无网络、无密钥、可重复。

## Goals / Non-Goals

**Goals:**

- 提供独立 Python evaluator 与薄 PowerShell 入口。
- 使用固定 fixture/rubric 覆盖代码定位、实现解释、配置、测试、无答案、模糊问题和 prompt
  injection。
- 验证默认 `/chat` 启动 wiring、Grounded Answer、Long Task Planner 与显式注入 Patch Authoring。
- 记录 citation validity、groundedness baseline、拒答、泄漏、latency、token 和成本。
- 缺少 live 配置时明确 SKIP；只有真实 hard gates PASS 并生成 tracked attestation 后才能归档。

**Non-Goals:**

- 不修改 Model Provider runtime、system prompt、默认 Patch wiring、API contract、默认 CI 或
  `scripts/verify.ps1`。
- 不新增 retry、streaming、gateway、provider routing、answerability classifier 或 V24。
- 不将真实模型质量 baseline 设为初始硬门。
- 不保存 prompt、Evidence Pack、原始回答、原始 diff、reasoning content 或 API key。

## Decisions

### 1. 通用 evaluator core + DeepSeek profile

Evaluator core 负责 case 执行、gate、报告和 attestation；provider-specific profile 负责环境约束、
finish reason、usage 完整性和价格。首个 profile 固定：

- provider: `openai_compatible`
- base URL: `https://api.deepseek.com`
- model: `deepseek-v4-flash`
- thinking: `disabled`
- pricing effective date: `2026-06-22`
- cache hit / cache miss / output: `0.02 / 1 / 2` CNY per million tokens

价格只存在于版本化 profile，不进入 runtime。Reasoning tokens 已包含在 completion tokens 内，不重复
计费。

### 2. 固定调用预算与失败语义

Runner 最多执行 8 次真实调用，每个 case 最多一次，无 retry。单次 provider timeout 固定 30 秒，
API subprocess timeout 120 秒，整轮 deadline 300 秒。缺少任一 live 环境变量时输出 SKIP 并返回
0；profile mismatch 或 hard gate failure 返回 1；runner 内部错误返回 2。

### 3. 默认启动链必须通过全新 subprocess 验证

API smoke helper 在环境已由父进程显式设置后才 import `app.main`。它从模块级 `ChatService` 获取
默认构造的 `AgentLoop`，先断言 Grounded Answer provider 是
`OpenAICompatibleModelProvider`，然后只在该 subprocess 内用 recording wrapper 包装同一实例并
通过 `TestClient` 调 `/chat`。Helper 只向父进程返回脱敏 response contract、rubric facts 和
provider metrics，不返回 prompt 或原始 HTTP payload。

### 4. 组件 smoke 与副作用边界

- Grounded Answer cases 使用固定 EvidencePack；无答案 case 使用空 EvidencePack 和 counting
  provider，证明零调用。
- Planner 显式注入 recording real provider 并启用 provider-assisted planning。
- Patch 在临时 synthetic repo 中把 `ModelPatchAuthoringProvider` 显式注入 `PatchManager`；
  允许创建临时 pending proposal 以覆盖 citation/path/diff/store 校验，但绝不 apply，并在 case
  结束后删除临时目录。
- Secret filtering 使用 synthetic repo、真实 retrieval/EvidencePack 边界和 `httpx.MockTransport`，
  不消耗真实调用。

### 5. Gate 与质量 baseline 分离

硬门包括 finish reason、完整 usage、citation、Planner/Patch schema、无答案零调用、prompt
injection、secret filtering、report redaction、调用预算和 timeout。质量 baseline 仅对代码定位、
实现解释、配置、测试和模糊问题计算 required-facts `x/5`，不阻断本阶段归档。

### 6. 两层报告与归档证据

每轮运行写 `.repopilot/live-eval/<timestamp>.json` 本地脱敏报告。只有整轮 PASS 才额外写
`docs/evals/live-model-provider/<timestamp>.json` tracked attestation。Attestation 记录被测
commit、时间、profile/rubric 版本、模型、调用数、质量分数、聚合 latency/token/cost 和本地报告
SHA-256，不记录原始 fingerprint 或模型内容。

Live gate 只能在 tracked working tree 干净时运行。Attestation 后只允许 closeout 文档变化；若
runtime、tests、fixture、rubric、profile 或 evaluator 变化，旧 live 结果、attestation 和 review
证据全部作废。

### 7. Live 失败触发独立 remediation

如果 live gate 暴露 runtime 缺陷，eval change 停止修改并在 Harness 记录 paused exception。
随后临时创建独立 remediation change；remediation 完成 TDD、review、archive、merge/push 后再
恢复 eval change，并基于新 `main` 重跑 deterministic verification、formal review 和完整 live
gate。不得在 eval change 内顺手修改 runtime。

## Risks / Trade-offs

- [真实模型输出漂移] → 安全和结构使用硬门，语义质量仅记录版本化 baseline。
- [API key 或模型内容泄漏] → 报告采用 allowlist schema，并用 canary 测试本地报告与 attestation。
- [subprocess smoke 误测手工 wiring] → helper 必须先断言 import-time 默认 provider 类型，再包装。
- [Patch case 产生状态] → 只在临时 repo 创建 pending DB，finally 清理，绝不 apply。
- [价格变化] → profile 携带 effective date；后续价格更新必须修改 profile、测试并重跑 attestation。
- [无密钥无法完成阶段] → deterministic 实现可以完成，但 change 保持 active，HANDOFF 明确 blocker。
