## MODIFIED Requirements

### Requirement: Agent Loop 由轻量 Harness Kernel 编排

系统 SHALL 提供轻量 Agent Harness Kernel，用于编排请求路由、Long Task 边界、Memory 边界、Assistant Control Surface、Patch command / Patch intent、Verification intent、工具元数据、工具调用、grounded answer 边界和 trace event。默认 Kernel MUST 保持确定性，MUST NOT 在未显式配置 provider 时依赖真实 LLM。

前置控制命令的具体顺序为：先解析 V13 memory command，再解析 Long Task command，然后解析 Assistant Control Surface 状态请求，然后解析 V16/V18 Patch command / Patch intent，其中组合确认 MUST 在 Patch command 分支内优先捕获；然后解析 V17 Verification intent，最后才进入 capability-status 或 `RequestRouter`。优先级 SHALL 为 `组合确认 > 纯 verification intent > capability-status/repo_search`。Patch command / Patch intent 和 Verification intent 命中后，系统 MUST NOT 将该请求误当作普通 repo_search 或 capability-status。

#### Scenario: 组合确认优先于纯 verification intent

- **WHEN** 聊天消息包含 `patch_id` 和明确验证 label
- **THEN** AgentLoop MUST 在 Patch command 分支处理组合确认
- **AND** AgentLoop MUST NOT 将其当作纯 verification request

#### Scenario: Verification intent 在 repo_search 前处理

- **WHEN** 聊天消息是明确验证请求
- **THEN** AgentLoop 在 capability-status 和 repo_search 前处理该请求
- **AND** Agent MUST NOT 直接走普通 repo_search answer

#### Scenario: Memory、Long Task、Assistant Control Surface 和 Patch 仍优先于 Verification

- **WHEN** 聊天消息是明确 memory command、Long Task command、Assistant Control Surface 请求或 Patch command / Patch intent
- **THEN** AgentLoop MUST 先按既有前置分支处理
- **AND** Agent MUST NOT 因正文包含 verify 或 test 词而改走 Verification intent
