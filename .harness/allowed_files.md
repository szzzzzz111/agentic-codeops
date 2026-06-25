# 当前 Harness 写入边界

Active OpenSpec change：无。`demo-ready-readme-cli-planning` 已归档到
`openspec/changes/archive/2026-06-25-demo-ready-readme-cli-planning/`。

本阶段 README 门面优化与 Demo-ready Agent CLI 规划已完成并归档；未实现 CLI runtime，未创建 V24。

## 当前允许修改

- archive closeout 文档：
  - `.harness/allowed_files.md`
  - `.harness/review_checklist.md`
  - `docs/PROGRESS.md`
  - `HANDOFF_TO_NEXT_CHAT.md`
- README 门面结果：
  - `README.md`
- archive artifact：
  - `openspec/changes/archive/2026-06-25-demo-ready-readme-cli-planning/**`
- long-term spec sync：
  - `openspec/specs/demo-ready-agent-cli/spec.md`
  - `openspec/specs/harness-development-workflow/spec.md`

## 禁止修改 / 禁止行为

- 不修改 runtime、tests、fixtures、rubric、profile、pricing、live evaluator 或 evidence schema。
- 不修改 `app/**`、`tests/**`、`scripts/run_live_model_eval.ps1`、`scripts/verify.ps1`、默认 CI、`/chat` public contract 或默认 Patch wiring。
- 不新增 CLI runtime、package entrypoint、命令 parser、命令测试或发布配置。
- 不引入网络依赖，不要求 provider API key，不运行 live gate，不 retry，不切换模型，不发送真实 provider 诊断请求。
- 不把 CLI、V24 promotion、commit、merge、push、任意 shell、后台任务、subagents、connectors、always-on assistant 写成已实现。
- 不打印、提交或持久化 API key、完整 URL、prompt、EvidencePack、原始回答、diff、raw exception、traceback、reasoning content、原始 fingerprint 或 HTTP payload。
