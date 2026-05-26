# 当前 Review 清单

当前活跃阶段：V11 `v11-grounded-answer-model-provider-boundary`。

## Plan Review

- [ ] V11 change 包含 proposal、design、tasks，以及 `grounded-answer-model-provider`、`agent-loop-tool-execution`、`chat-api` spec delta。
- [ ] `.harness/allowed_files.md` 明确允许修改 `pyproject.toml`，且说明 `httpx` 是本阶段显式批准的运行时依赖。
- [ ] 计划明确默认 provider 为 deterministic fake provider，真实 OpenAI-compatible provider 必须显式配置。
- [ ] 计划明确 `/chat` 顶层响应 contract 不新增必需字段。

## Grounded Answer Contract

- [ ] ModelProvider 输入只包含 original query、question type、预算内 included evidence snippets 和相对路径 citation metadata。
- [ ] 无 included evidence 时不调用真实 provider，并返回保守 fallback。
- [ ] citation 格式固定为 `relative/path.py:start-end`，且必须匹配 provided evidence。
- [ ] 无合法 citation、越界 citation、provider error、timeout 或 invalid response 均降级。
- [ ] provider audit 只记录 provider name、model、status、latency/error class、fallback reason。
- [ ] provider audit 不记录完整 prompt、完整模型输出、完整 Evidence Pack、API key、本机绝对路径或内部 trace 细节。
- [ ] `tool_calls` 不包含 prompt、evidence_pack、API key、完整模型输出或 provider audit。

## Scope Guard

- [ ] 不把小米 MiMo/Mino 写死为运行时主链路；只作为 OpenAI-compatible provider 配置。
- [ ] 不实现 query rewrite、rerank、memory、context compression、SandboxRunner、skill execution、多 agent 或 ReAct。
- [ ] 默认验证不依赖真实网络、真实 key 或真实模型输出。
- [ ] `agent-loop-tool-execution` 长期 spec 已同步 V11 provider boundary 例外，避免和旧“不使用真实 LLM”口径冲突。
- [ ] README、ARCHITECTURE、PROGRESS、FEATURE_LIST 和 HANDOFF 均反映 V11 边界，且不把 V12+ 能力写成已实现。

## Verification

- [ ] `openspec validate --all` 通过。
- [ ] `openspec validate v11-grounded-answer-model-provider-boundary` 通过。
- [ ] `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` 通过，或说明无法运行的原因。
- [ ] `git diff --check` 通过。
- [ ] `git status --short --branch` 和 `git diff --name-only` 未显示 V11 allowed files 外文件。
- [ ] 内部 self-review、外部 review、提交和 archive 均已完成后，才能把 V11 视为阶段完成。
