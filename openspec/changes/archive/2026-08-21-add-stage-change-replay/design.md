## Context

`stage-authority-binding` 已经把 live human authority 与 repository-local mechanical binding 分开，并在 scope、risk、base、target 或 review subject 漂移时 fail closed。当前缺口是 fail 后没有一份闭合合同回答：变化事件是否属于原 envelope、哪些已完成 gate 变 stale、哪些证据可证明未受影响、需要重放哪些 gate，以及恢复执行的最早 frontier 是什么。

历史材料给出的有效原则是“变化后精确失效并重放”，但不能直接复制固定 `resume_step=1`、自写 event 继承旧批准或把 replay receipt 当作用户授权。本设计把 replay 限定为 development workflow evidence，并继续让 direct-user authority、technical readiness 和 Git delivery verdict 相互独立。

本 change 基于 `bd66dba26f245de6a49999dfde14006d0474ab25` 规划。它不修改 `app/**`，不新增公开 API、runtime event bus、后台 worker、runtime subagent、provider/network dependency 或产品级 Git 自动化。

## Goals / Non-Goals

**Goals:**

- 为阶段中的 material change 建立 append-only、content-addressed change-event lineage。
- 通过版本化 gate dependency graph 重算 invalidated、preserved、required replay 和 replay frontier，而不是信任手写 resume step。
- 让 retained evidence 必须证明其 inputs 与 dependency closure 未变化；不能只写 `preserved=true`。
- 区分 direct-user envelope change、Agent-owned technical correction、review remediation 和 repository/Git drift，避免把技术决定升级为 owner 问题。
- 机械定义未来激活后 implement/archive/commit/merge/push 在 changed lineage 下只能精确命中 current frontier；本 change 不把该模型升格为已激活 action gate。
- V1 只保留 earliest seed 之前、且 host snapshot 证明输入未变的 prefix evidence；宁可保守重放，不用特殊跳边制造不一致的“最小集合”。

**Non-Goals:**

- 不从自然语言自动判断产品语义是否变化；语义分类仍由 host/controller 和 review 负责。
- 不让 repository event、hash 或 replay receipt 证明 user identity、message authenticity、chronology 或 `human_authorized=true`。
- 不允许 Agent-authored event 扩大 scope、risk、non-goals、action ceiling 或 Git target 后继承旧 authority。
- 不实现 runtime change ingestion、durable/background execution、runtime subagent、通知、cron、PR 或自动 commit/merge/push。
- 不把 replay progress 变成第三个 final-review evidence-tail 文件；pre-tail receipt 必须在 final packet 冻结前进入 reviewed subject，tail/live facts只在 action validation 时组合。
- 不在已验证 push 后继续追加同一 stage event；后续需求必须开始新 stage。

这里的 material change 不是“阶段内每一次按已批准计划进行的正常编辑”。只有某个已闭合或已绑定的 gate input
随后发生变化，或一个声明过的 transition 产生了合同外输出，才追加 event。仍处于 open 状态的初始实现编辑、
按合同生成的 archive move、candidate commit、ff-only merge 和 push 本身由原 gate 顺序消费，不重复包装成 change event。

## Decisions

### 1. Repository validation consumes a bounded controller context; blocking activation remains external

Repository validator 接受版本化 `controller_stage_context/v1`，其机械字段包含：stage terminal state、每个
gate 的 lifecycle/input snapshot、event/receipt prior 与 current count/head，以及 immutable workspace binding。`0 + none`
只表示 repository lineage 为空；它必须与 supplied closed/bound gate snapshots 和 live adapter inputs 全部一致后，
才能得到 `mechanical_consistency_only`。Repository writer、receipt 或聊天摘要不能把 changed input 重新标成
open 来绕过 event。

