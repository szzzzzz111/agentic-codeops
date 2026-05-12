## 1. OpenSpec Change

- [x] 1.1 创建 `retire-legacy-specs` proposal。
- [x] 1.2 创建 design，说明删除旧 specs 而不是移动归档的取舍。
- [x] 1.3 创建 `harness-development-workflow` spec delta，明确 `openspec/specs/` 是长期规格入口。

## 2. Cleanup

- [x] 2.1 删除旧 `specs/001-mvp-code-agent`。
- [x] 2.2 删除旧 `specs/002-file-tools`。
- [x] 2.3 删除旧 `specs/003-agent-loop`。
- [x] 2.4 删除旧 `specs/004-skill-loader`。
- [x] 2.5 更新 `AGENTS.md`、README、PROGRESS 和 HANDOFF。

## 3. Verification

- [x] 3.1 运行 `openspec validate retire-legacy-specs`。
- [x] 3.2 运行 `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`。
- [x] 3.3 运行 `git diff --check`。
- [x] 3.4 归档 `retire-legacy-specs`，让长期 `openspec/specs/` 记录入口变更。
