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

### Requirement: Progress And Handoff Have Separate Ownership

仓库 SHALL 只在文档拥有的事实发生变化时更新文档。`docs/PROGRESS.md` MUST 记录长期能力、
重要决策、验证证据和未清债务；`HANDOFF_TO_NEXT_CHAT.md` MUST 只记录下一 session 安全行动所需的
当前上下文、阻塞和下一步。

#### Scenario: Session does not change durable or handoff facts

- **WHEN** a work session does not change facts owned by PROGRESS or HANDOFF
- **THEN** the agent MUST NOT update those documents only to satisfy a ritual

#### Scenario: Stage reaches final integrated state

- **WHEN** archive, merge, push, and optional branch cleanup are complete
- **THEN** the repository records one final handoff instead of separate near-duplicate updates after each action

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

### Requirement: Stage Debt Sweep Is Focused And Checkable

系统 SHALL require an explicit Stage Debt Sweep before archive readiness. The sweep MUST inspect changed runtime
and test paths, older paths they directly call or share state with, and documents whose owned facts changed.
It MUST record inspected paths, findings, dispositions, and residual risks. The sweep MUST NOT require an
unbounded repository-wide scan without a concrete dependency or finding.

Discoverable debt MUST be fixed in scope or recorded in `docs/PROGRESS.md` with severity, deferral rationale,
and intended follow-up. A debt item belongs in `HANDOFF_TO_NEXT_CHAT.md` only when it affects the next session's
safe action. Blocking debt MUST stop closeout or the next stage. Debt MUST NOT remain only in chat.

Deterministic scripts SHALL cover mechanically searchable debt where practical, but passing scripts, tests, or
checklists MUST NOT be treated as evidence that the manual code/test debt review of changed and adjacent paths
has completed.

#### Scenario: Stage Debt Sweep evidence is durable

- **WHEN** a stage reaches review or closeout
- **THEN** `.harness/review_checklist.md` includes checkable scope and disposition evidence
- **AND** unresolved durable debt is recorded in `docs/PROGRESS.md`

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

### Requirement: Final Handoff Uses Live Repository Facts

系统 SHALL verify actual branch, remote, commit, archive, and active-change state using Git and OpenSpec commands.
Durable docs MUST NOT duplicate volatile current-HEAD or remote hash claims across multiple files.

#### Scenario: Merge/push closeout does not leave stale next steps

- **WHEN** a stage has been merged and pushed
- **THEN** one final handoff MUST NOT continue to describe merge/push as a future decision
- **AND** exact repository state is queried live when the next session needs it

### Requirement: Current Documentation Facts Have Narrow Ownership

RepoPilot documentation SHALL avoid duplicating volatile current-stage facts across multiple durable files. Each
current-facing document MUST keep to its owned fact type:

- `README.md` owns the human-facing project facade, current capability snapshot, quick start, and links to deeper docs.
- `docs/ARCHITECTURE.md` owns stable runtime boundaries and durable relationships between components.
- `docs/PROGRESS.md` owns stage history, durable decisions, validation evidence, and unresolved debt.
- `docs/AGENT_RULES.md` owns long-term collaboration, branch, review, debt sweep, and documentation ownership rules.
- `HANDOFF_TO_NEXT_CHAT.md` owns next-session action context, blockers, and safe next steps.
- `docs/FEATURE_LIST.json` owns acceptance-oriented capability inventory and pass/fail status.
- `.harness/allowed_files.md` and `.harness/review_checklist.md` own the active stage write boundary and review gate evidence.

#### Scenario: Stage closeout updates current facts

- **WHEN** a stage is archived, merged, pushed, or otherwise changes current stage state
- **THEN** the agent updates only documents whose owned facts changed
- **AND** it avoids repeating the same volatile status in unrelated documents

#### Scenario: Architecture document references recent stages

- **WHEN** `docs/ARCHITECTURE.md` mentions a recent stage
- **THEN** the wording describes stable architecture boundaries or implemented runtime relationships
- **AND** it does not describe transient implementation tasks as current work

### Requirement: Volatile Repository State Comes From Live Commands

RepoPilot SHALL treat Git and OpenSpec commands as the source of truth for branch, HEAD, remote sync, and active
OpenSpec change state. Durable documents MUST NOT require repeated exact HEAD or remote hash updates across multiple
files.