该 context 的 provenance 无法由 repository validator 从 CLI 参数反证。因此本 change 不宣称现有 Codex/OpenCode
已提供 durable host adapter，也不激活 blocking replay gate。默认 entrypoint 仍使用 pre-change v1 流程；只可运行
shadow/mechanical replay 检查，且 PASS 不得授权 mutation。未来真实激活的外部前置固定为
`provider_neutral.stage_state_cas/v1`：宿主必须实现 `load(stage_key)`、原子
`compare_and_swap(stage_key, expected_generation, expected_heads, next_state)`、
`recover(stage_key, workspace_binding)`、`close(stage_key, tombstone)` 和不可由 repo/CLI 伪造的 reviewer dispatch
metadata。本仓库不实现该 store；激活前必须有宿主实现所有权、capability/version attestation、restart
恢复和真实 CAS 竞争证据。缺失时返回 `HOST_STATE_UNAVAILABLE` 且继续使用 pre-change 流程，不把
shadow PASS 升格为已激活 gate。

Workspace binding 是 context/CAS key/tombstone/dispatch 的一部分，精确包含 host-issued `workspace_id`、
host 启动时 canonical project-root raw-byte digest、Git common-dir identity digest、worktree git-dir identity digest、stage id
和 planning base。Entrypoint 只能将宿主启动时 root 与 live resolved root 比较，不能用 caller 新选的
`project_root`。Sibling clone、linked worktree、symlink alias、另一 `git -C` target 均不得共享 state key。

Event 与 receipt append 都使用两阶段 compare-and-swap。Controller 以 prior retained count/head 和 candidate local
count/head 调用 validator；validator 必须证明 prior exact head 仍是未改写 prefix、只新增允许数量的 contiguous files，
然后返回 proposed next state。Host 只在 PASS 后原子替换 retained state。Crash recovery 只能在同一 prior state上采用或
拒绝唯一 candidate append；并发 append、先更新 host 再验证、prefix rewrite + new head 全部 fail closed。普通 action
preflight 只接受 local lineage 与已 retained current state exact equal，不会顺便“收养”新 head。

每个 event 记录 stage、sequence、previous event hash、event kind、host-issued event identity、bounded source reference、
`authority_before` epoch/hash、`authority_requirement`、changed fact ids、before/observed input snapshot digests、classification
ceiling 和 canonical payload digest。Host reference 仍不证明 user identity。仅对未来已激活 v2 cohort，
direct-user change 的无环顺序为：event 先绑定 old authority和 required later epoch；later authority v2 再绑定
trigger event count/head并 supersede old record；replay receipt 最后绑定 event head 与 new authority hash。
Introducing/in-flight v1 cohort 的 owner-bound drift 继续使用 pre-change later-v1 epoch/record，不生成 replay event。

Alternative：只扫描 Git diff 或只比较 current head。拒绝，因为 requirement change 可能尚未落盘，而 current-only head
无法证明历史 prefix 未被重写。

### 2. Use a versioned dependency graph and a replay frontier set

Validator 内置版本化 gate graph，而不是接收 repository-authored任意 graph。初始节点为：

`plan_contract -> plan_review -> authority -> implementation -> verification -> implementation_review -> archive -> post_archive_delivery_review -> candidate -> merge -> push`。

V1 有意保持线性，便于把新合同限制在当前真实 closeout 流程内；`replay_frontier_gate_ids` 仍使用集合类型。
每个 exact fact id 只映射到一个 earliest seed，`invalidated_gate_ids`/`required_replay_gate_ids` 是从 seed 开始的完整
suffix，`preserved_gate_ids` 是 seed 之前且 snapshot proof成立的完整 prefix，初始 frontier 是 seed。多个 facts 取最早
seed。不存在 Git target 特殊跳边，也不声称 V1 得到理论最小集合：target-only drift 会从 `authority` 保守重放所有 suffix。

| Exact `changed_fact_id` | Earliest invalidated gate |
| --- | --- |
| `requirements`, `scope`, `non_goals`, `risk`, `allowed_path_rules`, `planning_baseline` | `plan_contract` |
| `plan_subject` | `plan_contract` |
| `authority_record`, `action_ceiling`, `vcs_endpoint`, `target_branch`, `authorized_remote_tip` | `authority` |
| `implementation_subject`, `workflow_subject`, `template_subject`, `verification_contract` | `implementation` |
| `verification_evidence` | `verification` |
| `implementation_review_binding` | `implementation_review` |
| `archive_output` | `archive` |
| `final_delivery_packet`, `candidate_head` | `post_archive_delivery_review` |
| `merge_target_state` | `merge` |
| `push_outcome_evidence` | `push` |

