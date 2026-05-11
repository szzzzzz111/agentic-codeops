# Legacy Specs OpenSpec 归档允许文件

- `openspec/changes/archive/2026-05-11-migrate-legacy-specs-to-openspec/**`
- `openspec/specs/agent-loop-tool-execution/spec.md`
- `openspec/specs/chat-api/spec.md`
- `openspec/specs/harness-development-workflow/spec.md`
- `openspec/specs/safe-repository-file-tools/spec.md`
- `openspec/specs/skill-metadata-loader/spec.md`
- `openspec/changes/migrate-legacy-specs-to-openspec/**`
- `.harness/allowed_files.md`
- `.harness/review_checklist.md`
- `docs/PROGRESS.md`
- `HANDOFF_TO_NEXT_CHAT.md`
- `AGENTS.md`

本阶段只允许归档 `migrate-legacy-specs-to-openspec` OpenSpec change，并生成长期 `openspec/specs/`。不开放 `app/` 运行时代码、`tests/` 测试代码或旧 `specs/00x-*` 删除。

旧 `specs/00x-*` 是否删除、移动或保留仍需后续独立 cleanup change 决策。
