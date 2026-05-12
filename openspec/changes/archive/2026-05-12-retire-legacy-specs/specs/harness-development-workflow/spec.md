## ADDED Requirements

### Requirement: OpenSpec specs 是长期规格入口

仓库 SHALL 使用 `openspec/specs/` 作为长期规格入口。旧 `specs/00x-*` 迁移完成后 MUST NOT 继续作为当前规格入口维护。

#### Scenario: Agent 查找长期规格

- **WHEN** Agent 需要查看当前已验收能力规格
- **THEN** Agent 读取 `openspec/specs/` 中的 capability specs

#### Scenario: 旧 specs 已退役

- **WHEN** Agent 看到历史迁移记录
- **THEN** Agent 将旧 `specs/00x-*` 视为已迁移来源，而不是当前可编辑规格入口
