## 1. Harness

- [x] 1.1 创建 `v8-query-understanding-repo-rag` OpenSpec change。
- [x] 1.2 更新 `.harness/allowed_files.md`。
- [x] 1.3 更新 `.harness/review_checklist.md`。

## 2. OpenSpec

- [x] 2.1 编写 V8 proposal。
- [x] 2.2 编写 V8 design，并记录参考项目只作为规划资料。
- [x] 2.3 编写 `repo-query-understanding-rag` spec delta。
- [x] 2.4 编写 `agent-loop-tool-execution` spec delta。
- [x] 2.5 运行 `openspec validate v8-query-understanding-repo-rag`。

## 3. Tests

- [x] 3.1 为 query understanding 和 search plan 写失败测试。
- [x] 3.2 为 lexical repo chunk、scoring、citation 写失败测试。
- [x] 3.3 为 `AgentLoop` 集成 repo-local lexical RAG 写失败测试。
- [x] 3.4 为 `/chat` contract 不新增顶层字段写回归测试。
- [x] 3.5 为“不编造 embedding/Milvus/ES/memory 已实现”写回归测试。

## 4. Implementation

- [x] 4.1 新增 deterministic query understanding。
- [x] 4.2 新增 repo chunk 和 lexical retriever。
- [x] 4.3 将 `AgentLoop` 从单 keyword search 接入 query understanding + lexical repo RAG。
- [x] 4.4 保持权限/审批边界和 `/chat` contract 不变。
- [x] 4.5 保持现有 `ToolExecutor.search_code` 兼容或提供等价审计摘要。

## 5. Docs and Verification

- [x] 5.1 更新 `README.md`。
- [x] 5.2 更新 `docs/ARCHITECTURE.md`。
- [x] 5.3 更新 `docs/PROGRESS.md`。
- [x] 5.4 更新 `docs/FEATURE_LIST.json`。
- [x] 5.5 更新 `HANDOFF_TO_NEXT_CHAT.md`。
- [x] 5.6 运行 `pytest`。
- [x] 5.7 运行 `ruff check .`。
- [x] 5.8 运行 `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`。
- [x] 5.9 运行 `openspec validate --all`。
- [x] 5.10 运行 `git diff --check`。
