# 任务：V2 安全仓库文件工具

## 实现

- [x] 创建 V2 spec、plan 和 tasks。
- [x] 更新 harness 允许文件。
- [x] 更新 harness 评审清单。
- [x] 增加 `app/tools/__init__.py`。
- [x] 实现 `list_files`。
- [x] 实现 `read_file`。
- [x] 实现 `search_code`。
- [x] 增加普通文件列举测试。
- [x] 增加忽略目录和敏感文件测试。
- [x] 增加 repo 内文件读取测试。
- [x] 增加 repo 外文件拒绝测试。
- [x] 增加敏感文件拒绝测试。
- [x] 增加代码搜索结果测试。
- [x] 增加空搜索结果测试。
- [x] 增加不返回敏感文件内容的测试。
- [x] 更新 README。

## 验证

- [ ] 运行 `pytest`。
- [ ] 运行 `ruff check .`。

## 延后

- [ ] 将工具连接到 `CodeAgent`。
- [ ] 在 `/chat` 中记录工具调用。
- [ ] 加入技能加载器。
- [ ] 加入反思检查。
- [ ] 加入小型评测。
