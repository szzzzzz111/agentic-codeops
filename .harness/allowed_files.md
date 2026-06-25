# 当前 Harness 写入边界

当前无 active OpenSpec change。最近归档 change：`polish-demo-cli-capability-surface`，
归档目录为 `openspec/changes/archive/2026-06-25-polish-demo-cli-capability-surface/`。

本阶段为 V24 CLI Capability Surface / Demo-ready Product Surface，并同时修正计划级 review
流程。原 Verified Patch Promotion 顺延为 V25/backlog，本阶段不得实现 promotion。

## 当前允许修改

- CLI runtime：
  - `app/cli.py`
- CLI tests：
  - `tests/test_cli.py`
- Archived OpenSpec artifacts：
  - `openspec/changes/archive/2026-06-25-polish-demo-cli-capability-surface/**`
- Long-term specs touched by this change：
  - `openspec/specs/demo-ready-agent-cli/spec.md`
  - `openspec/specs/harness-development-workflow/spec.md`
- Harness 边界：
  - `.harness/allowed_files.md`
  - `.harness/review_checklist.md`
- Codex workflow skills：
  - `.codex/skills/openspec-stage-planner/**`
  - `.codex/skills/repo-stage-workflow/**`
  - `.codex/skills/repo-stage-review-loop/**`
  - `.codex/skills/external-review-triage/**`
- OpenCode workflow entry：
  - `.opencode/skills/**`
- Durable docs：
  - `README.md`
  - `docs/ARCHITECTURE.md`
  - `docs/FEATURE_LIST.json`
  - `docs/PROGRESS.md`
  - `docs/AGENT_RULES.md`
  - `HANDOFF_TO_NEXT_CHAT.md`

## 禁止修改 / 禁止行为

- 不修改 `/chat` public contract、FastAPI route schema、默认 CI、`scripts/verify.ps1` 或
  `scripts/run_live_model_eval.ps1`。
- 不修改 AgentLoop、ToolExecutor、VerificationRunner、Audit、Worktree runtime、provider runtime、
  live eval profile、fixtures、rubric、pricing、evidence schema 或默认 Patch wiring。
- 不新增网络依赖，不要求 provider API key，不运行 live gate，不发送真实 provider 诊断请求。
- 不实现 Verified Patch Promotion、commit automation、merge automation、push automation、branch
  management、PR creation、后台任务、runtime subagents、connectors、notifications 或 always-on
  assistant。
- 不接受任意 shell、用户附加 argv、管道、重定向、环境变量注入或额外 verification 参数。
- 不打印、提交或持久化 API key、完整 URL、prompt、EvidencePack、原始回答、完整 diff、raw
  exception、traceback、reasoning content、原始 fingerprint 或 HTTP payload。