#### Scenario: Next session needs current repository state

- **WHEN** an agent starts or resumes a stage
- **THEN** it checks live `git status --short --branch`, recent commits, remote sync when needed, and `openspec list`
- **AND** it does not rely on stale prose as proof of current Git/OpenSpec state

### Requirement: Drift Checks Target Current Facts Without Rewriting History

RepoPilot deterministic documentation checks SHALL target current-state files and current guidance sections for
mechanically searchable stale wording. They MUST NOT treat archived OpenSpec changes or historical PROGRESS entries
as current truth merely because they contain old stage wording.

#### Scenario: Stale wording appears in current guidance

- **WHEN** README, HANDOFF, Harness files, FEATURE_LIST notes, or the current PROGRESS guidance describe a completed
  stage as future, pending, unmerged, or backlog
- **THEN** the stage docs scan fails with a clear finding

#### Scenario: Historical archive contains old roadmap wording

- **WHEN** an archived OpenSpec change or historical PROGRESS entry contains wording that was true for that past stage
- **THEN** deterministic drift checks do not fail solely because of that historical wording

### Requirement: Stage Workflow Is Risk-Scaled

系统 SHALL classify each stage as low, medium, or high risk before implementation. Risk level MUST control review
depth and external-review expectations, but MUST NOT remove TDD, deterministic validation, or safety boundaries.

For ordinary narrow stages, the agent SHALL read the full OpenSpec artifacts and present the user with a concise
Chinese summary, risk level, touched file families, non-goals, and implementation confirmation gate. The user is not
required to read every proposal/design/tasks/spec line unless the stage is high risk, changes public/runtime behavior,
has fuzzy product terminology, or the user explicitly asks for full detail.

For themes prone to scope inflation or roadmap confusion, including MCP, Skill, subagent, connector, runtime plugin,
background worker, durable execution, or always-on assistant, the workflow SHOULD run a lightweight Grilling Gate before
OpenSpec drafting. The gate SHOULD clarify canonical terms, counterexamples, runtime availability, approval/audit
boundaries, and non-goals. It MUST remain a planning discipline and MUST NOT turn process skills into runtime
capabilities by itself.

#### Scenario: High-risk stateful stage

- **WHEN** a stage changes Git/subprocess execution, persistence, permissions, patch lifecycle, or public API contracts
- **THEN** the workflow requires internal review and independent adversarial external review

#### Scenario: Low-risk process-only stage

- **WHEN** a stage changes only development documentation, local skills, or deterministic process checks
- **THEN** internal review and relevant structural validation are sufficient unless external review is requested

#### Scenario: Narrow stage uses summary approval

- **WHEN** an ordinary narrow stage reaches implementation confirmation
- **THEN** the agent summarizes the OpenSpec baseline instead of requiring user line-by-line review
- **AND** product, workflow, risk, or scope decisions are still escalated to the user

#### Scenario: Fuzzy runtime-adjacent stage uses Grilling Gate

- **WHEN** a stage uses ambiguous terms such as MCP, Skill, connector, subagent, or runtime plugin
- **THEN** the workflow clarifies what is runtime-available, development-only, explicitly out of scope, and auditable before implementation planning

### Requirement: V24 CLI Surface Replaces Previous Promotion Slot

RepoPilot SHALL treat V24 as the CLI Capability Surface / Demo-ready Product Surface stage. The previous Verified Patch Promotion roadmap item MUST be moved to V25 or backlog and MUST NOT be implemented or documented as implemented by this stage.

#### Scenario: V24 planning updates roadmap truth

- **WHEN** V24 CLI Capability Surface planning artifacts and docs are updated
- **THEN** README, ARCHITECTURE, PROGRESS, HANDOFF, and relevant specs MUST avoid using V24 to mean Verified Patch Promotion
- **AND** Verified Patch Promotion MUST be described only as a future candidate

### Requirement: Plan Review Gates Precede Implementation

Medium and high risk RepoPilot stages SHALL complete plan-level review before runtime or test implementation begins.

Plan-level review MUST include internal plan review, two independently instantiated plan-review slots, and triage of all findings. Passing OpenSpec validation MUST NOT be treated as plan review. Reviewer provider or product identity MUST NOT be the sole reason a review slot passes or fails.

