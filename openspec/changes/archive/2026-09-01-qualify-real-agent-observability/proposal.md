# Why

RepoPilot 的近期主线已经转为 Coding Agent Governance Harness，但继续开发 supervisor 之前有一个更基础的
资格问题：是否能从一个真实 Coding Agent 取得可机器观察的终态/完成声明，并让独立验证回执绑定 Agent 结束后
同一个代码快照。现有 fake/offline provider、单元测试或手写事件不能回答这个问题。

# What Changes

- 增加一个开发期、fail-closed 的真实 Agent 可观察性 qualification validator；它只解析冻结输入，不启动 Agent、
  不 apply、不 commit，也不进入 RepoPilot runtime。
- 在一个新建且干净的临时 Git fixture 中显式运行真实 Codex CLI，捕获 JSONL 终态与最终 completion claim。
- 在 Agent 终态后捕获 Git snapshot，独立运行 fixture verification，再捕获 snapshot；receipt 必须绑定相同快照。
- 用六类确定性负样本验证缺失、歧义、dirty baseline、验证失败与 snapshot mismatch 全部 fail closed。
- 保存最小、可复核的 qualification observation/report；真实证据与合成测试 fixture 明确分离。

# Impact

这是 low-risk qualification spike：只修改 scripts/tests/OpenSpec/Harness/进度交接文档，不修改 `app/**`、runtime
public contract、provider 默认值、权限、持久化、依赖或网络默认行为。结果最多证明
`QUALIFIED_OBSERVABILITY`，不能证明 Agent 语义完成、代码正确、产品验收、supervisor MVP 或任何 Git delivery。
若真实 completion event 或 snapshot-bound receipt 任一不能成立，结果必须为 `NOT_OBSERVED`，阶段立即停止。
