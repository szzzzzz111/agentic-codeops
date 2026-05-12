# Legacy Specs 退役允许文件

- `openspec/changes/retire-legacy-specs/**`
- `openspec/changes/archive/*retire-legacy-specs*/**`
- `specs/001-mvp-code-agent/**`
- `specs/002-file-tools/**`
- `specs/003-agent-loop/**`
- `specs/004-skill-loader/**`
- `.harness/allowed_files.md`
- `.harness/review_checklist.md`
- `AGENTS.md`
- `README.md`
- `docs/PROGRESS.md`
- `HANDOFF_TO_NEXT_CHAT.md`

本阶段只允许退役已迁移到 OpenSpec 的旧 `specs/00x-*`，并更新入口文档和交接说明。不开放 `app/` 运行时代码、`tests/` 测试代码或长期 `openspec/specs/` 行为修改。

退役后长期规格以 `openspec/specs/` 为准；历史迁移记录保留在 `openspec/changes/archive/2026-05-11-migrate-legacy-specs-to-openspec/`。
