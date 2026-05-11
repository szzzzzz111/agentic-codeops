# 计划：V4 Skill Metadata Loader

## 文件

V4 实现阶段修改：

- `specs/004-skill-loader/spec.md`：V4 范围、metadata 契约和验收标准。
- `specs/004-skill-loader/plan.md`：V4 实现计划和阶段边界。
- `specs/004-skill-loader/tasks.md`：V4 任务清单。
- `app/tools/skill_loader.py`：Skill Metadata Loader 实现。
- `tests/test_skill_loader.py`：V4 聚焦测试。
- `.harness/allowed_files.md`：V4 实现阶段允许文件。
- `.harness/review_checklist.md`：V4 实现阶段评审清单。
- `docs/PROGRESS.md`：记录 V4 状态。
- `HANDOFF_TO_NEXT_CHAT.md`：交接 V4 当前上下文。
- `README.md`、`docs/FEATURE_LIST.json`：记录 V4 已实现能力。

当前实现阶段只开放 `app/tools/skill_loader.py` 和 `tests/test_skill_loader.py`，不开放 API handler、Service 层、Agent loop 或 `/chat` 决策修改。

## 设计边界

V4 只做 Skill Metadata Loader：

```text
repo_path
  -> .agents/skills/*/SKILL.md
  -> frontmatter metadata
  -> SkillMetadata(name, description, path)
```

设计重点：

- metadata-first：只读 frontmatter 元数据。
- progressive disclosure 延后：完整 `SKILL.md` 正文由后续阶段按需读取。
- agent loop 延后：V4 不根据用户消息选择 skill，不改变 `/chat` 行为。
- 安全边界延续：所有路径限制在 `repo_path` 内，输出使用相对路径。

## 实现

V4 新增独立工具模块，避免把技能发现逻辑塞进 API、Service 或 Agent 层：

```text
app/tools/skill_loader.py
```

公开函数：

```python
def load_skill_metadata(repo_path: str) -> list[dict[str, str]]:
    ...
```

当前实现使用 Python 标准库逐行读取 `SKILL.md` 开头的 YAML frontmatter，只支持简单 `key: value`。读取遇到 frontmatter 结束线即停止，不读取或返回完整 skill 正文。

当前错误策略是 fail fast：如果某个 `SKILL.md` 缺少必要 metadata、frontmatter 未闭合或格式不合法，Loader 直接抛出异常。后续等日志、trace audit 或 skill audit 能力存在后，可以改成记录坏 skill 并跳过，避免单个坏配置阻断整体发现。

## 测试策略

已新增聚焦测试：

- 构造临时仓库和 `.agents/skills/example/SKILL.md`。
- 验证返回 `name`、`description` 和相对 `path`。
- 构造多个技能，验证排序稳定。
- 验证不存在 `.agents/skills` 时返回空列表。
- 验证正文中包含唯一 token 时，Loader 不返回正文内容。
- 验证异常 frontmatter 受读取限制。
- 验证路径不泄露本机绝对路径。
- 运行既有全量验证，确认 V1/V2/V3 行为不变。

## 阶段推进顺序

1. 已确认当前分支为 `feature/v4-skill-loader`。
2. 已创建 `specs/004-skill-loader/spec.md`、`plan.md` 和 `tasks.md`。
3. 已更新 harness 允许文件和 review checklist，开放 V4 实现文件。
4. 已新增 `app/tools/skill_loader.py` 和 `tests/test_skill_loader.py`。
5. 已更新 README、`docs/PROGRESS.md`、`HANDOFF_TO_NEXT_CHAT.md` 和 `docs/FEATURE_LIST.json`。
6. 已运行验证命令，确认既有 V1/V2/V3 行为不变。

## 延后阶段

- V5 或后续：Skill Content Loader / progressive disclosure，按需读取完整 `SKILL.md`。
- V6 或后续：Skill-aware Agent Loop，基于用户消息和 skill metadata 选择相关 skill。
- 更后续：trace/tool/skill audit、eval、Reflection、RAG 或 Memory。

这些能力不能在 V4 中写成已实现。