Each first-round independent reviewer MUST be distinct from the implementer and the other independent reviewer, MUST review the same frozen plan baseline, MUST NOT inherit the implementation conversation, and MUST NOT read the other first-round review conclusion before producing its own conclusion. A Codex reviewer MAY satisfy either independent slot through a new empty-context task or a subagent invocation that explicitly disables parent-context inheritance. A Codex task/subagent with inherited implementation context or unverified context mode MUST NOT satisfy an independent review slot.

Each independent review record MUST identify stage/phase/slot id, implementer instance identity, reviewer provider/model/instance identity, host-reported context inheritance mode, an immutable reviewed Git/tree or packet-manifest ref and artifact hashes, whether other first-round conclusions were visible, final findings or an explicit no-findings conclusion, finding disposition/closure, remediation lineage when applicable, and residual uncertainty. Remediation lineage MUST resolve a content-hashed original first-round receipt and MUST bind the original slot, reviewer, and finding IDs. Different providers or models MAY add diversity evidence, but MUST NOT replace the context and instance independence requirements. A deterministic validator MUST reject mechanically observable identity collisions, duplicate slots/reviewers, declared inherited or unknown context, declared first-round cross-review visibility, noncanonical/mutable/mismatched baselines, missing artifact hashes, stale post-remediation receipts, unresolved lineage, contradictory or open final conclusions, and incomplete records.

Actual review sets MUST be stored at `.harness/reviews/<stage-id>/<phase>/review-set.json` and validated with `scripts/validate_independent_review.py` against explicit expected stage, phase, and required-slot count. The validator MUST recompute reviewed artifact hashes and the content-addressed packet hash from canonical project-relative files, emit structured errors, and exit nonzero on any mechanical defect. It MUST label its claim `mechanical_consistency_only`, MUST NOT claim that repository-authored fields prove host dispatch provenance or activation chronology, and MUST leave `gate_ready=false`. The host controller MUST separately verify native reviewer/implementer dispatch identity, parent-context inheritance and first-round visibility, while the pre-change process authority MUST verify activation sequence. A receipt set that is missing, was not passed to the validator, returned nonzero, or lacks either required external check MUST NOT contribute any completed review slot.

When a stage introduces this validator or another new review gate, activation timing MUST remain owned by the pre-change process authority and MUST occur only after implementation, negative tests, and workflow wiring pass. The receipt MUST bind a project-relative activation record and its hash; the validator MAY verify record integrity but MUST NOT claim to prove chronology. The introducing stage's earlier plan review MUST remain governed by the pre-change review contract and frozen review evidence; the workflow MUST NOT retroactively claim that the not-yet-created validator ran before implementation. Once activated, the new gate MUST govern the introducing stage's final implementation review and all subsequent applicable plan/final independent reviews.

#### Scenario: Implementation waits for two independent plan reviews

- **WHEN** a medium or high risk stage reaches the implementation confirmation gate
- **THEN** internal plan review MUST check proposal, design, tasks, spec deltas, test plan, and Harness boundaries
- **AND** two distinct independent reviewer instances MUST each return severity findings or an explicit no-findings conclusion against the same frozen baseline
- **AND** all plan findings MUST be classified as `fix`, `clarify`, `reject`, or `defer`

#### Scenario: Codex replaces an OpenCode review slot

- **WHEN** a required independent plan-review slot is assigned to Codex instead of OpenCode
- **THEN** the reviewer MUST use a new empty-context task or a subagent with parent-context inheritance explicitly disabled
- **AND** inherited or unverified context MUST keep the independent review gate open

#### Scenario: First-round reviewers remain blind to each other

- **WHEN** two independent reviewers inspect the first frozen plan baseline
- **THEN** neither reviewer MUST receive the other reviewer's findings before producing its own first-round conclusion
- **AND** repeating another reviewer's conclusion MUST NOT count as independent counterexample evidence

#### Scenario: Re-review preserves finding lineage

- **WHEN** implementation or plan artifacts change to remediate an existing finding
- **THEN** the original reviewer session MAY be reused to verify closure of that finding
- **AND** the reused session MUST continue to occupy only its original review slot and MUST NOT be counted as an additional independent reviewer
- **AND** remediation lineage MUST resolve a content-hashed original first-round receipt with the same slot/reviewer and the referenced finding IDs
- **AND** every required slot MUST issue a final receipt against the same final content-addressed baseline before the gate closes

