## Why

RepoPilot 的 GitHub README 已经把 Demo-ready CLI 标为规划中，但仓库当前没有 `repopilot`
命令。为了支撑简历项目演示，需要一个最薄的本地 CLI，把已有 `/chat` 背后的 AgentLoop 能力串成
可录屏路径，而不是重写 runtime 或新增第二套 API。

## What Changes

- 新增本地 `repopilot` console entrypoint，作为现有 `ChatService -> CodeAgent -> AgentLoop`
  的薄入口。
- 初始命令收敛为：`ask`、`patch`、`patch confirm`、`verify`、`status`、`audit latest`。
- CLI 使用 stdlib `argparse`，默认 `repo_path=.`、`user_id=cli`、`session_id=cli`，并允许显式覆盖。
- CLI 只把命令转换成现有 `/chat` message 语义，返回 `answer`、`related_files` 和 `tool_calls`
  的安全摘要；不新增 `/chat` 字段，不改变 FastAPI contract。
- `verify` 只接受现有固定标签 `pytest`、`ruff`、`verify`；不接受任意 shell、附加 argv、管道、
  重定向或环境变量注入。
- CLI 不启用网络依赖，不修改 live eval profile，不接入真实 patch provider，不实现 V24 promotion、
  commit、merge、push 或 background/subagent/connectors。

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `demo-ready-agent-cli`: implement the planned local thin entrypoint.
- `harness-development-workflow`: require CLI implementation to stay inside existing runtime boundaries.

## Impact

- Code: targeted CLI entrypoint and package script metadata only.
- Tests: new focused CLI tests, plus existing AgentLoop/API/verification regression where needed.
- Docs: OpenSpec artifacts, harness boundaries, README CLI section, PROGRESS, HANDOFF, and FEATURE_LIST only if owned facts change.
- Dependencies: no new runtime dependency.
