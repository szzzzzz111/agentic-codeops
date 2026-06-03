## Context

当前主链路是：

```text
API -> ChatService(trace_id) -> CodeAgent -> AgentLoop
  -> MemoryManager(STM/PREF/LTM command/read audit)
  -> LongTaskManager(command/status/step audit)
  -> AssistantControlSurface(read-only status)
  -> PatchManager(proposal/apply confirmation)
  -> QueryUnderstanding/SearchPlan -> QueryRewriteProvider
  -> ToolRegistry -> PermissionPolicy -> ApprovalGate
  -> ToolExecutor(repo_rag / patch_apply) -> HybridRepoRetriever -> Reranker -> EvidencePack/ContextBudget
     -> GroundedAnswerGenerator -> ModelProvider
```

V17 在 Patch command / Patch intent 之后插入 Verification intent。验证请求只接受明确命令标签，不接受任意 shell 文本。执行仍通过权限、审批和 ToolExecutor 边界，避免 API handler、AgentLoop 或具体 parser 直接运行 subprocess。

## Goals / Non-Goals

**Goals:**

- 通过明确验证请求运行白名单验证命令。
- 初始只支持固定标签 `pytest`、`ruff` 和 `verify`。
- 验证执行必须经过 `ToolRegistry -> PermissionPolicy -> ApprovalGate -> ToolExecutor`。
- runner 使用 argv list，不通过 shell 字符串执行。
- 返回 exit code、status、duration 和截断脱敏输出摘要。
- 保持 `/chat` 顶层响应字段不变。

**Non-Goals:**

- 不自动在 patch apply 后运行验证。
- 不根据验证失败自动生成修复 patch。
- 不持久化 verification result、attempt id 或审计日志。
- 不创建 branch/worktree，不 commit，不 push。
- 不开放任意 shell、用户自定义参数、管道、重定向或环境变量注入。
- 不实现 Persistent Audit / Recovery、Patch + Verify Loop、Worktree Isolation、真实 SandboxRunner 或后台任务。

## Decisions

### Decision 1: Verification 前置顺序固定

AgentLoop 前置处理顺序为：

1. Memory command。
2. Long Task command。
3. Assistant Control Surface。
4. Patch command / Patch intent。
5. Verification intent。
6. capability-status。
7. repo_search / chat_only。

这样验证请求不会被 capability-status 或 repo_search 抢先处理；V16 patch 语义仍保留既有优先级。

### Decision 2: 只开放固定命令标签

V17 初始白名单只包含：

- `pytest`: 映射为当前 Python 环境中的 `pytest`。
- `ruff`: 映射为 `ruff check .`。
- `verify`: 映射为 `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`。

用户可以用中文或英文触发，例如 `运行验证`、`运行 pytest`、`run pytest`、`run ruff`、`run verify`。V17 不支持附加参数，例如 `pytest tests/foo.py` 或 `ruff --fix`。

### Decision 3: verification_run 是需审批工具

`verification_run` 注册为 `read_only=False`、`risk="write"`、`requires_approval=True`。虽然验证通常不是业务写入，但命令可能创建 `.pytest_cache`、`__pycache__` 或执行项目脚本，因此必须走高风险审批路径。

`PermissionPolicy` 仍只返回 `allow`、`deny` 或 `ask`。明确验证请求由 parser 生成归一化 `ToolInvocationContext`；context 必须只携带 `tool_name=verification_run`、`intent=verification_run`、`command_label`、`confirmed=true` 和 `scope_valid=true`。context 有效且 `command_label` 属于白名单时，`PermissionPolicy` MAY 返回 `ask`，`ApprovalGate` MAY 在同一 context 下通过。普通非 low 风险工具仍按既有策略拒绝。

### Decision 4: runner 只执行 argv list

runner 接收 registry 产出的 argv list 和 timeout，不接收用户原始命令字符串。实现 MUST 不使用 `shell=True`，MUST 不拼接 shell 字符串，MUST 不透传用户附加参数、管道、重定向或环境变量赋值。

工作目录 MUST 是 resolved `repo_path`，且必须确认在目标 repo 内。repo_path 不存在、不可解析或不是目录时返回安全失败摘要。

### Decision 5: 输出公开前统一压缩和脱敏

runner 保存并返回摘要字段：

- `command_label`
- `status`
- `exit_code`
- `duration_ms`
- `stdout_excerpt`
- `stderr_excerpt`
- `timed_out`
- `truncated`

`stdout_excerpt` 和 `stderr_excerpt` 各最多 4000 字符。`/chat.answer` 中验证输出摘要总计最多 6000 字符，并明确标记 `truncated=true/false`。公开 `answer` 和 `tool_calls` MUST NOT 包含完整输出、本机绝对路径、DB 路径、环境变量、API key 或内部 trace。

脱敏规则固定为：

- resolved `repo_path` 替换为 `<repo>`。
- Windows / POSIX 本机绝对路径替换为 `<local-path>`。
- `.repopilot/...` 替换为 `.repopilot/<redacted>`。
- `API_KEY=...`、`TOKEN=...`、`SECRET=...`、`PASSWORD=...` 整段替换为 `<redacted-secret>`。

`tool_calls` 不放 stdout/stderr，只放 `tool_name`、`command_label`、`status`、`exit_code`、`duration_ms`、`timed_out`、`truncated` 和 `result_count`。

## Error Behavior

- 非白名单命令：拒绝执行，返回支持的命令标签。
- repo_path 不存在或不可用：拒绝执行，不泄露本机路径。
- 命令缺失：返回 `unavailable` 或 `failed` 摘要，不抛出到 API 层。
- timeout：终止进程，返回 `timed_out=true` 和截断输出。
- 非零退出码：返回 `failed` 摘要，保留截断 stdout/stderr，`/chat` 请求本身仍成功。

## Rollback

V17 不修改 `/chat` schema。若 Verification Runner 需要回退，可移除 AgentLoop 中 Verification 分支、`verification_run` 工具规格和 `app/verification/**`；Patch、Memory、Long Task、Assistant Control Surface 和 repo RAG 主链路不受影响。
