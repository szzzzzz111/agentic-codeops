# 评审清单：Legacy Specs OpenSpec 归档

- [ ] 当前分支是 `feature/archive-legacy-specs-openspec`。
- [ ] 只修改了 Legacy Specs OpenSpec 归档允许文件。
- [ ] 未修改 `app/` 运行时代码。
- [ ] 未修改 `tests/` 测试代码。
- [ ] 未删除或移动旧 `specs/00x-*`。
- [ ] `migrate-legacy-specs-to-openspec` 已移动到 `openspec/changes/archive/2026-05-11-migrate-legacy-specs-to-openspec/`。
- [ ] `openspec/specs/` 已生成 chat API、safe repository file tools、agent loop tool execution、skill metadata loader 和 harness development workflow 长期规格。
- [ ] `openspec list` 显示 No active changes found。
- [ ] `openspec list --specs` 显示 5 个迁移后的 capabilities。
- [ ] OpenSpec specs 不把未来能力写成已实现。
- [ ] OpenSpec specs 不引入 runtime MCP、plugin、skill execution、dynamic tool registration 或 `/chat` 决策变更。
- [ ] 已运行 `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`，或说明无法运行的原因。
- [ ] 已运行 `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`，或说明无法运行的原因。
