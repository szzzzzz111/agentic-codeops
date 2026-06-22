## Context

当前 `ModelProviderRequest` 只有 query、question type 和 evidence。OpenAI-compatible provider 对所有
任务使用同一 grounded-answer system prompt；Long Task Planner 和 Model Patch AuthoringProvider
只能把 JSON shape 重复拼进普通 query。Provider response 也只有 answer 与字符串 audit summary，
无法表达 finish reason、token usage 或后续 live eval 所需的脱敏调用指标。

该边界同时服务 Grounded Answer、Long Task Planner 和可注入 Patch Authoring provider，因此本
change 按 high risk 处理。默认 provider、公开 API、patch apply、存储和 AgentLoop 路由必须保持不变。

## Goals / Non-Goals

**Goals:**

- 建立向后兼容且由调用方显式描述的 text / JSON object 请求契约。
- 在 HTTP 前确定性拒绝非法 mode、instruction、thinking 配置与 token 上限。
- 让 Provider 只承担通用 JSON object 基础校验，让 Planner/Patch 保留业务 schema 与安全校验。
- 为后续独立 live eval 提供可选、脱敏、无 side channel 的调用 metrics。
- 保持默认测试离线确定性，并用 TDD 锁定请求/响应兼容性与不泄漏边界。

**Non-Goals:**

- 不执行真实 provider smoke/eval，不新增 runner、fixture、rubric、报告或成本计算。
- 不修改默认 `AgentLoop -> PatchManager()` wiring，不生成或 apply 真实 patch。
- 不建设 LLM Gateway、重试、模型路由、价格表、streaming、tool calls 或 JSON Schema 引擎。
- 不实现 answerability classifier，不创建 V24，不修改 `/chat` 顶层 contract。

## Decisions

1. **请求使用小型显式输出契约，不按业务类型猜测。**

   `ModelProviderRequest.output_mode` 默认 `grounded_text`。`json_object` 请求必须携带
   `StructuredOutputInstruction(name, json_example, max_output_tokens)`。Provider 不读取
   `question_type` 来选择 schema。`json_example` 只是输出约束示例，不是完整 JSON Schema。

2. **HTTP 前完成完整基础校验。**

   允许的 mode 只有 `grounded_text` 与 `json_object`。`grounded_text` 禁止携带 structured
   instruction；`json_object` 必须携带 instruction。`name` 必须是 1–64 字符的稳定标识符，以字母
   开头且只允许字母、数字、`_`、`.`、`-`；`json_example` 必须非空、长度不超过 4096 字符、
   可解析且顶层为 object；`max_output_tokens` 必须是 `1..16384` 的整数。
   JSON 深度解析错误同样 fail closed。任何失败都返回稳定 `ProviderRequestValidationError`，HTTP
   client 调用次数必须为零。

3. **JSON 指令只表达一次。**

   Planner 提供 `long_task_plan` instruction，example 包含 `steps` 与允许增强的四个字段，
   `max_output_tokens=2000`。Patch 提供 `patch_proposal` instruction，example 包含 summary、
   target_files、diff、citations，`max_output_tokens=8000`。Planner prompt 只保留 task type、
   memory summary 和 template steps；Patch query 只保留用户修改意图。

4. **Provider 与业务校验分层。**

   Provider 对 `json_object` response 只检查 content 非空、JSON 可解析且顶层为 object，并返回原始
   content。Planner 先检查 provider status；非 success 直接 deterministic fallback，不进入 JSON
   parser。随后 Planner 校验 steps 与模板约束。Patch 保留现有 status preflight，再校验业务字段；
   PatchManager 继续校验 citation、target files、路径和 unified diff。

5. **Thinking 是显式、最小的兼容扩展。**

   未配置 `REPOPILOT_MODEL_THINKING` 时不发送 `thinking`。仅接受 `disabled`，并发送
   `{"type":"disabled"}`；其他值由 provider factory 返回配置错误。直接构造 provider 时也必须在
   HTTP 前验证 thinking mode。

6. **Metrics 是 response-local 数据，不穿透业务结果。**

   `ModelProviderResponse.metrics` 可选持有 `ProviderCallMetrics`：latency、requested/returned
   model、system fingerprint、finish reason、finish reason status，以及 prompt/cache-hit/
   cache-miss/completion/reasoning/total token。字段缺失使用 `None`，整体状态使用
   `available/partial/unavailable`。Grounded Answer、Planner 和 Patch 不把 metrics 复制到业务结果；
   后续 eval 必须使用显式 recording provider wrapper 捕获 response，不得使用全局变量。

7. **Finish reason 在共享兼容层采用有限 fail-closed。**

   `stop` 成功；`length`、`content_filter`、`tool_calls`、`insufficient_system_resource` 返回
   `ProviderFinishReasonError`。字段缺失标记 `unavailable`，未知值标记 `unknown`，二者不破坏
   其他兼容端点的合法 content。JSON 与 text 使用相同规则。usage/metrics 缺失不影响合法业务结果。

8. **Audit 与公开 contract 保持脱敏。**

   audit summary 继续只含 provider、model、status、error class 等安全标量；不得加入 prompt、
   output、API key、reasoning content、system fingerprint 或 token 明细。`/chat` 与
   `/chat.tool_calls` 不新增字段。

## Risks / Trade-offs

- [Risk] `json_example` 不是完整 schema，无法阻止业务字段错误 → Provider 只负责协议基础校验，
  Planner/Patch 的现有业务校验继续 fail closed。
- [Risk] 未知 finish reason 被兼容接受可能掩盖 provider 差异 → metrics 明确记录 `unknown`；
  后续 DeepSeek live gate 可要求精确 `stop`。
- [Risk] response content 会被 Provider 与业务层解析两次 → 保持职责清晰，避免共享 Provider 耦合
  业务 schema；数据规模受现有 context/output 上限约束。
- [Risk] 新字段影响旧测试或自定义 provider → dataclass 使用默认值，`FakeModelProvider` 保持
  grounded text 行为；新增回归覆盖旧构造方式。
- [Risk] metrics 被误写入 audit → 类型不自动序列化进 audit，并增加 Kernel/API/持久化脱敏测试。
