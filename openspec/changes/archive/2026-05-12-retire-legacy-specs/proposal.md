## Why

旧 `specs/00x-*` 已经迁移并归档到长期 `openspec/specs/`。继续保留两套主规格入口会让后续 Agent 和 reviewer 不确定该以哪套规格为准。

## What Changes

- 退役旧 `specs/00x-*` 阶段规格目录。
- 更新入口文档，使长期规格入口指向 `openspec/specs/`。
- 保留历史迁移记录在 `openspec/changes/archive/2026-05-11-migrate-legacy-specs-to-openspec/`。
- 不修改运行时代码、测试代码或产品行为。

## Capabilities

### New Capabilities

- 无。

### Modified Capabilities

- `harness-development-workflow`：明确长期规格以 `openspec/specs/` 为准，旧 `specs/00x-*` 只作为已迁移历史来源退役。

## Impact

- 删除旧 `specs/001-mvp-code-agent` 到 `specs/004-skill-loader`。
- 更新 `AGENTS.md`、`README.md`、`docs/PROGRESS.md` 和 `HANDOFF_TO_NEXT_CHAT.md`。
- 不修改 `app/`、`tests/` 或长期 OpenSpec requirements 的产品行为。
