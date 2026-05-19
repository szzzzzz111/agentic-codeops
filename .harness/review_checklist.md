# 当前 Review 清单

当前暂无活跃开发阶段；下一阶段开始前，必须把本文件更新为该阶段 review 清单。

默认检查项：

- [ ] 当前变更有对应 OpenSpec change，或明确说明为什么不需要。
- [ ] `.harness/allowed_files.md` 已更新为当前阶段写入边界。
- [ ] 变更没有恢复旧 `specs/00x-*` 作为规格入口。
- [ ] OpenSpec、Superpowers、MCP、plugin 或外部 skill 没有被误写成 RepoPilot runtime 能力。
- [ ] 未把 LLM、RAG、Memory、Reflection、真实审批流程、SandboxRunner 或 eval 写成已实现，除非当前阶段确实实现。
- [ ] 已运行 `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`，或说明无法运行的原因。
