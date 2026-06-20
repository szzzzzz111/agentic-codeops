## Context

`AgentLoop` 通过静态 capability-status 文案回答“patch 是否支持”等问题。该文案创建于 V16-V18，
在 V19-V23 完成后未更新，测试又把旧 non-goal 固化。另一方面，仓库存在
`ModelPatchAuthoringProvider`，但默认 `AgentLoop` 构造 `PatchManager()` 时没有把
`load_model_provider_from_env()` 包装后注入，因此环境变量启用的共享 provider 只供 grounded
answer 和 Long Task planner 使用，不会启用真实 patch proposal。

本 change 同时涉及用户可见回答、测试、长期规格和人类文档，但不改变执行链路。

## Goals / Non-Goals

**Goals:**

- patch capability-status 准确反映 V16-V23 已实现能力。
- 状态回答明确当前仍未实现 promotion、自动 commit/push 和默认真实 diff 生成。
- 文档/spec 准确描述 `ModelPatchAuthoringProvider` 的“可注入但未默认装配”边界。
- 用 Kernel 与 API 测试锁定当前事实，而不是历史版本措辞。

**Non-Goals:**

- 不把真实 patch provider 接入环境配置。
- 不修改 provider schema、citation/diff 校验、patch store 或 apply 行为。
- 不修改路由优先级、API contract、权限、审批、worktree、verification 或 audit。
- 不处理检索性能、认证、并发、依赖锁定或 V24。

## Decisions

1. **保留确定性静态 capability-status，只更新事实内容。**
   当前问题是数据过期，不是路由架构缺失。引入动态 capability registry 会扩大 scope，并增加新的
   一致性来源。

2. **回答使用能力名称而非提交/hash。**
   状态回答列出 Safe Patch Authoring、Verification Runner、Patch + Verify、Persistent Audit 和
   Worktree lifecycle；non-goal 只保留当前真实未实现项。

3. **文档选择降级声明，而不是补 provider wiring。**
   `ModelPatchAuthoringProvider` 的类级可注入性是真实能力；环境变量驱动的默认应用装配不是。补 wiring
   会改变默认运行时、安全面和测试范围，应作为独立功能阶段。

4. **测试断言当前语义，不依赖完整长字符串。**
   Kernel/API 测试确认已实现能力存在、错误旧措辞不存在、工具未被调用、顶层 contract 不变。

## Risks / Trade-offs

- [Risk] 静态 capability-status 未来仍可能漂移 → 用跨阶段语义断言和 focused review 检查降低风险。
- [Risk] 文档降级后用户误以为 provider 类无用途 → 明确它仍可通过依赖注入用于测试或自定义装配。
- [Risk] 只修 patch 状态，其他历史状态常量未来也可能漂移 → 本 change 不扩 scope；在 debt sweep 中记录
  是否发现同类当前错误。