上述 table + suffix/prefix 公式是完整 exact-set 合同。实现必须为每个 fact id 参数化断言完整 invalidated、preserved、
required replay 和 initial frontier sets；receipt 不能补 edge、删 gate 或自报更晚 gate。

Event-kind ceiling 同样是代码常量：`direct_user_envelope_change` 只能声明 owner-bound facts 与随之更新的
`plan_subject`；`agent_technical_correction` 只能声明 `plan_subject`、implementation/workflow/template 和 verification
facts；`review_remediation` 必须记录 `review_phase=plan|implementation`，plan finding 可声明 `plan_subject`，implementation
finding可声明 implementation/workflow/template/verification/review-binding facts，二者都必须绑定原 slot/receipt/finding
lineage；`repository_or_git_drift` 只能声明 planning baseline、VCS target、archive/final packet、candidate、merge 或 push
facts，并只能触发停止/重放，不能把 observed value 变成 authorized value。Unknown fact、duplicate、wrong phase/kind fail closed。

输出同时包含：

- `invalidated_gate_ids`
- `preserved_gate_ids`
- `required_replay_gate_ids`
- `replay_frontier_gate_ids`
- `resume_status`

Frontier 是 required suffix 中所有 earliest uncompleted nodes 的集合，不使用单个固定步骤号。V1 不伪造并行 gate；
未来图版本若增加并行节点，必须同时升级 graph version、完整 exact-set fixtures 和 action matrix。

Alternative：线性 `resume_step`。拒绝，因为它既会过度重放，也可能掩盖并行依赖缺口。

### 3. Material-change classification consumes a host gate snapshot and transition contract

Host-owned `gate_lifecycle_snapshot/v1` 为每个 gate 保留 `state=open|bound|closed`、monotonic generation、code-owned
evidence-adapter id、exact input snapshot digest、output digest 和 dependency digests。Action preflight 现场用同一 adapter
重算 live input；任一 closed/bound input 不同且没有 host-CAS accepted event 时，即使 caller 传 `0/none` 也返回
`MATERIAL_CHANGE_EVENT_REQUIRED`。

No-event 例外不是自然语言标签，而是 code-owned transition table：

| Transition | Required pre-state | Exact allowed effect |
| --- | --- | --- |
| `initial_plan_authoring` | `plan_contract=open` | 仅计划 packet/Harness planning paths |
| `initial_implementation_edit` | frontier=`implementation` | 仅 approved implementation subject/path envelope |
| `verification_run` | frontier=`verification` | read-only subject；只生成 code-owned verification evidence |
| `review_tail_write` | frontier=`plan_review` 或 `implementation_review` | 对应 schema-valid review evidence，且 host dispatch另验 |
| `openspec_archive` | frontier=`archive` | exact active-to-approved archive mapping和声明的 spec sync |
| `delivery_tail_write` | frontier=`post_archive_delivery_review` | 仅 final `review-set.json` 与 `delivery-binding.json` |
| `candidate_commit` | frontier=`candidate` | worktree已冻结，只创建 exact reviewed finite commit |
| `ff_merge` | frontier=`merge` | exact candidate 到 exact target 的 fast-forward |
| `lease_push` | frontier=`push` | exact refspec + exact-old-OID lease |

Post-state/delta 与 table 不完全相等、closed subject 被改、archive 额外文件、错误 destination、post-packet non-tail write
或 preserved earlier mutation，均须先追加 material event。语义分类仍由 host/review负责；snapshot只封闭机器可观察的遗漏。
所有 event kinds沿用上一节 ceiling。原 envelope 内技术修复不强制 owner 重批；owner-bound fact 改变必须有
later direct-user authority。V1 cohort 走 pre-change later-v1 record；已激活 v2 cohort 才另需
`direct_user_envelope_change` event/replay。

### 4. Authority/delivery schema v2 removes the commit-order ambiguity

