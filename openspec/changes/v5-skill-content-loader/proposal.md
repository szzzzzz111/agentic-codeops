## Why

V4 已建立 Skill Metadata Loader，只能发现 `.agents/skills/*/SKILL.md` 并读取 `name`、`description` 和 `path`。V5 需要补上 DeepAgents 风格 progressive disclosure 的下一层：在调用方已经选定某个 skill 后，按需读取该 `SKILL.md` 的完整内容，同时继续保持路径、安全和阶段边界清晰。

## What Changes

- 为 skill loader 增加按相对路径读取完整 `SKILL.md` 内容的能力。
- 读取入口必须限制在当前 `repo_path` 下的 `.agents/skills/*/SKILL.md`，拒绝路径逃逸、非 skill 文件、缺失文件和目录符号链接绕过。
- 完整内容输出必须包含调用方需要的正文，但不得返回本机绝对路径。
- 保留 V4 metadata-first 行为：`load_skill_metadata(repo_path)` 仍只返回 `name`、`description` 和 `path`。
- 继续不接入 `/chat` 决策、不执行 skill、不接真实 LLM、不把 skill 内容自动注入 prompt。

## Capabilities

### New Capabilities

- 无。

### Modified Capabilities

- `skill-metadata-loader`: 从仅 metadata discovery 扩展为 metadata-first + 按需 content loading；仍不承担 skill 选择、执行或 `/chat` 决策。

## Impact

- 预计影响 `app/tools/skill_loader.py` 和 `tests/test_skill_loader.py`。
- 需要同步当前阶段 `.harness/allowed_files.md`、`.harness/review_checklist.md`、`docs/PROGRESS.md`、`docs/FEATURE_LIST.json` 和 `HANDOFF_TO_NEXT_CHAT.md`。
- 不新增运行时依赖，不改变 `/chat` API，不改变 `ToolExecutor` 当前行为。
