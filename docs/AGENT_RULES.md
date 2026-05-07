# Agent 工作规则

本项目使用 Harness Engineering 思路管理 AI 辅助开发：让 Agent 通过规则、文档、验证和交接机制稳定工作。

## 分支规则

- `main` 只保留稳定可运行版本。
- `dev` 用于集成已完成阶段。
- 当前功能必须在 `feature/*` 分支开发。
- 每轮实现前先确认当前分支。
- 如果当前不在正确 feature 分支，先暂停并提醒用户，不直接修改代码。

## 修改规则

- 严格遵守 `.harness/allowed_files.md`。
- 不要跨阶段实现未来功能。
- 不要把所有逻辑堆进 `main.py`。
- 不要提交缓存文件、虚拟环境、本地环境变量或临时产物。
- 文档、注释和用户可见文案优先使用中文。
- 函数名、类名、接口字段和命令保持英文工程约定。

## 验证规则

优先使用确定性检查，不要只靠 LLM review。

当前最低验证：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify.ps1
```

该脚本至少应运行：

- `pytest`
- `ruff check .`，如果当前环境已安装 ruff

如果某个检查无法运行，最终说明必须写清楚原因。

## 交接规则

每轮结束必须更新：

- `docs/PROGRESS.md`
- `HANDOFF_TO_NEXT_CHAT.md`
- 必要时更新 `docs/FEATURE_LIST.json`

交接内容至少包含：

- 当前分支。
- 本轮完成内容。
- 修改文件。
- 验证命令和结果。
- 未完成事项。
- 下一轮建议。

## Review 规则

Review Agent 必须检查：

- 是否符合当前阶段 scope。
- 是否修改了不该改的文件。
- 是否真的运行了验证命令。
- 是否存在假实现或过度设计。
- 是否破坏架构边界。
- 是否更新测试和文档。
- 是否更新 progress 和 handoff。
