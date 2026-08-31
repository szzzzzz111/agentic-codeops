# Context

现行规则已经把 README、ARCHITECTURE、PROGRESS、FEATURE_LIST、HANDOFF、Harness 与 OpenSpec 分配给不同
事实类型，但 tracked HANDOFF 仍保存 post-commit 才能知道的 push 状态，ARCHITECTURE 和 PROGRESS 仍承担
版本日志，scanner 只匹配少量 literal stale phrases。结果是 structural checks 全绿而 current guidance 失真。

# Decisions

1. 先按语义类别区分 `read-only`、`mechanical`、`behavioral`、`authority-sensitive`，再映射 low/medium/high。
   文件数量只扩大验证面，不能单独提升 review lane。
2. Implementation lane 与 delivery action 分开；low-risk docs change 即使以后交付，也只在 Git mutation 时使用
   对应 delivery preflight，不继承 medium/high semantic review。
3. Tracked HANDOFF 只保存恢复命令、阅读顺序和安全规则；branch、HEAD、worktree、candidate、merge、push、
   remote parity 与 active change 均从 live Git/OpenSpec/controller state 获取。
4. ARCHITECTURE 的 current surface 只描述 runtime system context、route order、component-to-code map、state、
   mutation flow、trust boundaries 和 non-goals。为避免一次性删除仍可能有参考价值的旧正文，旧逐阶段内容
   暂时放入明确 non-canonical 的折叠 migration appendix；历史事实所有权仍归 archived OpenSpec。
5. PROGRESS 不再复制每个 archived stage 的完整证据；保留 durable status、remaining debt、候选顺序和阶段索引。
6. Scanner 只检查可确定的结构：handoff 禁止 volatile claims、FEATURE_LIST notes 禁止 stage narration、
   specs index 与目录集合一致、ARCHITECTURE current-first 且不含 version-heading log。历史 archive 不扫描。
7. 新 authority records 可在 hashed scope 中加入 `review_slot_requirements`，精确绑定 plan 与 implementation
   slot count。旧 records 为兼容性可以缺省该字段，但缺少绑定时不得请求 zero-slot；当前 high-risk 阶段在
   validator 激活后以 later v1 epoch 绑定 `plan=2`、`implementation=2`。
8. `required_slots=0` 只表示 authority-bound low-risk contract 不要求 independent receipts，不表示跳过 review
   packet。Stage-authority gate 必须拒绝 medium/high zero、未绑定 zero 以及 caller count 与 scope count 不一致；
   archive/commit 仍消费 schema-valid review set、完整 manifest、packet hash、activation 和 authority binding。
9. Independent-review validator 只接受 `type(required_slots) is int` 的非负值，明确拒绝 bool、float、字符串和
   负数。零要求 `receipts=[]` 且 `review_history=[]`；正数的 reviewer identity、context isolation、finding
   closure 和 exact-count 规则保持不变。
10. 这是 authority-sensitive gate behavior change，阶段风险向上升级为 high；实现前和最终候选分别使用两个
   `fork_turns=none` 的独立 review slots，不能用仓库自填字段代替 host dispatch provenance。
11. Archive 使用 pre-archive packet 预检；spec sync/move 后必须重建 final manifest/diff，并让两个 final slots
   绑定同一 post-archive packet，之后才生成 delivery binding 和 candidate commit。
12. 新 records 的 binding schema 必须精确为 `{plan, implementation}`，两个值均为非负真整数；任意 phase 的
    caller count 都必须与 bound count exact equal。Stage-authority 增加 plan-phase review-set 输入，以便未来
    stage 机械消费 plan binding；当前 introducing plan review 仍由 pre-change process governing，不能用新实现
    追溯声称已验证自身。
13. 对带 `review_slot_requirements` 的未来 authority record，`required_action=implement` 是 plan review 的强制
    消费点。调用方必须提供 canonical `.harness/reviews/<stage-id>/plan/review-set.json`、caller plan count 和
    host-retained expected plan packet SHA256；validator 必须以 `expected_phase=plan` 复核完整 manifest、packet
    hash、activation、authority binding 和 exact bound count。缺输入、非 canonical path、错 phase、错 packet、
    缺 manifest/activation/authority evidence 或拿 implementation review set 交叉替代均 fail closed。legacy
    record 没有 binding 时保持既有 implement preflight 兼容路径，但不得报告 authority-bound count。
