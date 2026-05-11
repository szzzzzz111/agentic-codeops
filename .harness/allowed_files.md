# Legacy Specs OpenSpec 迁移规划允许文件

- `openspec/changes/migrate-legacy-specs-to-openspec/**`
- `.harness/allowed_files.md`
- `.harness/review_checklist.md`
- `docs/PROGRESS.md`
- `HANDOFF_TO_NEXT_CHAT.md`
- `AGENTS.md`

本阶段只允许创建旧 `specs/00x-*` 到 OpenSpec 的迁移规划 change，不开放 `app/` 运行时代码、`tests/` 测试代码、旧 `specs/00x-*` 删除或 OpenSpec archive 操作。

迁移规划必须保持文档性：只新增 `openspec/changes/migrate-legacy-specs-to-openspec` 下的 proposal、design、tasks 和 spec delta。是否删除或归档旧 `specs/00x-*` 必须作为后续独立步骤处理。
