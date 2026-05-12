# 评审清单：Legacy Specs 退役

- [ ] 当前分支是 `feature/retire-legacy-specs`。
- [ ] 只修改了 Legacy Specs 退役允许文件。
- [ ] 未修改 `app/` 运行时代码。
- [ ] 未修改 `tests/` 测试代码。
- [ ] 旧 `specs/00x-*` 已删除或退役，不再作为当前规格入口。
- [ ] `AGENTS.md` 不再要求阅读旧 `specs/00x-*`，并指向 `openspec/specs/`。
- [ ] README、PROGRESS 和 HANDOFF 已说明长期规格以 `openspec/specs/` 为准。
- [ ] 历史迁移记录仍保留在 `openspec/changes/archive/2026-05-11-migrate-legacy-specs-to-openspec/`。
- [ ] `openspec list` 显示 No active changes found。
- [ ] `openspec list --specs` 显示 5 个迁移后的 capabilities。
- [ ] 未修改长期 `openspec/specs/` 的 requirement 行为。
- [ ] 已运行 `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`，或说明无法运行的原因。
- [ ] 已运行 `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`，或说明无法运行的原因。