Current `stage_authority/v1` 的 ordinal 是 `plan -> implement -> commit -> archive -> merge -> push`，而真实 finite candidate
在 archive/post-archive review 后创建。新 gate 不把同一个 `commit` 同时解释成 archive 前 checkpoint 与 candidate。
Prospective `stage_authority/v2` 将 order 固定为 `plan -> implement -> archive -> commit -> merge -> push`，其中 `commit`
只表示 finite `candidate`。现有 `.harness/templates/stage-authority-record.template.json` 和
`.harness/templates/stage-delivery-binding.template.json` 继续是 active v1 producers，直到所有 v1 cohort terminal。
新增的 `.harness/templates/stage-authority-record-v2.template.json` 和
`.harness/templates/stage-delivery-binding-v2.template.json` 仅是dormant v2 schemas。Activation 后的新 cohort 才使用 v2；
caller 不得通过选 template/schema 切换 cohort，也不得跨 schema 重新解释旧 ceiling。

V1 stage 在 terminal 前发生 owner-authorized scope/risk/action/target drift 时，必须保留现有 later-v1 epoch、
supersession hash、live decision 和 validator path，不依赖 dormant host CAS。V2 authority record 增加
`trigger_change`：initial/no-change epoch 为 `count=0/head=none`；direct-user replacement epoch
绑定已 CAS accepted 的 trigger event count/head、old authority hash和 required later epoch。Event 不含 future authority hash；
receipt 绑定 event head + new authority hash，validator对 old/new scope exact delta交叉核对，因此无哈希环。V2 delivery
binding 同时绑定 current event/receipt counts/heads、final review packet 和下列精确 pre-candidate inputs：
`expected_parent_oid`、`review_packet_sha256`、`reviewed_manifest_sha256`、
`reviewed_inventory_sha256`、固定的 review-metadata/two-file-tail path set，以及
`single_parent_exact_subject_plus_metadata/v1` construction policy。它不包含 future candidate OID 或 tree OID。
Candidate 创建后，host 另行保留 actual OID；candidate adapter 检查唯一 parent、完整 reviewed subject、
固定 metadata/tail 路径和 replay/authority heads，不得回写 delivery binding，因此无自引用。

### 5. Gate completion uses code-owned evidence adapters

Change replay receipt 只能引用下表 adapter 的严格输出，不能用任意 hashed file、timestamp、chat summary、自由 command
digest 或 repository-authored `PASS` 关闭 gate：

| Gate | Code-owned evidence adapter and required bindings |
| --- | --- |
| `plan_contract` | `openspec_plan_contract/v1`: exact plan artifacts/packet、change id、strict OpenSpec result、gate input generation |
| `plan_review` | `independent_review/v1` phase=plan: actual `validate_independent_review` PASS + exact packet + host dispatch/activation checks external |
| `authority` | authority core v1/v2 result先于 replay运行，绑定 live-host expected envelope；replay只消费 core report digest |
| `implementation` | `implementation_subject/v1`: exhaustive planning-base-to-live Git manifest、allowed-path hash、generation |
| `verification` | `verification_bundle/v1`: code-owned command ids/argv/cwd、required command set、exit status、subject/input hashes和 output digests |
| `implementation_review` | `independent_review/v1` phase=implementation: actual validator PASS + exact subject packet + host dispatch/activation checks external |
| `archive` | `openspec_archive/v1`: exact active/archive mapping、declared spec sync和 post-archive strict/all status |
| `post_archive_delivery_review` | final reviewed manifest/diff + all required reviewer slots on one post-archive packet |
| `candidate` | existing exact candidate/source/worktree/delivery-binding checks，包含 replay heads |
| `merge` | existing exact target/premerge/ff-only/live endpoint checks |
| `push` | existing exact refspec/lease/same-endpoint reconciliation and host outcome |

Unknown adapter/schema/producer、partial command set、wrong argv/subject/generation/event head/authority/packet 或缺外部 host-observed
review dispatch时，该 gate不进入 completed set。Authority core 与 replay分层调用，禁止 outer authority report 与 replay report
互相引用。

