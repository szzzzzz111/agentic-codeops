# harness-development-workflow Specification

## Purpose

记录 RepoPilot 仓库的阶段化开发、OpenSpec 规格入口、Harness 写入边界、验证和交接规则。
## Requirements
### Requirement: 仓库使用阶段化开发流程

仓库 SHALL 一次只开发一个小阶段，并且 MUST 保持阶段 scope 明确。

#### Scenario: 新阶段开始

- **WHEN** 新阶段开始
- **THEN** Agent 在修改文件前确认分支、工作区状态和当前阶段

### Requirement: allowed files 定义写入范围

仓库 SHALL 维护 `.harness/allowed_files.md` 作为当前阶段写入边界。

#### Scenario: 实现开始

- **WHEN** Agent 开始实现
- **THEN** 只编辑 `.harness/allowed_files.md` 允许的文件

### Requirement: review checklist 定义验收风险

仓库 SHALL 维护 `.harness/review_checklist.md` 作为当前阶段 review 标准。

#### Scenario: 进行 review

- **WHEN** 变更被 review
- **THEN** reviewer 检查 scope、允许文件、测试、文档、架构边界和 Roadmap 准确性

### Requirement: 验证使用确定性命令

仓库 SHALL 优先使用 `scripts/verify.ps1`、pytest 和 ruff 进行确定性验证。

#### Scenario: 变更完成

- **WHEN** 变更准备 review 或合并
- **THEN** 运行 `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`，或记录无法运行的原因

### Requirement: handoff 和 progress 保持最新

仓库 SHALL 在有意义的工作结束时更新 `docs/PROGRESS.md` 和 `HANDOFF_TO_NEXT_CHAT.md`。

#### Scenario: 工作 session 结束

- **WHEN** 阶段状态变化或实现完成
- **THEN** progress 和 handoff 文档记录分支、完成内容、验证、未完成事项和下一步建议

### Requirement: OpenSpec 是项目级开发流程

仓库 SHALL 在规划重要新阶段时使用 OpenSpec 管理 proposal、design、tasks、specs 和 archive。

#### Scenario: 规划重要新阶段

- **WHEN** 新的重要阶段被规划
- **THEN** Agent 在实现前创建或更新 OpenSpec change

### Requirement: OpenSpec 不等于运行时能力

OpenSpec、Superpowers、MCP、plugin 和外部 skill 概念 MUST NOT 被视为 RepoPilot 运行时能力，除非阶段 spec 明确开放该 scope。

#### Scenario: 存在 OpenSpec 工作流

- **WHEN** 仓库存在 OpenSpec 文件或项目级 AI skills
- **THEN** 应用运行时行为不因此改变，除非专门的产品 spec 要求改变

### Requirement: OpenSpec specs 是长期规格入口

仓库 SHALL 使用 `openspec/specs/` 作为长期规格入口。旧 `specs/00x-*` 迁移完成后 MUST NOT 继续作为当前规格入口维护。

#### Scenario: Agent 查找长期规格

- **WHEN** Agent 需要查看当前已验收能力规格
- **THEN** Agent 读取 `openspec/specs/` 中的 capability specs

#### Scenario: 旧 specs 已退役

- **WHEN** Agent 看到历史迁移记录
- **THEN** Agent 将旧 `specs/00x-*` 视为已迁移来源，而不是当前可编辑规格入口

### Requirement: 后续阶段采用轻量工程化路线

项目 SHALL 优先通过清晰边界、结构化审计、确定性验证、可替换接口和交接文档体现工程化。项目 MUST NOT 为了“看起来工程化”而在无明确阶段需求时引入重型基础设施。

V18 Patch + Verify Loop SHALL 使用现有 `/chat` 入口、明确组合确认、pending patch apply、白名单验证命令、权限审批边界和受控 `patch_apply` / `verification_run` 工具串联一次 apply 后 verify。V18 MUST NOT 新增公开 API、新增 `/chat` 顶层字段、开放任意 shell、支持用户自定义验证参数、根据失败自动生成 patch、持久化验证结果、自动 commit、创建 worktree、调度真实 subagents、执行后台任务或实现 Persistent Audit / Recovery。

