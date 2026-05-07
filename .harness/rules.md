# 执行约束规则

## V1 范围

V1 只做可运行的 FastAPI 骨架和模拟代码智能体。API 为了后续兼容会接收 `repo_path`，但 V1 代码不能读取该路径下的文件。

## 分层

使用这条边界：

```text
API -> Service -> Agent -> Trace
```

- API 只处理 HTTP。
- Service 编排请求处理。
- Agent 负责分析行为。
- Trace 负责生成 trace ID。

## V1 禁止项

- 真实 LLM 调用。
- 读取仓库文件。
- `list_files`、`read_file` 或 `search_code`。
- 技能加载器。
- 反思检查。
- 评测。
- 复杂智能体循环。
- 自动修改代码。
- 硬编码 API key 或密钥。
