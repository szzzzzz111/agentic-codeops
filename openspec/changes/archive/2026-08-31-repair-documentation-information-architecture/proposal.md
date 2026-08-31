# Why

RepoPilot 已经规定 durable document ownership 和 risk-scaled workflow，但实际文档仍出现三类可复现漂移：
tracked handoff 保存了已经过期的 delivery 待办，PROGRESS/ARCHITECTURE 混合 current facts 与历史叙事，
OpenSpec index 和 FEATURE_LIST 保留旧阶段状态。现有 scanner 与 tests 对这些错误仍返回 PASS。

交付预检进一步暴露了一个 authority gate 矛盾：risk contract 允许明确的 low-risk 阶段使用零个 independent
review slot，但 `validate_independent_review.py` 当前拒绝 `required_slots=0`，导致 archive gate 只能失败或
人为制造 review slot。

# What Changes

- 明确按 change class 路由 implementation review，并把实施风险与 Git delivery action 分开。
- 把 HANDOFF 收窄为稳定的 live-resume protocol，不再让 tracked file 自证其所在 commit 已 push。
- 将 ARCHITECTURE 改为 current-first runtime map，将历史细节交给 archived OpenSpec。
- 将 PROGRESS 收窄为 durable status、remaining debt、candidate sequence 和简洁 archive index。
- 修复 FEATURE_LIST 与 OpenSpec indexes 的 current-fact drift。
- 强化 deterministic docs scanner/tests，使上述错误不再误报 PASS。
- 将 plan/implementation slot count 绑定进 authority scope；只有显式绑定为 zero 的 low-risk 阶段才能以空
  receipts/history 的完整 packet review set 进入 delivery gate，同时保持未绑定或 medium/high zero、非整数/
  负数 count、非空 receipts/history 和所有 positive-slot 规则 fail closed。
- 对采用新 slot binding 的未来阶段，`implement` preflight 必须消费 canonical plan review set、host-retained
  packet hash 与对应 plan count；不能把输入留成可选提示或用 implementation phase 替代。

# Impact

阶段原始文档整理部分是 low risk；新增的 review validator 语义属于 authority-sensitive，因此整体向上升级为
high risk，并在实现前补做两个空上下文 plan-review slots。修改仅限开发流程 validator/tests，不修改 `app/**`、
runtime/public API、权限、持久化、依赖、网络默认值或产品级 Git automation。不新增文档站、生成器或依赖，
不改写既有 archived OpenSpec history。
