## Why

RepoPilot 现在能在阶段 envelope 漂移时拒绝继续执行，但还没有一份机器可验证的 change intake 记录说明“什么变了、哪些既有证据失效、必须从哪一个最早 gate 重放”。缺少这层会让中途修正依赖聊天记忆，容易出现全量重做、漏重放或拿旧 review/verification 继续 closeout。

## What Changes

- 新增 development-only 的 dormant stage change intake、gate lifecycle snapshot、append-CAS event/receipt lineage 和 replay plan 合同，为未来已激活 v2 cohort 以无哈希环顺序绑定被取代的 authority、所需 later epoch、change event、authority v2、受影响 inputs、失效原因和必须重放的 gate 集合；不改变 v1 cohort 现有 later-v1 恢复路径。
- 使用显式 V1 linear gate graph和完整 fact-to-suffix mapping计算最早可辩护 frontier；不得写死 `resume_step=1`、自报更晚恢复点或添加特殊跳边。
- 将 scope、non-goal、risk、planning base、action ceiling、endpoint、branch、tip 和 review-subject drift 映射到确定性保守失效 suffix；只有 seed 前且 host snapshot/adapter证明未变的 prefix evidence可保留。
- 用 code-owned per-gate evidence adapters 阻止任意 hash 文件自证 review/verification completion，并用 authority/delivery schema v2 统一 `archive -> commit(candidate)` 顺序。
- 定义 stage authority 与 end-to-end development workflow 的 replay 接入合同：激活后，apply/archive/commit(candidate)/merge/push 只能在 requested action 精确等于 current frontier 时继续。本 change 交付 repository-local mechanical validator 和未激活接线；真实 blocking activation 以后续 provider-neutral host CAS capability 为前置，不把 CLI/repo 自报冒充宿主能力。
- 保持 OpenSpec、skills、receipts 和 replay validator 为仓库开发流程能力；不新增 RepoPilot runtime change-event、后台调度、runtime subagent、自动 commit/merge/push 或公开 API。

## Capabilities

### New Capabilities

- `stage-change-replay`: 定义阶段中途变化的来源绑定、证据失效、依赖驱动 replay、恢复点和闭合判定。

### Modified Capabilities

- `stage-authority-binding`: 对未来已激活 v2 cohort，authority epoch 变化还要绑定 change event 与待重放证据；introducing/in-flight v1 cohort 仍用 pre-change later-v1 record，不要求 event。
- `harness-development-workflow`: 已激活 v2 cohort 在实现期发生 requirement/scope/design drift 时，必须先完成 change intake、失效和所需 replay；v1 cohort 仍按 pre-change stop、later authority 与重验流程恢复。

## Impact

- Process code: `scripts/validate_stage_change_replay.py`、stage authority validator 的 snapshot/CAS/replay preflight 接线。
- Tests: 新 validator 的 fail-closed/negative cases，以及 apply/archive/merge/push workflow structural tests。
- Workflow assets: Repo-local Codex/OpenCode apply、archive、review、handoff 和 end-to-end stage skills/commands；默认仍走 pre-change gate，未满足外部 host capability 前不声称 replay 已激活。
- Harness/OpenSpec: 新 replay templates、保留的 active v1 authority/delivery templates、独立 dormant v2 templates、active stage allowed/review boundaries、三份 capability specs 和本 change artifacts。
- Runtime/API/dependencies: 不修改 `app/**`、公开 `/chat` contract、provider runtime、持久化 schema 或网络依赖。
