# 当前 Review 清单

Active OpenSpec change：无。`demo-ready-readme-cli-planning` 已归档。

## Planning / README / CLI scope

- [x] 已读取 AGENTS.md、必读项目文档、`openspec/README.md`、当前 harness 文件和 handoff。
- [x] 已确认当前分支为 `main`，初始工作树干净，最近提交为 revalidation handoff，起始 `openspec list` 无 active change。
- [x] 已判断风险级别为 `low`：只做 README/规划文档，不改 runtime、tests、provider、CI 或 `/chat` contract。
- [x] 已创建非 V24 OpenSpec change：`demo-ready-readme-cli-planning`。
- [x] README 首屏已改为“面试官版”项目门面：一句话定位、核心能力、执行闭环、快速开始、文档入口。
- [x] README 核心能力只列当前已实现能力，不把 Roadmap 写成已实现。
- [x] 内部阶段记录已下沉，不让首屏像开发流水账。
- [x] CLI 明确只是规划中的薄入口，不声明 `repopilot` 命令已实现。
- [x] CLI 规划复用现有 AgentLoop / ToolExecutor / VerificationRunner / Audit / Worktree 能力。
- [x] 不重写 AgentLoop，不修改 `/chat` contract，不改变默认 CI，不引入网络依赖。
- [x] 不接受任意 shell、用户附加 argv、管道、重定向、环境变量注入或额外 verification 参数。
- [x] Patch proposal 与 apply confirmation 保持分离，不做隐式 apply。
- [x] 不修改 live eval profile、provider runtime、默认 Patch wiring，不创建或实现 V24。

## Archive closeout

- [x] `openspec archive demo-ready-readme-cli-planning -y` 已同步 specs 并归档到
  `openspec/changes/archive/2026-06-25-demo-ready-readme-cli-planning/`。
- [x] Long-term spec sync：
  - `openspec/specs/demo-ready-agent-cli/spec.md` 新增 3 条 requirements。
  - `openspec/specs/harness-development-workflow/spec.md` 新增 1 条 requirement。
- [x] 新增 `demo-ready-agent-cli` long-term spec 的 Purpose 已替换 archive 默认 `TBD`。
- [x] `openspec list` 当前为 No active changes found。

## Verification

- [x] Focused regression：`pytest tests/test_chat_api.py::test_docs_keep_stage_route_map_consistent -q`，1 passed。
- [x] Archive 前 `openspec validate demo-ready-readme-cli-planning --strict` 通过。
- [x] Archive 后 `openspec validate --all` 通过。
- [x] Archive 后 `git diff --check` 通过；仅有 CRLF normalization warning。
- [x] Archive 后 full `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` 通过：pytest 400 passed、1 skipped；ruff passed；stage docs scan passed；skill eval structure scan passed。
