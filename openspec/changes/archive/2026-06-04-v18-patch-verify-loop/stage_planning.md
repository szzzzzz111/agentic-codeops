# V18 Stage Planning

## Stage

- Stage: `V18 Patch + Verify Loop`
- Proposed branch: `feature/v18-patch-verify-loop`
- Capability owner:
  - New capability: `patch-verify-loop`
  - Modified capabilities: `safe-patch-authoring`, `verification-runner`, `agent-loop-tool-execution`, `chat-api`, `harness-development-workflow`
- Previous completed stage: `V17 Verification Runner`

## Intent

- Problem:
  - V16 可以确认 apply pending patch，V17 可以独立运行白名单验证，但用户还不能用一个明确请求完成 apply 后验证的受控闭环。
- Why now:
  - V18 是 V16/V17 之后的最小纵向切片，能够把受控写入和受控验证串联起来，同时不提前进入 V19 持久审计或 V20 worktree 隔离。
- User-visible outcome:
  - 用户可发送明确组合确认，例如 `确认 patch patch_xxx 并运行验证`，系统 apply 成功后运行白名单验证，并通过现有 `/chat.answer` 返回组合摘要。

## Scope

- In scope:
  - 明确组合确认解析、apply 成功后的白名单 verification run、组合响应摘要、内部 trace 摘要和相关测试/文档。
- Out of scope:
  - 持久化 verification result、attempt history、recovery、worktree、任意 shell、targeted pytest、自动生成后续 patch、commit/push、subagent 调度。
- API contract:
  - `/chat` 顶层响应保持不变：`trace_id`、`answer`、`related_files`、`tool_calls`。
- Runtime dependency changes:
  - None.

## Boundaries

- Harness boundaries preserved:
  - 组合流程必须复用 `PatchManager`、`ToolExecutor.patch_apply`、`PermissionPolicy`、`ApprovalGate` 和 `ToolExecutor.verification_run`。
- Security and audit:
  - 组合请求必须同时解析出 `patch_id` 和 verification label；缺失、半解析、非法 label、附加参数或 shell 语法时整体拒绝，且不得 apply。
  - verification 必须使用独立 `ToolInvocationContext`，只在 patch apply 成功后生成。
  - 公开响应不得泄露完整 diff、完整 stdout/stderr、完整 internal trace、本机绝对路径、DB 路径、Evidence Pack 或 provider output。
- Retrieval stance:
  - `grep-first, RAG-assisted`; V18 不改变 repo retrieval 链路。

## Tests

- Unit tests:
  - `tests/test_patch_authoring.py` 覆盖组合 parser、旧 apply-only 行为和半解析拒绝。
  - `tests/test_verification_runner.py` 覆盖组合 label 白名单和 unsafe syntax 拒绝。
- API / contract tests:
  - `tests/test_agent_harness_kernel.py` 覆盖组合优先级、执行顺序、独立 verification context 和失败门。
  - `tests/test_chat_api.py` 覆盖 `/chat` contract、tool_calls 摘要和脱敏。
- Docs / route-map tests:
  - `openspec validate v18-patch-verify-loop`
  - `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`

## Docs And Harness

- Allowed files to update:
  - `app/harness/kernel.py`
  - `app/patching/`
  - `app/verification/`
  - `tests/`
  - `openspec/changes/v18-patch-verify-loop/`
  - `.harness/allowed_files.md`
  - `.harness/review_checklist.md`
  - `README.md`
  - `docs/ARCHITECTURE.md`
  - `docs/PROGRESS.md`
  - `docs/FEATURE_LIST.json`
  - `HANDOFF_TO_NEXT_CHAT.md`
- Review checklist additions:
  - 组合确认优先级、半解析拒绝、非法 label 整体拒绝、独立 verification context、失败门、输出脱敏和 non-goal gates。
- Durable docs to update:
  - `README.md`
  - `docs/ARCHITECTURE.md`
  - `docs/PROGRESS.md`
  - `docs/FEATURE_LIST.json`
  - `HANDOFF_TO_NEXT_CHAT.md`

## Human Decisions

- Decision needed:
  - V18 是否按 Patch + Verify Loop，而不是重做 Verification Runner。
- Default recommendation:
  - 已确认按 Patch + Verify Loop 实施；组合确认必须显式给出验证标签或“验证”别名，不自动补默认值。
