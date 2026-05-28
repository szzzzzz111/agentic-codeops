# 当前 Review 清单

当前活跃阶段：暂无；V12 `v12-query-rewrite-rerank` 已实现、review、提交并归档。

## V11 Archive Closeout

- [x] V11 change 包含 proposal、design、tasks，以及 `grounded-answer-model-provider`、`agent-loop-tool-execution`、`chat-api` 和 `repo-query-understanding-rag` spec delta。
- [x] `httpx>=0.27.0` 已放入 `[project].dependencies`，作为可选 OpenAI-compatible provider 的运行时依赖。
- [x] 默认 provider 为 deterministic fake provider，真实 OpenAI-compatible provider 必须显式配置。
- [x] `/chat` 顶层响应 contract 不新增必需字段。
- [x] citation、fallback、provider audit 和脱敏边界已有测试覆盖。
- [x] `openspec validate --all` 通过。
- [x] `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` 通过。
- [x] `git diff --check` 通过。
- [x] 内部 self-review 和外部 review 均已处理。
- [x] V11 active change 已归档到 `openspec/changes/archive/2026-05-26-v11-grounded-answer-model-provider-boundary/`。

## V13 Next Stage Gate

- [ ] 使用 `.harness/templates/stage_planning.md` 先做 V13 阶段级规划，明确 capability、scope、non-goals、依赖和 human decision。
- [ ] 开始 V13 前先创建 Memory 的 OpenSpec proposal、design、tasks 和 spec delta。
- [ ] V13 必须区分 STM、LTM 和 PREF，并定义 memory audit、脱敏和 `/chat` contract 边界。
- [ ] V13 开工前同步 `.harness/allowed_files.md` 和本 checklist，明确允许修改的代码、测试、docs 和 OpenSpec artifacts。
- [ ] V13 plan review 通过前，不修改运行时代码或测试。

## V12 Implementation Review

- [x] OpenSpec change 包含 proposal、design、tasks，以及 `repo-query-understanding-rag` / `agent-loop-tool-execution` spec delta。
- [x] deterministic rewrite 永远保留 `original` variant，额外 variants 最多 3 条，id 和模板顺序稳定。
- [x] rewrite 不改变 route、权限决策或整体 `question_type`。
- [x] rerank 只作用于 retrieval results 层，Evidence Pack budget/summary 和 grounded answer citation validation 语义不变。
- [x] 每个 rewrite variant 都执行 hybrid retrieval；不得因 original variant 为空跳过 rewrite-only variants。
- [x] 原始 query 的 path/symbol/exact token 直接命中在容量允许时不被 variant-only 结果挤掉。
- [x] symbol/path 查询保持 lexical anchor，embedding-only 弱命中不得绕过 grep-first baseline。
- [x] rewrite/rerank audit 只进入内部 trace，不进入 `/chat` 顶层字段或完整 `tool_calls`。
- [x] capability status 区分 deterministic rewrite/rerank 已实现和真实 LLM rewrite/rerank 未实现。
- [x] 默认验证不依赖真实网络、API key 或真实模型输出。

## V12 Archive Closeout Gate

- [x] 使用 `.harness/templates/stage_closeout.md` 更新 PROGRESS、HANDOFF 和 harness 状态。
- [x] V12 implementation commit 已创建：`aaddad2 Add V12 query rewrite rerank`。
- [x] V12 review follow-up commit 已创建：`4553b11 Fix V12 review follow-ups`。
- [x] V12 active change 已归档到 `openspec/changes/archive/2026-05-27-v12-query-rewrite-rerank/`。
- [x] 长期 specs 已在 archive 前同步。
- [x] `openspec list` 显示 no active changes。
- [x] `openspec validate --all` 通过。
- [x] `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` 通过。
- [x] `git diff --check` 通过。
- [x] `powershell -ExecutionPolicy Bypass -File scripts/check_stage_docs.ps1` 通过。
- [x] `powershell -ExecutionPolicy Bypass -File scripts/check_stage_closeout.ps1` 通过。
- [x] `README.md`、`docs/PROGRESS.md`、`HANDOFF_TO_NEXT_CHAT.md`、`.harness/allowed_files.md` 和 `.harness/review_checklist.md` 不再把已归档阶段描述为 active。
- [x] 下一阶段只写成 planned / next，不写成 implemented。
