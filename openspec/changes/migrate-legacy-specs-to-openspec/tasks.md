## 1. 迁移 Review

- [ ] 1.1 对照旧 `specs/001-mvp-code-agent` review OpenSpec capabilities。
- [ ] 1.2 对照旧 `specs/002-file-tools` review OpenSpec capabilities。
- [ ] 1.3 对照旧 `specs/003-agent-loop` review OpenSpec capabilities。
- [ ] 1.4 对照旧 `specs/004-skill-loader` review OpenSpec capabilities。
- [ ] 1.5 确认 `docs/FEATURE_LIST.json`、`README.md`、`docs/PROGRESS.md` 与 OpenSpec specs 不矛盾。

## 2. 归档 OpenSpec Change

- [ ] 2.1 运行 `openspec validate migrate-legacy-specs-to-openspec`。
- [ ] 2.2 归档该 change，让已接受 requirements 写入 `openspec/specs/`。
- [ ] 2.3 确认 `openspec list --specs` 能看到迁移后的 capabilities。
- [ ] 2.4 运行 `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`。

## 3. 旧 Specs 去留决策

- [ ] 3.1 决定旧 `specs/00x-*` 是删除、移动到归档文档，还是保留为历史阶段记录。
- [ ] 3.2 如果删除或移动旧 specs，先创建单独 cleanup change，再修改旧 specs。
- [ ] 3.3 归档或 cleanup 后更新 `AGENTS.md`、`docs/PROGRESS.md` 和 `HANDOFF_TO_NEXT_CHAT.md`。
