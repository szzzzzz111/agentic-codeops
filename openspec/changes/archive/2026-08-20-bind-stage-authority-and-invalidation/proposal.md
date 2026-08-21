## Why

RepoPilot 的开发工作流已经要求人工确认、独立评审、archive、merge 和 push 授权，但连续执行授权仍只以自然语言存在，未机械绑定精确 stage scope、risk、action ceiling 和 Git target。范围、风险、remote、target branch 或最终被评审的 HEAD 漂移时，现有流程也没有统一的 fail-closed 失效合同。

## What Changes

- 新增 append-only repo-local stage authority record（阶段授权记录）、独立 delivery binding 与确定性 validator，把一次 direct-user authorization 绑定到精确 stage、planning baseline、risk、scope digest、允许动作上限和目标 remote/branch/tip。
- 明确仓库记录只能证明内容一致性，不能证明用户身份或宿主消息真实性；宿主控制器必须从当前 direct-user interaction 独立核对 live human authority。
- 定义 scope、risk、action ceiling、baseline、remote 或 target branch 漂移时的失效语义；validator 从 planning base 重算真实 Git change set，越界路径不得继承旧授权继续实现、commit、archive、merge 或 push。
- 在 archive/merge/push 前消费实际 independent-review set 与穷尽 change manifest；只允许两个 schema-valid evidence-tail JSON 在 final packet 后写入。
- 在 push 前绑定 exact candidate HEAD、effective push endpoint 和 authorized old tip，并使用 ancestry check + exact-old-OID lease 关闭 TOCTOU；ambiguous outcome 保持 `unknown` 并只读 reconciliation。
- 让 Codex/OpenCode 的 repo-local apply/archive 入口消费同一 authority gate，不能从旁路 warning-and-continue。
- 分离 `technical_ready`、`human_authorized` 和 `vcs_pushed` 三种 verdict，禁止用测试、review receipt 或仓库自写 hash 冒充人工授权或 push 成功。
- 更新开发 workflow、规则、模板、长期 spec、结构测试和 Harness 阶段边界；不新增 RepoPilot runtime Git 自动化。

## Capabilities

### New Capabilities

- `stage-authority-binding`: 定义开发阶段人工授权的机械绑定、失效触发、external authority claim ceiling 和 push 前 live target/HEAD preflight。

### Modified Capabilities

- `harness-development-workflow`: 让阶段 workflow 消费 stage authority validator，保持人工授权、技术就绪和 Git 推送事实相互独立。

## Impact

- 影响 repo-local 开发流程、Harness 模板/规则、确定性验证脚本与测试、OpenSpec 规格和相关 skills。
- 不修改 `app/**`、公开 `/chat` contract、RepoPilot runtime permission/approval、provider、持久化、网络、CI 或产品级 commit/merge/push 能力。
- 阶段按 `high / L3` 处理，因为它改变人工授权与 Git closeout 的失败语义；实现前需要完整 design/tasks/spec 人工确认、内部评审和两个空上下文独立 plan-review slots。