#### Scenario: OpenCode adapter timeout is not a verdict

- **WHEN** an OpenCode adapter command times out or does not print a final result
- **THEN** the agent MUST inspect the relevant OpenCode session for final assistant review text before marking that adapter attempt failed
- **AND** missing final review text keeps that slot open until the same attempt is recovered or another independently instantiated reviewer satisfies it; adapter unavailability MUST NOT reduce the required slot count

#### Scenario: OpenCode first-round review uses an isolated session

- **WHEN** OpenCode is assigned a first-round independent review slot
- **THEN** it MUST use a new isolated review session or provide host evidence that a candidate session contains no implementation conversation or other first-round conclusion
- **AND** ordinary session reuse MUST be limited to timeout recovery of the same attempt or remediation re-review for the same slot

#### Scenario: Review evidence proves independence

- **WHEN** an independent plan review is recorded as complete
- **THEN** its validated receipt MUST identify implementer and reviewer identities, slot, host-reported context mode, immutable frozen ref and artifact hashes, conclusion visibility, final conclusion, lineage, and residual uncertainty
- **AND** repository validation MUST remain mechanical-only while the host controller separately verifies native dispatch provenance
- **AND** provider/model diversity without context isolation MUST NOT satisfy the gate

#### Scenario: Review gate consumes the actual receipt set

- **WHEN** a workflow attempts to count required independent review slots
- **THEN** it MUST run the independent-review validator against the actual stage/phase receipt set with the risk-contract required-slot count
- **AND** missing invocation, missing receipts, stale packet hashes, nonzero validation, missing host dispatch verification, or missing activation-sequence verification MUST keep the review gate open

#### Scenario: Newly introduced review gate does not self-bootstrap

- **WHEN** a process change implements a new independent-review validator or gate
- **THEN** the change's pre-implementation plan review MUST use and preserve the pre-change review contract and frozen evidence
- **AND** the pre-change process authority MUST own and record activation only after implementation and negative verification, beginning with that change's final review and subsequent applicable reviews
- **AND** the repository validator MUST NOT claim that a declarative activation field proves that chronology
- **AND** later validation MUST NOT be reported as if it preceded implementation

### Requirement: External Review Seeks Independent Counterexamples

独立 review SHALL target failure modes not already covered by task completion reporting. Findings SHOULD include severity, location, trigger, consequence, and a suggested regression test. External feedback MUST be classified as `fix`, `clarify`, `reject`, or `defer` against repository evidence.

The same reviewer-slot independence contract SHALL apply to every independent slot required by plan review or final implementation review. Medium/high plan review retains two independent slots; final implementation review slot count remains defined by the stage risk contract. A first-round reviewer MUST inspect a frozen review packet without inherited implementation conversation or another first-round reviewer conclusion. A remediation re-review MAY reuse the original reviewer session to preserve finding lineage, but that reused session MUST NOT create an additional independent slot. After remediation, every required slot's final receipt MUST bind the same final content-addressed baseline.

Code review SHALL assess layered concerns: scope, business logic, architecture boundaries, minimality, failure semantics, security/privacy, test adequacy, and maintainability. The agent SHALL own low-level implementation review by default and translate findings into user-facing Chinese summaries when the user needs to judge product behavior, workflow semantics, risk acceptance, or residual risk.

#### Scenario: External review repeats implementation status

- **WHEN** independent feedback only repeats tasks, passing tests, implementation status, or another first-round review conclusion without an independent failure hypothesis
- **THEN** it MUST NOT be treated as meaningful diversity evidence

#### Scenario: Final implementation reviewer uses an isolated instance

- **WHEN** a stage requires independent final implementation review
- **THEN** every required first-round reviewer slot MUST use a distinct instance with no inherited implementation conversation and review the same frozen final code/test packet
- **AND** a Codex empty-context task or parent-context-disabled subagent MAY satisfy any required slot regardless of whether OpenCode is available
- **AND** remediation MUST refresh every required slot's final receipt to the same final baseline before the final review gate closes

#### Scenario: User-facing review summary explains terms

- **WHEN** review results include non-obvious engineering terms
- **THEN** the summary keeps the precise term and adds a short Chinese explanation or concrete example

