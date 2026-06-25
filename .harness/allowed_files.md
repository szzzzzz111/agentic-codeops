# 当前 Harness 写入边界

当前无 active OpenSpec change。最近归档 change：`add-demo-ready-agent-cli`，归档目录为 `openspec/changes/archive/2026-06-25-add-demo-ready-agent-cli/`。

本阶段已完成 Demo-ready Agent CLI 的本地薄入口实现；剩余工作仅限 archive 后文档收口、验证、提交、合并和推送，不再扩 runtime 能力。

## 当前允许修改

- CLI runtime：
  - `app/cli.py`
- Package script metadata：
  - `pyproject.toml`
- CLI tests：
  - `tests/test_cli.py`
- Archived OpenSpec artifacts：
  - `openspec/changes/archive/2026-06-25-add-demo-ready-agent-cli/**`
- Long-term specs touched by this change：
  - `openspec/specs/demo-ready-agent-cli/spec.md`
  - `openspec/specs/harness-development-workflow/spec.md`
- Harness 边界：
  - `.harness/allowed_files.md`
  - `.harness/review_checklist.md`
- Durable docs：
  - `README.md`
  - `docs/FEATURE_LIST.json`
  - `docs/PROGRESS.md`
  - `HANDOFF_TO_NEXT_CHAT.md`

## 禁止修改 / 禁止行为

- 不修改 `/chat` public contract、FastAPI route schema、默认 CI、`scripts/verify.ps1` 或 `scripts/run_live_model_eval.ps1`。
- 不修改 provider runtime、live eval profile、fixtures、rubric、pricing、evidence schema 或默认 Patch wiring。
- 不新增网络依赖，不要求 provider API key，不运行 live gate，不发送真实 provider 诊断请求。
- 不实现 V24 promotion、commit automation、merge automation、push automation、branch management、PR creation、后台任务、subagents、connectors、notifications 或 always-on assistant。
- 不接受任意 shell、用户附加 argv、管道、重定向、环境变量注入或额外 verification 参数。
- 不打印、提交或持久化 API key、完整 URL、prompt、EvidencePack、原始回答、完整 diff、raw exception、traceback、reasoning content、原始 fingerprint 或 HTTP payload。