14. 仅当前 change 的 epoch 5 introducing-plan 由 pre-change process 完成，不追溯调用尚未实现的新 gate；此例外
    由 exact stage/epoch 和 activation chronology 限定，不能成为未来 bound record 的 bypass。validator 激活后
    创建的 bound records 必须遵守 decision 13。
15. OpenSpec 的 archive-before-candidate 是本阶段 controller 顺序和 post-archive content-addressed packet contract，
    不是所有 repository commit 的全局前置条件；通用 commit gate 不新增“必须存在 OpenSpec archive”状态。
16. zero-slot 结果中 reviewer dispatch provenance 为 `not_applicable`；activation chronology、authority binding 和
    host-retained expected values 仍为外部必需证据。positive-slot 报告继续要求真实 host dispatch provenance。
17. Plan packet completeness 由 controller 冻结的 canonical artifact-manifest SHA256 绑定；该 expected hash 是
    host-retained authority input，不是 repository/caller 自报值。删除或替换任一 artifact 都会改变 packet hash，
    并在 unchanged host value 下 fail closed。若 host expected value 本身被替换，已超出 mechanical validator 的
    claim ceiling，与替换 risk/scope/remote-tip 等 host inputs 同类。
18. zero-slot 的 empty-history 规则约束当前提交并被验证的 review set；不声称 repository validator 能从可变
    worktree 推导一个未提供的 prior review-set head。跨版本 append-only history/CAS 仍依赖已暂缓的 external
    host CAS/replay v2，不能在本窄修中伪造。
19. Bound-plan inputs 不只写入 validator 和 stage planner；实际 Codex/OpenCode apply entrypoints 与
    `.harness/test_commands.md` 必须显式列出三个必需 flags，避免正常 apply 流程因文档缺参而必然 fail closed。
    HANDOFF live-state scanner 先去除常见 Markdown list/emphasis/inline-code 包装，再覆盖带或不带
    current/当前前缀、半角或全角冒号的中英文 branch、HEAD、worktree、candidate、merge、push、
    remote/remote parity 与 OpenSpec change/变更赋值；中英文“易变事实/现场查询”等稳定
    query-guidance 元说明均保留。
20. medium/high authority 的整个 `review_slot_requirements` binding 中任一 phase 为 zero 都必须在 record
    shape validation 阶段失败，不能只检查当前 action 消费的 phase。
21. 通用规则必须区分 positive-slot 与 authority-bound zero-slot：前者要求 host-native reviewer dispatch
    provenance，后者明确 `NOT_APPLICABLE` 且不得制造 reviewer evidence；activation sequence 两者都保留。

# Risks And Controls

- 文档压缩可能丢失证据：详细阶段 artifacts 继续保存在 `openspec/changes/archive/` 和 Git history；PROGRESS
  提供索引而不是删除唯一事实。
- Scanner 可能误报：只检查明确 structural patterns，不尝试自然语言推理。
- 大文件重写可能掩盖 runtime drift：ARCHITECTURE 的模块和路由顺序直接从当前 `app/**` 只读核对，
  不修改实现。
- 零 slot 可能被误解为无 packet gate：测试同时覆盖 authority-bound low+zero、unbound/high+zero rejection、
  empty receipts/history、zero+nonempty receipts/history、negative/non-int count，以及 archive/commit packet 消费。
- Binding 可能只在 zero 分支生效：测试覆盖 plan/implementation bound `2` 与 caller `1/3`、bound `0` 与 caller
  `1`、phase 交叉替代，以及 binding 的 bool/float/string/negative/missing/extra-field rejection。
- Future plan input 可能存在但未消费：测试覆盖 bound record 的 implement PASS，以及 plan set 缺失、非 canonical
  path、错 phase、错 host packet hash、缺 manifest/activation/authority evidence 和 implementation set 替代。
- Archive 顺序可能被误做成全局 commit 语义：只由本阶段 controller 执行 archive 后 packet refresh；不改变
  非 OpenSpec 阶段的通用 commit contract。
- 放宽条件可能意外削弱正数 slot：保留现有 positive-count suite，并运行 independent-review、stage-authority
  focused tests 与 canonical repository verification。

# Verification

- Scanner RED/GREEN unit tests。
- Docs contract targeted test。
- Repository stage-doc scan、JSON parse、changed Python Ruff、OpenSpec validation、`git diff --check`。
- 因 checker/tests 变化，最终运行 canonical `python -I scripts/verify.py`。
- Authority scope 追加后先运行两个独立 plan reviews；validator 采用 RED/GREEN focused tests，最终再运行两个
  independent implementation reviews、archive/commit gate、ff merge 和 exact-old-OID lease push。