#### Scenario: V18 受控 Patch + Verify Loop 阶段

- **WHEN** V18 实现 Patch + Verify Loop
- **THEN** 系统通过 `/chat.answer` 返回组合结果摘要
- **AND** 系统保持 `/chat` contract 和现有 Harness 权限边界
- **AND** review checklist MUST 检查组合确认优先级、半解析拒绝、命令白名单、独立 verification context、失败门、输出脱敏、contract 和 non-goals

### Requirement: Stage Debt Sweep Is A Checkable Gate

系统 SHALL require an explicit Stage Debt Sweep before a stage is called implementation-complete, ready to commit, archive-ready, merged, pushed, or ready for the next stage.

The Stage Debt Sweep MUST scan current durable docs, harness docs, active OpenSpec artifacts, long-term specs, changed runtime paths, and adjacent older runtime paths. Discoverable debt MUST be fixed in scope or recorded in durable docs with severity, deferral rationale, and intended follow-up. Blocking debt MUST stop closeout or the next stage. Debt MUST NOT remain only in chat.

Deterministic scripts SHALL cover mechanically searchable debt where practical, but passing scripts, tests, or
checklists MUST NOT be treated as evidence that the manual code/test debt review of changed and adjacent paths
has completed.

#### Scenario: Stage Debt Sweep evidence is durable

- **WHEN** a stage reaches review or closeout
- **THEN** `docs/PROGRESS.md`, `HANDOFF_TO_NEXT_CHAT.md`, and `.harness/review_checklist.md` include checkable Stage Debt Sweep evidence or blockers

#### Scenario: Script gates do not replace manual debt review

- **WHEN** deterministic stage checks pass
- **THEN** the reviewer still manually inspects changed runtime/tests and adjacent older paths
- **AND** remaining findings are fixed in scope or recorded in durable docs

### Requirement: Manual Judgment Gates Remain Human-Reasoned

系统 SHALL require visible manual judgment conclusions before implementation confirmation and before stage
closeout. The required judgment categories are stage intent/scope, safety/architecture, test adequacy, review
triage, semantic documentation parity, and archive/merge/handoff truth.

Deterministic validation, tests, scans, and checklist markers MAY prove that evidence exists, but MUST NOT be
treated as proof that these semantic judgments are correct.

#### Scenario: Planning validation does not prove plan quality

- **WHEN** an OpenSpec change passes validation
- **THEN** the reviewer still assesses intent, scope, non-goals, safety boundaries, and planned test adequacy

#### Scenario: Closeout scripts do not prove semantic correctness

- **WHEN** tests and closeout scripts pass
- **THEN** the reviewer still records visible conclusions for all manual judgment categories
- **AND** unresolved blocking findings stop closeout or the next stage

### Requirement: Post-Merge Durable Docs Reflect Actual State

系统 SHALL update durable docs after merge/push with the actual main/remote state, commit hash, validation evidence, next stage recommendation, and feature branch cleanup/retention decision.

#### Scenario: Merge/push closeout does not leave stale next steps

- **WHEN** a stage has been merged and pushed
- **THEN** durable docs MUST NOT continue to describe merge/push as a future decision for that completed stage
- **AND** durable docs MUST record whether the feature branch was retained or cleaned up

### Requirement: Process Skills Are Not Runtime Capabilities

系统 SHALL treat local `.codex/skills/**` edits as development process documentation only unless a future stage explicitly makes a runtime capability. V19 MUST NOT describe Stage Debt Sweep, handoff skills, OpenSpec skills, Superpowers, MCP, or plugins as RepoPilot runtime behavior.

#### Scenario: Skill boundary remains process-only

