## Context

`AgentLoop` 使用静态 capability-status 常量回答当前能力问题。此前 patch 状态漂移已经修复，但
Stage Debt Sweep 发现 `V11_CAPABILITY_STATUS_ANSWER` 与 `V12_CAPABILITY_STATUS_ANSWER`
仍保留阶段创建时的历史 non-goals：

- V11 回答声称 query rewrite、rerank、memory 未实现；
- V12 回答声称 memory 未实现。

当前 V12 deterministic rewrite/rerank 与 V13 Memory 均已归档实现。历史 README/ARCHITECTURE
章节描述的是各阶段当时的边界，仍然正确，不应随当前状态回答一起改写。

## Goals / Non-Goals

**Goals:**

- 使 V11/V12 capability-status 准确描述当前 V1-V23 runtime。
- 保留真实 non-goals，不把 deterministic 能力写成真实 LLM 或向量能力。
- 用 Kernel/API 测试锁定当前事实和无工具调用 contract。
- 保持 V19 best-effort trace envelope 语义不变。

**Non-Goals:**

- 不引入动态 capability registry 或重构 capability 路由。
- 不修改 query rewrite、rerank、memory、provider 或 audit 实现。
- 不修改 `/chat` 顶层字段、权限、审批、存储或执行行为。
- 不把历史阶段章节中的当时 non-goals 改成当前状态。
- 不创建或规划 V24。

## Decisions

1. **只更新两个静态回答常量。**
   当前缺陷是文案事实漂移，不是路由或执行缺陷。动态 registry 会扩大范围并引入新的事实来源。

2. **V11 回答同时概括后续 V12/V13 能力。**
   当用户问 grounded answer/model provider 当前是否可用时，回答必须避免继续声称 rewrite/rerank
   与 memory 不存在，同时明确这些是后续阶段实现。

3. **V12 回答区分 deterministic 与真实模型能力。**
   当前已实现 deterministic rewrite/rerank 和 V13 Memory；真实 LLM rewrite/rerank、
   向量 memory、自动总结、跨 repo 智能召回与 context compression 仍是 non-goals。

4. **测试断言语义而非完整字符串。**
   测试确认已实现能力存在、过期否定措辞不存在、真实 non-goals 仍存在，且
   `related_files` / `tool_calls` 为空。

## Risks / Trade-offs

- [Risk] 静态回答未来仍可能漂移 → 使用跨阶段语义断言与 focused Stage Debt Sweep。
- [Risk] 回答变长后边界混淆 → 明确标注 V12/V13 后续能力和 deterministic/真实模型区别。
- [Trade-off] 不引入统一 registry，保留少量重复 → 以最小风险修复当前真实缺陷。