#### Scenario: Independent reviewer reports findings

- **WHEN** an independent reviewer reports plan or implementation findings
- **THEN** each finding MUST be classified as `fix`, `clarify`, `reject`, or `defer`
- **AND** accepted fixes or clarifications MUST be reflected in the reviewed artifacts before the relevant gate closes

### Requirement: Archive Freezes Reviewed Runtime

Archive readiness SHALL apply to the reviewed runtime/test state. A runtime or test correction after formal review
or archive MUST invalidate stale review evidence and reopen affected verification and review gates.

#### Scenario: Runtime changes after archive

- **WHEN** a runtime defect is discovered and fixed after archive
- **THEN** the repository reruns affected verification and formal review
- **AND** the change is not treated as handoff-only cleanup

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
- **THEN** `.harness/review_checklist.md` and `docs/PROGRESS.md` record the blocker
- **AND** `HANDOFF_TO_NEXT_CHAT.md` records it when it changes the next session's safe action
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

### Requirement: README Facade And CLI Planning Stop Before Runtime Implementation

The stage SHALL optimize README first-viewport positioning and create Demo-ready Agent CLI planning artifacts before any runtime implementation work begins.

The stage MUST keep README truthfulness, OpenSpec artifacts, and Harness boundaries aligned. It MUST NOT modify runtime code, tests, provider runtime, live eval profiles, default Patch wiring, default CI, `/chat` public contract, or V24 behavior without a later explicit user confirmation and updated harness scope.

#### Scenario: Planning confirmation gate

- **WHEN** OpenSpec artifacts and harness boundaries are synchronized for `demo-ready-readme-cli-planning`
- **THEN** the stage stops at the planning confirmation gate
- **AND** README content edits require explicit user confirmation
- **AND** runtime or CLI implementation remains out of scope

### Requirement: CLI Implementation Stays Inside Existing Runtime Boundaries

The Demo-ready Agent CLI implementation SHALL be planned and reviewed as a medium-risk user-facing command surface.

It MUST use TDD, update Harness boundaries before runtime/test edits, and preserve existing `/chat`, AgentLoop, ToolExecutor, PermissionPolicy, ApprovalGate, VerificationRunner, Worktree, Audit, provider, and CI boundaries. It MUST NOT introduce Verified Patch Promotion, arbitrary shell execution, network dependency, background tasks, subagents, connectors, commit/merge/push automation, or real model patch provider wiring.

#### Scenario: CLI implementation starts after planning gate

- **WHEN** `add-demo-ready-agent-cli` planning artifacts validate successfully
- **THEN** implementation remains blocked until explicit confirmation
- **AND** allowed files and review checklist define the CLI runtime/test/doc scope

#### Scenario: CLI closeout requires command-surface review

- **WHEN** CLI implementation is complete
- **THEN** review MUST check parser safety, command mapping, exit codes, output redaction, no new network dependency, no `/chat` contract change, and no bypass of existing patch/verification confirmation boundaries

### Requirement: Workflow Skills Keep Specification And Execution Roles Separate

RepoPilot repo-local workflow skills SHALL distinguish specification baseline work from execution discipline.
OpenSpec SHALL own requirement clarification, interface/model/design decisions, task decomposition, spec review,
requirement changes, and archive. Execution-discipline skills SHALL own reading the approved baseline,
isolated development where needed, TDD, deterministic verification, code review, finishing, and skill/process
self-checks.

Workflow documentation MUST NOT describe OpenSpec, Superpowers, Codex/OpenCode skills, MCP, plugins, or
connectors as RepoPilot runtime capabilities unless a future runtime OpenSpec change explicitly opens that scope.

#### Scenario: Requirement changes during implementation

- **WHEN** implementation reveals a requirement change, design contradiction, or scope drift
- **THEN** the workflow returns to OpenSpec planning or exploration before implementation resumes
- **AND** the execution plan is regenerated or updated from the new approved baseline

#### Scenario: Process-only workflow update

- **WHEN** a change edits only repo-local workflow skills and owned process documents
- **THEN** risk may be classified as low
- **AND** validation and review focus on process clarity, scope truth, roadmap truth, and document ownership
- **AND** runtime files and public product contracts remain out of scope
