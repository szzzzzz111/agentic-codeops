## Why

RepoPilot 已经具备 repo-local RAG、Evidence Pack、受控 Patch、Verification Runner、Worktree
隔离和 persistent audit 等核心能力，但 GitHub README 首屏仍像阶段流水账，不利于简历和面试官快速理解项目价值。

同时，后续 demo 需要一个薄 CLI 入口把现有 `/chat`/AgentLoop 能力串成可录屏路径：代码定位、grounded
answer、pending patch proposal、明确确认 apply、verify、audit/status。当前先规划该 CLI，不直接实现命令入口，
也不创建 V24。

## What Changes

- 优化 README 顶部“面试官版”项目介绍，把 RepoPilot 表述为面向代码仓库理解、受控 Patch 和验证闭环的本地 Coding Agent Harness。
- README 首屏突出当前已实现的核心能力：Agent Loop、repo-local hybrid RAG、Evidence Pack / citation、受控 Patch + Verify、Worktree 隔离、SQLite audit、live model eval。
- README 增加简洁架构图或流程图，并把内部阶段记录下沉到详细文档入口之后。
- 创建 Demo-ready Agent CLI 的 OpenSpec 规划，明确 CLI 只是现有能力薄封装，不重写 AgentLoop，不修改 `/chat` contract，不改变默认 CI，不引入网络依赖。
- 明确候选命令、复用边界、demo 路径、已实现能力与仅规划能力的区分。
- 本 change 不实现 CLI runtime，不修改 `app/**`、tests、provider runtime、live eval profile、默认 Patch wiring 或 V24 promotion。

## Capabilities

### New Capabilities

- `demo-ready-agent-cli`: planned thin local CLI wrapper over existing RepoPilot capabilities.

### Modified Capabilities

- `harness-development-workflow`: require README facade and CLI planning to stay separate from runtime implementation until explicit confirmation.

## Impact

- Code: none in this planning stage.
- Tests: no runtime tests in this planning stage; validation is OpenSpec structure plus deterministic repo checks.
- Docs: `README.md`, this OpenSpec change, `.harness/allowed_files.md`, `.harness/review_checklist.md`, and only durable status docs whose owned facts change.
- Dependencies: no new dependency and no network requirement.