Canonical layout 仍为 `.harness/change-replay/<stage-id>/events/event-<six-digit-sequence>.json` 与
`receipts/receipt-<six-digit-sequence>.json`。Filename/internal sequence、predecessor、strict schema、canonical path、regular-file、
non-symlink、raw-path safety 与 CAS prefix必须全过；replay root 必须精确等于 host-bound initial
workspace 下的 canonical stage path。只相对 caller-selected root 合法不足以通过。

### 6. Replay progress is monotonic and exact-frontier only

同一 event head 的 receipt progress 只能按 graph 顺序单调增加 adapter-verified completed gates。新 event 让所有 earlier
progress stale。Changed lineage 下，governed mutation 必须精确等于 current frontier 映射；earlier preserved action 返回
`ACTION_BEHIND_REPLAY_FRONTIER`，later action返回 `STAGE_REPLAY_REQUIRED`。不存在 `unaffected action` 旁路。No-change
lineage也必须通过 host gate snapshot 的 normal-sequence transition check，不能仅因 invalidated set empty而任意放行。

V2 governed mapping是 `implement -> implementation`、`archive -> archive`、`commit -> candidate`、`merge -> merge`、
`push -> push`。Plan/authority、read-only verification和independent review用对应 adapter推进。Canonical event/receipt projection
是单独的 controller evidence transition，只能CAS追加stage-local replay path，不能修改subject或提升ceiling，并进入final packet。

Final implementation review receipt、delivery binding、exact candidate、merge state 和 push outcome 已由现有 gate 作为
tail/host/live inputs 消费。Replay validator 可以在 action preflight 时组合这些外部 inputs 判定相应 predecessor，
但不得把它们复制回 pre-frozen replay receipt。这样 remediation replay 不会要求 review-set 在 frozen subject 内引用自己，
也不会产生第三个 evidence-tail 文件。Successful push 后的最终状态仍由 controller live receipt 报告，不回写 repository。

Artifact 或 command evidence 的 freshness 完全由上一节 adapter matrix和host generation决定；byte/hash相同但dependency
generation改变仍 stale。

### 7. Integrate before action gates without expanding final evidence tail

`validate_stage_authority.py` 增加可选的 dormant replay interface，机械消费
`validate_stage_change_replay.py` 的结构化结果。本 change 不将该结果激活为 v1 stage 的 mutation
authority；只有后续 host capability stage 通过独立评审和 direct-user activation 后，v2
implement/archive/commit/merge/push 才能把它作为 blocking preflight。

该 interface 参数固定为 controller context capability/version、immutable workspace binding、canonical replay dir、
current event/receipt counts/heads、gate snapshot digest、terminal state、required action 和现有 authority/review/delivery/Git
inputs。Append-CAS模式另收 prior heads与 candidate append，
只返回proposed host update。Unknown action、alternate mapping、snapshot generation 或unretained local head fail closed。

- no-change：lineages empty/equal且live closed/bound inputs匹配host snapshot，再按normal transition state machine判断；
- changed/behind或ahead：结构化FAIL并给current frontier；
- changed/exact-frontier：CAS heads、adapter evidence、authority、snapshot和action全部一致后才ready。

Change event、receipt 和 pre-tail replay evidence 都属于 final reviewed subject。Final packet 后若新增 event，manifest drift
必须重新打开 verification/review/archive；既有 `review-set.json + delivery-binding.json` 两文件 tail 不增加第三项。
Review/candidate/merge/push 等 tail/live gate 的 replay completion 只在 validation report/host state 中组合，不回写 receipt。

### 8. Terminal stage state, activation, and claim ceiling stay external

Future activated-v2 host 在 same-endpoint read-only query确认 exact candidate 已位于 target branch 后，原子写入 external terminal tombstone：
`workspace identity/stage_id/candidate/endpoint fingerprint/branch/verified remote tip/status=closed`。所有同 stage event append、apply或closeout
preflight先检查 tombstone；closed返回 `NEW_STAGE_REQUIRED`。`UNKNOWN_PUSH_OUTCOME` 保持 `delivery_unknown`，只允许同endpoint
reconciliation，不得追加普通 replay progress。Tombstone不回写repository，controller restart仍须恢复。

