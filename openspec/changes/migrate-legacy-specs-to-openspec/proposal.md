## Why

RepoPilot 已经接入项目级 OpenSpec，但已验收的 V1-V4 规格仍保存在旧的 `specs/00x-*` 目录中。将这些规格迁移为 OpenSpec capabilities，可以让后续 Codex、OpenCode 和 Copilot 工作时使用同一个规格入口，同时不丢失已有阶段历史。

## What Changes

- 新增 OpenSpec 长期规格，用于承接 V1-V4 已验收能力。
- 在迁移 review 期间保留旧 `specs/00x-*`，避免丢失历史验收上下文。
- OpenSpec specs 通过 review 并归档后，再单独决定是否删除、移动或保留旧 `specs/00x-*`。
- 本迁移不改变运行时代码、API、测试或产品能力。

## Capabilities

### New Capabilities

- `chat-api`：Agent 服务入口、请求/响应契约和 trace 响应结构。
- `safe-repository-file-tools`：安全只读仓库文件工具，以及路径和敏感文件边界。
- `agent-loop-tool-execution`：最小确定性 Agent Loop 和统一 `ToolExecutor` 搜索边界。
- `skill-metadata-loader`：DeepAgents 风格 `.agents/skills/*/SKILL.md` 技能元数据发现。
- `harness-development-workflow`：仓库开发流程、允许文件、review checklist、验证、handoff 和 OpenSpec 使用边界。

### Modified Capabilities

- 无。

## Impact

- 新增 OpenSpec change 文件，后续归档后会生成 `openspec/specs/` 下的长期规格。
- 当前不修改 `app/`、`tests/`、API schema、运行时工具或 `/chat` 行为。
- 是否删除旧 `specs/00x-*` 留到后续独立 cleanup change 决策。
