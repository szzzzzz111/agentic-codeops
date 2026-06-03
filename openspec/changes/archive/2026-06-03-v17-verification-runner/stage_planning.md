# V17 Verification Runner Stage Planning

## Stage

- Stage: `V17 Verification Runner`
- Proposed branch: `feature/v17-verification-runner`
- Capability owner:
  - New capability: `verification-runner`
  - Modified capabilities: `agent-loop-tool-execution`, `chat-api`, `harness-development-workflow`
- Previous completed stage: `V16 Safe Patch Authoring`

## Intent

- Problem:
  - RepoPilot V16 可以在用户明确确认后受控 apply patch，但 runtime 仍不能执行任何验证命令。用户需要离开 `/chat` 手动运行 `pytest`、`ruff check .` 或 `scripts/verify.ps1`，导致 patch 后验证闭环仍断开。
- Why now:
  - V17 是 V18 Patch + Verify Loop 的前置小切片。只有先把验证命令执行收口到白名单、权限、审批、输出截断和脱敏边界内，后续才可以安全串联 patch apply 和 verify。
- User-visible outcome:
  - 用户通过明确验证请求触发受控验证，系统通过现有 `/chat.answer` 返回验证状态、命令标签、退出码、耗时和截断后的输出摘要；`/chat` 顶层 contract 不变。

## Scope

- In scope:
  - 新增明确 verification intent / command parser。
  - 新增白名单验证命令 registry，初始支持 `pytest`、`ruff check .` 和 `scripts/verify.ps1` 的稳定标签。
  - 新增受控 `verification_run` 工具，经过 `ToolRegistry -> PermissionPolicy -> ApprovalGate -> ToolExecutor` 执行。
  - 新增本地 subprocess runner，限制 cwd 在 `repo_path` 内、固定 timeout、截断 stdout/stderr，并对公开 answer / trace 摘要脱敏。
  - `/chat.answer` 返回验证摘要，`tool_calls` 只保留安全摘要。
- Out of scope:
  - 不自动在 patch apply 后运行验证。
  - 不根据失败结果自动生成修复 patch。
  - 不持久化 verification result、attempt id 或审计日志。
  - 不创建 branch/worktree，不 commit，不 push。
  - 不开放任意 shell 命令、命令参数拼接、后台任务或真实 SandboxRunner。
- API contract:
  - `/chat` 顶层响应字段保持 `trace_id`、`answer`、`related_files`、`tool_calls`，不新增必需或可选字段。
- Runtime dependency changes:
  - 无。使用 Python stdlib `subprocess` / `time` / `pathlib` 等能力；默认验证不依赖网络、API key 或真实模型输出。

## Boundaries

- Harness boundaries preserved:
  - Verification intent 在 Patch command / Patch intent 之后、capability-status / repo_search 之前处理。
  - `verification_run` 必须注册为 `read_only=False`、`risk=write` 或等价高风险等级、`requires_approval=True`，因为验证命令可能创建缓存、覆盖测试输出或运行项目脚本。
  - `PermissionPolicy` 仍只产出 `allow`、`deny`、`ask`；明确验证请求通过归一化 `ToolInvocationContext` 进入 `ask -> ApprovalGate pass`。
  - 实际执行只通过 `ToolExecutor.verification_run(...)`，API handler 和 AgentLoop 不直接调用 subprocess。
- Security and audit:
  - 只允许白名单命令标签，不接受任意命令文本、额外 shell 参数、管道、重定向或环境变量注入。
  - runner 必须使用 argv list 执行，不通过 shell 字符串执行。
  - cwd 必须限制在 resolved `repo_path` 内。
  - 公开输出必须截断并脱敏，不泄露本机绝对路径、完整 stdout/stderr、环境变量、API key、DB 路径或完整 trace。
  - 超时、命令缺失、非零退出码和 runner 异常都返回结构化失败摘要，不抛出到 `/chat` handler。
- Retrieval stance:
  - `grep-first, RAG-assisted`；V17 不改变 repo retrieval、rewrite/rerank、Evidence Pack 或 grounded answer 语义。

## Tests

- Unit tests:
  - `tests/test_verification_runner.py` 覆盖 parser、白名单 registry、repo path 边界、timeout、输出截断、路径脱敏和非零退出码摘要。
- API / contract tests:
  - `tests/test_agent_harness_kernel.py` 覆盖 Verification intent 优先级、`verification_run` 权限/审批上下文、非白名单命令拒绝、执行摘要进入 `tool_calls`。
  - `tests/test_chat_api.py` 覆盖 `/chat` 顶层字段不变、明确验证请求不触发 repo_search、不泄露完整输出或本机绝对路径。
- Docs / route-map tests:
  - `scripts/verify.ps1` 继续作为默认验证入口。
  - 阶段完成前运行 `openspec validate v17-verification-runner`、`openspec validate --all`、默认 verify 和 `git diff --check`。

## Docs And Harness

- Allowed files to update:
  - `.harness/allowed_files.md`
  - `.harness/review_checklist.md`
  - `openspec/changes/v17-verification-runner/**`
  - `app/verification/**`
  - `app/harness/kernel.py`
  - `app/tools/tool_executor.py`
  - `tests/test_verification_runner.py`
  - `tests/test_agent_harness_kernel.py`
  - `tests/test_chat_api.py`
  - `README.md`
  - `docs/ARCHITECTURE.md`
  - `docs/PROGRESS.md`
  - `docs/FEATURE_LIST.json`
  - `HANDOFF_TO_NEXT_CHAT.md`
- Review checklist additions:
  - 检查验证 intent 不误吞 memory、long task、assistant status 或 patch。
  - 检查白名单命令不可被用户参数扩展为任意 shell。
  - 检查 `verification_run` 经过权限、审批和 ToolExecutor。
  - 检查 stdout/stderr 截断、脱敏和非零退出码摘要。
  - 检查 V18+ Patch + Verify Loop、持久审计和 worktree 未被实现。
- Durable docs to update:
  - `README.md`
  - `docs/ARCHITECTURE.md`
  - `docs/PROGRESS.md`
  - `docs/FEATURE_LIST.json`
  - `HANDOFF_TO_NEXT_CHAT.md`

## Human Decisions

- Decision needed:
  - V17 白名单命令是否只开放三个固定标签：`pytest`、`ruff`、`verify`，其中 `verify` 映射到 `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`。
- Default recommendation:
  - 推荐只开放这三个固定标签，不支持用户附加参数；更细粒度的 test selection 留到后续单独阶段，避免 V17 变成任意 shell 入口。
