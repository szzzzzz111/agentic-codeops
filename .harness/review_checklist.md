# 当前 Review 清单

当前活跃阶段：无。V11 `v11-grounded-answer-model-provider-boundary` 已完成实现、review、提交并归档。

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

## Next Stage Gate

- [ ] 开始 V12 前先创建 Query Rewrite + Rerank 的 OpenSpec proposal、design、tasks 和 spec delta。
- [ ] V12 必须继承 grep-first, RAG-assisted 检索立场：rewrite/rerank 服务于 lexical/path/symbol baseline，不默认切换到向量库优先。
- [ ] V12 开工前同步 `.harness/allowed_files.md` 和本 checklist，明确允许修改的代码、测试、docs 和 OpenSpec artifacts。
- [ ] V12 plan review 通过前，不修改运行时代码或测试。

## Reusable Archive Closeout Gate

- [ ] 使用 `.harness/templates/stage_closeout.md` 更新 PROGRESS、HANDOFF 和 harness 状态。
- [ ] `openspec list` 显示 no active changes，或明确记录仍有 active change 的原因。
- [ ] `openspec validate --all` 通过。
- [ ] `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` 通过。
- [ ] `git diff --check` 通过。
- [ ] `powershell -ExecutionPolicy Bypass -File scripts/check_stage_docs.ps1` 通过。
- [ ] `README.md`、`docs/PROGRESS.md`、`HANDOFF_TO_NEXT_CHAT.md`、`.harness/allowed_files.md` 和 `.harness/review_checklist.md` 不再把已归档阶段描述为 active。
- [ ] 下一阶段只写成 planned / next，不写成 implemented。
