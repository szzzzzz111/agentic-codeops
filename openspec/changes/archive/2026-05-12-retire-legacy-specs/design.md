## Context

`openspec/specs/` 已包含从 V1-V4 legacy specs 迁移来的长期 capabilities。旧 `specs/00x-*` 与 OpenSpec specs 内容重叠，继续作为入口会增加维护成本和上下文负担。

## Goals / Non-Goals

**Goals:**

- 让 `openspec/specs/` 成为长期规格唯一入口。
- 删除旧 `specs/00x-*`，减少重复文档。
- 保留迁移归档记录，便于追溯旧 specs 来源。

**Non-Goals:**

- 不修改运行时代码。
- 不修改测试行为。
- 不改变 V1-V4 已验收产品能力。
- 不重新设计 OpenSpec capability 内容。

## Decisions

- 删除旧 `specs/00x-*`，不移动到另一个历史目录。
  - 理由：迁移归档已经保留了旧规格映射，继续复制历史目录会延续重复入口问题。
  - 备选方案：移动到 `docs/archive/legacy-specs/`；放弃，因为会继续让 Agent 在两个位置寻找规格。

- 在 `harness-development-workflow` 中记录长期规格入口决策。
  - 理由：这是开发流程规则，不是产品运行时功能。

## Risks / Trade-offs

- 删除旧目录可能让熟悉旧路径的 Agent 一开始找不到历史 specs。
  - 缓解：更新 `AGENTS.md`、README、progress 和 handoff，明确旧 specs 已迁移到 `openspec/specs/`。

- 旧阶段叙事不再以目录形式存在。
  - 缓解：阶段历史继续保留在 `docs/PROGRESS.md` 和 OpenSpec archive 中。
