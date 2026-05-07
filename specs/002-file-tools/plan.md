# 计划：V2 安全仓库文件工具

## 文件

- `app/tools/__init__.py`：仓库工具包标记。
- `app/tools/file_tools.py`：安全文件列举、读取和搜索。
- `tests/test_file_tools.py`：文件工具安全契约的单元测试。
- `specs/002-file-tools/spec.md`：V2 范围和验收标准。
- `specs/002-file-tools/plan.md`：实现计划。
- `specs/002-file-tools/tasks.md`：任务清单。
- `.harness/allowed_files.md`：更新 V2 允许文件。
- `.harness/review_checklist.md`：更新 V2 评审清单。
- `README.md`：记录 V2 文件工具。

## 设计

使用 `pathlib.Path` 处理路径，并通过 `Path.resolve()` 加 `relative_to()` 检查访问是否仍在 `repo_path` 内。不调用 shell 命令。

目录遍历时，在进入子目录前跳过忽略目录。

敏感文件通过文件名和扩展名排除，包括 `.env`、`.npmrc`、`.pypirc`、`.netrc`、密钥文件和证书文件。二进制文件通过读取少量字节样本检测并跳过。

V2 只是安全只读工具层，不是权限系统、操作系统级沙箱或人工介入工作流。这些能力后续应围绕统一工具执行边界增加，而不是散落在 API handler 或单个工具函数里。

未来工具调用应走：

```text
CodeAgent -> ToolExecutor -> PermissionPolicy / ApprovalGate / SandboxRunner -> file_tools
```

这样权限、审批、审计和沙箱命令执行都可以增量加入。只读工具可以不经审批直接运行；写操作、shell 执行、commit 或 PR 等高风险工具应在执行前要求明确审批。

## 开发顺序

1. 增加 specs 和 tasks。
2. 更新 harness 允许文件和评审清单。
3. 实现 `app/tools/file_tools.py`。
4. 使用临时仓库增加测试。
5. 更新 README。
6. 运行 `pytest`。
7. 运行 `ruff check .`。

## 测试策略

使用 `tmp_path` 创建小型测试仓库。覆盖普通代码文件、隐藏目录、忽略目录、敏感文件、二进制文件，以及用于路径穿越测试的 repo 外文件。
