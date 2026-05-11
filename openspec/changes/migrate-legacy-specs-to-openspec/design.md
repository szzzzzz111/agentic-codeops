## Context

RepoPilot 早期使用 `specs/00x-*` 目录管理 V1-V4 阶段规格。现在仓库已经有项目级 OpenSpec，但 `openspec/specs/` 仍为空，因此后续 Agent 还没有一个长期、能力导向的 OpenSpec 规格视图。

本迁移只做文档转换：把已验收行为转成 OpenSpec capabilities，同时保留旧 specs，直到迁移经过 review。

## Goals / Non-Goals

**Goals:**

- 创建覆盖 V1-V4 已验收行为的 OpenSpec capability specs。
- 将历史阶段规格映射为长期能力规格，便于后续 OpenSpec change 引用。
- 保持运行时代码和测试行为不变。
- 继续让 `.harness` 负责 allowed files、review checklist、验证和 handoff 纪律。

**Non-Goals:**

- 不修改 `app/` 运行时代码。
- 不修改 `tests/` 测试行为。
- 不在本规划 change 中删除旧 `specs/00x-*`。
- 不引入 MCP、plugin runtime、skill 执行、动态工具注册或 `/chat` 决策变更。

## Decisions

- 使用能力导向的 OpenSpec 名称，而不是沿用旧阶段编号。
  - 理由：OpenSpec 长期规格应该描述稳定能力，而不是历史实现阶段。
  - 备选方案：直接镜像 `001-*` 到 `004-*`；放弃，因为这会继续绑定阶段编号。

- 旧 `specs/00x-*` 暂时保留。
  - 理由：旧 specs 仍然是历史审计和验收上下文。
  - 备选方案：同一 change 中删除旧 specs；放弃，因为会增加 review 风险。

- 将 harness workflow 作为独立 capability。
  - 理由：RepoPilot 的可控开发纪律本身就是 Code Agent Harness 的重要能力。
  - 备选方案：只保留在 `.harness` 文档中；放弃，因为后续 OpenSpec change 需要可发现的流程契约。

## Risks / Trade-offs

- 旧 specs 和 OpenSpec specs 在迁移期间可能暂时并存。
  - 缓解：保持本 change 独立，review 映射准确性，接受后再决定旧 specs 去留。

- OpenSpec specs 不再按时间线组织。
  - 缓解：历史叙事继续放在 `docs/PROGRESS.md` 和 `HANDOFF_TO_NEXT_CHAT.md`。

- OpenSpec 不能替代 harness review 规则。
  - 缓解：继续强制维护 `.harness/allowed_files.md`、`.harness/review_checklist.md`、验证和 handoff。

## Migration Plan

1. 在本 change 中创建 OpenSpec capability specs。
2. 对照旧 `specs/00x-*`、README、progress 和 feature list review 映射。
3. 运行 `openspec validate migrate-legacy-specs-to-openspec`。
4. 接受后归档该 OpenSpec change，生成长期 `openspec/specs/`。
5. 后续单独决定旧 `specs/00x-*` 是删除、移动到归档文档，还是保留为历史阶段记录。

## Open Questions

- OpenSpec 归档后，旧 `specs/00x-*` 应删除、归档，还是继续保留？
- `docs/FEATURE_LIST.json` 是否继续作为验收索引，还是后续改为由 OpenSpec specs 承担主来源？