本 introducing stage 从 plan 到 verified push 始终属于 pre-change v1 cohort，不调用 replay blocking gate，也不被
v2 重解释。它只能在 reviewed repository bytes 中记录
`activation_status=blocked_on_external_host_capability`。激活时已存在的任何 v1 in-flight stage 同样沿用
pre-change 流程至 terminal；已 terminal v1 stage 不得重开。只有 introducing stage 已 verified push、
`provider_neutral.stage_state_cas/v1` 真实 host evidence 完整、另一独立 activation stage 获得 direct-user
approval 并被交付后，后续新建 stage 才进入 v2 cohort。Cohort 由 host activation chronology + exact
stage/schema state 决定，不从 repo hash、日期或 record schema 自行推断。

Reports continue to separate `mechanical_consistency_only`, host-observed authority, `technical_ready`, and `vcs_pushed`.
Repository validator 的 `requested_action_ready` 只表示 mechanical prerequisite；overall mutation 仍须 host controller在仓库
report之外核对 native state/dispatch/authority。CLI 中一个 self-reported boolean 不能替代该检查。

## Risks / Trade-offs

- [Risk] Gate graph 漏 edge 会产生过晚恢复点。→ V1固定linear suffix/prefix公式、每个fact的完整exact-set参数化测试；不使用特殊跳边。
- [Risk] V1 target-only change重放较多。→ 接受保守成本；只有未来独立graph版本和完整fixtures才能增加选择性保留。
- [Risk] Agent 自写 direct-user event扩权。→ Host gate snapshot + append CAS + authority v2 trigger binding + live decision分开校验；repository receipt永不升级human authority。
- [Risk] 任意 evidence 文件自证 gate。→ 只接受code-owned adapter matrix，真实 review/authority/terminal host facts继续external。
- [Risk] Final packet 后出现 event 造成证据尾无限增长。→ Event/replay 不是 tail；任何新 event 都使 packet stale，并回到 final review前。
- [Risk] Existing stages have no replay chain/action v2。→ Introducing/in-flight v1 cohorts完整沿用pre-change流程至terminal，包括owner drift后的later-v1 replacement；active v1 templates保留，v2使用独立dormant templates。
- [Risk] Repository validator 被误当作host adapter。→ 本change明确dormant/mechanical-only；无外部capability attestation不得激活，CLI PASS永不授权。
- [Risk] Stage state 重放到sibling worktree。→ context/CAS/tombstone同时绑定host-issued workspace id、initial root、common-dir、worktree git-dir和planning base。
- [Trade-off] Process-only change会增加 templates、tests 和 workflow wiring。→ 不进入 `app/**`，不增加 runtime概念；复杂度集中在单独 validator 与确定性 schemas。

## Migration Plan

1. 先提交 RED schemas/negative tests，覆盖 omitted event、CAS prefix rewrite、arbitrary evidence、exact-set/action matrix、legacy/v2 ordering、terminal stage和unreviewed packet drift。
2. 实现gate snapshots、adapter matrix、独立 replay validator与deterministic graph，再以authority-core-first顺序接入preflight。
3. 保持现有authority/delivery v1 templates/producer不变，新增独立dormant v2 templates，再同步Codex/OpenCode apply/archive、review/handoff、test commands和长期specs。
4. 运行 focused/full verification、两槽独立 implementation review 和 Stage Debt Sweep。
5. 由 pre-change v1 process 完成本 stage 的 archive/candidate/merge/push，只将 replay 产物记为
   `blocked_on_external_host_capability`；verified push 后不回写仓库，也不自动激活。
6. 后续独立 stage 必须先提供真实 `provider_neutral.stage_state_cas/v1` 实现证据、完整测试/评审和
   direct-user activation，然后才能对新建 v2 cohort 开启 blocking gate。

Rollback 是删除尚未激活的新 validator/wiring 并保留 OpenSpec/history。本 change 不存在“激活后回退”
路径；未来激活必须另起 reviewed change 定义 disable/recovery 规则。

## Open Questions

- 无需用户决定底层 graph 或 schema 结构；这些属于 Agent 技术选择。
- 实现前唯一人工 gate：是否接受本 stage 的 high-risk process scope、non-goals、exact path envelope 和 action ceiling。
