# 任务：V3 Agent Loop

## 计划阶段

- [x] 确认当前 V2 已集成。
- [x] 创建并切换到 `feature/v3-agent-loop`。
- [x] 创建 `specs/003-agent-loop/spec.md`。
- [x] 创建 `specs/003-agent-loop/plan.md`。
- [x] 创建 `specs/003-agent-loop/tasks.md`。
- [x] 更新 `.harness/allowed_files.md` 为 V3 计划阶段允许文件。
- [x] 更新 `.harness/review_checklist.md` 为 V3 计划阶段评审清单。
- [x] 更新 `docs/PROGRESS.md`，记录 V3 specs 计划状态。
- [x] 更新 `HANDOFF_TO_NEXT_CHAT.md`，交接 V3 specs 状态。
- [x] 更新 `docs/FEATURE_LIST.json`，保持 V3 未实现状态。

## 后续实现阶段

- [x] 更新 `.harness/allowed_files.md`，开放 V3 实现需要的运行时代码和测试文件。
- [x] 增加轻量 `ToolExecutor`。
- [x] 让 `CodeAgent` 通过 `ToolExecutor` 调用 `search_code`。
- [x] 实现最小确定性关键词提取。
- [x] 从搜索结果生成去重后的 `related_files`。
- [x] 在 `tool_calls` 中记录 `search_code` 和关键词摘要。
- [x] 保持 `/chat` 请求和响应 schema 不变。
- [x] 增加 `UNIQUE_BUG_TOKEN` 命中测试。
- [x] 增加无命中稳定返回测试。
- [x] 增加敏感文件不泄露测试。
- [x] 增加工具错误摘要脱敏测试。
- [x] 更新 README。
- [x] 更新 `docs/PROGRESS.md`。
- [x] 更新 `HANDOFF_TO_NEXT_CHAT.md`。
- [x] 维护 `docs/FEATURE_LIST.json` 中 V3 功能状态。

## 验证

- [x] 运行 `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`。
- [x] 确认 `pytest` 通过。
- [x] 确认 `ruff check .` 通过。

## 延后

- [ ] 真实 LLM 接入。
- [ ] 自动修改代码。
- [ ] shell 工具。
- [ ] 多 Agent。
- [ ] RAG。
- [ ] Memory。
- [ ] Reflection。
- [ ] eval。
