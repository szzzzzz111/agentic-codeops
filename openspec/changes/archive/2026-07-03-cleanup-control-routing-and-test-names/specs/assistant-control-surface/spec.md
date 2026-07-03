## MODIFIED Requirements

### Requirement: 控制面路由优先级稳定

系统 SHALL 在 AgentLoop 中按固定顺序处理前置控制面：Memory command、Long Task command、Assistant Control Surface，然后进入 `RequestRouter` 的 capability_status / repo_search / chat_only routing。

Assistant Control Surface status parsing SHALL remain narrow and explicit. Cleanup of capability-status routing or test names MUST NOT add new status trigger phrases unless a separate behavior-expansion change explicitly approves them.

#### Scenario: Memory 和 Long Task 命令优先于控制面

- **WHEN** 用户发送明确 memory command 或 Long Task command，且正文包含助手状态类词语
- **THEN** 系统 MUST 按 Memory 或 Long Task 命令处理
- **AND** 系统 MUST NOT 返回 Assistant Control Surface 状态回答

#### Scenario: capability-status 不被控制面误吞

- **WHEN** 用户发送 `memory 实现了吗?`
- **THEN** 系统 MUST 返回 capability-status 回答
- **AND** 系统 MUST NOT 返回 Assistant Control Surface 聚合状态

#### Scenario: 控制面 cleanup 不扩展自然语言触发词

- **WHEN** 用户发送未列入明确状态触发词的普通自然语言问题
- **THEN** Assistant Control Surface parser MUST NOT classify it as a status request
- **AND** the request MAY continue to normal routing