- **WHEN** `.codex/skills/repo-stage-review-loop/SKILL.md` or `.codex/skills/repo-stage-handoff/SKILL.md` is edited during V19
- **THEN** the change is documented as process discipline only
- **AND** runtime docs MUST NOT list it as a product feature

### Requirement: V20 Preserves Main Workspace Semantics

V20 SHALL isolate RepoPilot-owned patch mutation from the user's main working tree while preserving standalone verification semantics. Standalone verification MUST continue to inspect the current repository working tree and MUST NOT be forced into an isolated worktree.

#### Scenario: Standalone verification remains main-worktree scoped

- **WHEN** the user sends an explicit standalone verification request
- **THEN** the system runs verification against the request repo path
- **AND** it MUST NOT create a worktree first

### Requirement: V21 Planning And Implementation Remain Separately Confirmed

V21 SHALL complete stage planning, OpenSpec artifacts, harness synchronization, internal plan review, and OpenSpec validation before runtime or test implementation begins.

The implementation MUST remain limited to read-only worktree inventory / inspection and MUST NOT include V22-V24 re-verification, disposal/reconciliation, or promotion behavior.

#### Scenario: Planning stops before runtime implementation

- **WHEN** the V21 planning artifacts validate successfully
- **THEN** the stage stops at the implementation confirmation gate
- **AND** runtime code and tests remain unchanged until explicit confirmation

### Requirement: Continuous Authorization Does Not Remove Formal Review

用户对实现、提交、归档、合并或推送的连续执行授权 SHALL reduce only intermediate stage-level
confirmation prompts. It MUST NOT remove or weaken formal code review, Stage Debt Sweep, deterministic
validation, archive review, merge review, or post-merge verification.

Formal code review MUST run after the final runtime/test changes and before archive/merge, and MUST produce a
visible severity-ordered findings report or an explicit no-findings conclusion with residual risks. Passing tests,
incremental self-checks, and checked task/checklist items MUST NOT be treated as equivalent evidence.

#### Scenario: Merge authorization preserves review gates

- **WHEN** the user authorizes execution through merge or push
- **THEN** the agent still performs and reports formal code review before archive/merge
- **AND** unresolved P0/P1 findings block archive/merge or reopen closeout if discovered afterward

#### Scenario: Post-merge P1 reopens closeout

- **WHEN** formal review after merge discovers a P1 finding
- **THEN** `.harness/review_checklist.md`, `docs/PROGRESS.md`, and `HANDOFF_TO_NEXT_CHAT.md` record the blocker
- **AND** the next stage remains blocked until remediation, re-review, and verification complete

### Requirement: V22 Planning And Implementation Remain Separately Confirmed

V22 SHALL complete stage planning, OpenSpec artifacts, harness synchronization, internal plan review, and OpenSpec validation before runtime or test implementation begins.

The implementation MUST remain limited to retained worktree re-verification and MUST NOT include disposal/reconciliation, promotion, patch mutation, cleanup, commit, merge, or push behavior.

#### Scenario: Planning stops before runtime implementation

- **WHEN** the V22 planning artifacts validate successfully
- **THEN** the stage stops at the implementation confirmation gate
- **AND** runtime code and tests remain unchanged until explicit confirmation

### Requirement: V23 Planning And Implementation Remain Separately Confirmed

V23 SHALL complete stage planning, OpenSpec artifacts, harness synchronization, internal plan review, and strict OpenSpec validation before runtime or test implementation begins.

The implementation MUST remain limited to explicit worktree disposal/reconciliation and blocking adjacent metadata/store hardening. It MUST NOT include promotion, patch mutation/reapply, implicit repair, automatic retry, commit, merge, push, arbitrary shell, background tasks, subagents, connectors, or frontend behavior.

#### Scenario: Planning stops before implementation

- **WHEN** V23 planning artifacts pass internal review and validation
- **THEN** the stage stops at the implementation confirmation gate
- **AND** runtime code and tests remain unchanged until explicit confirmation
