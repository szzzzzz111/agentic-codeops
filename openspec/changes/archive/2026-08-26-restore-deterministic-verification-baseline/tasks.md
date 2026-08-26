## 1. Plan And Authority

- [x] 1.1 从 live `origin/main` 精确 OID 创建新 clean worktree，证明原脏 worktree不在 editable surface。
- [x] 1.2 记录首次 Python/pytest/Ruff/PowerShell baseline；按 96 项跨 56 文件的证据拆出机械 Ruff stage。
- [x] 1.3 冻结 proposal/design/spec deltas、allowed files、review checklist、risk、non-goals 和 stop conditions。
- [x] 1.4 完成 internal review 与两个 `fork_turns="none"` 独立 plan review slots；同席关闭 P0/P1，验证 final
  plan review set 绑定同一 packet。
- [x] 1.5 使用当前 direct-user confirmation 创建/校验 pre-change v1 authority record，并在任何
  runtime/test mutation 前通过 `required-action=implement`。

## 2. TDD: Provider JSON Depth

- [x] 2.1 增加含顶层 container 的 128/129 层边界、object/array、字符串 brace/escape、closing quote 前
  1/2/3/4 backslash parity RED cases；保留现有 1100 层 RED evidence。
- [x] 2.2 实现只统计字符串外结构字符的 nesting scanner；超限返回现有安全 provider validation error。
- [x] 2.3 运行 model-provider focused 与 long-task/patch-authoring adjacent regressions；确认默认 fake/offline、
  prompt、metrics、finish reason 与 caller-owned schema 不变。

## 3. TDD: Current Interpreter And Canonical Verify

- [x] 3.1 将临时 script runner tests 改为 `sys.executable`，保留 missing-command negative case。
- [x] 3.2 为 Verification Runner 三个 labels 增加 exact `sys.executable` argv tests；为 pytest/ruff module
  missing 增加 isolated-mode spawn-before preflight/unavailable stable error；在 fixture repo 与 hostile
  `PYTHONPATH` 放置退出 0 的 `pytest.py`/`ruff.py` 及同名 package，证明 standalone labels 不加载 shadow
  module、不假成功；增加 repo-local `.venv` 中正常 installed tool 的正例；扩展
  redactor 精确遮蔽 executable raw/resolved forms，并在 standalone、answer/tool-call、persistent audit
  projection 中回归；standalone pytest 清理 command-shaping env，`--collect-only` 继承值下 marker test 仍执行。
- [x] 3.3 为 Python stage-doc/skill-eval scans 与 canonical verify driver 写 positive/negative RED cases，包括
  pytest/Ruff missing module、子检查非零、从外部 cwd 绝对启动仍固定 repo root，以及 design 完整列出的每个
  stage-doc/skill-eval parity failure family；canonical entry 同样必须拒绝 repo/PYTHONPATH 中退出 0
  的 pytest/Ruff 同名 module/package，允许 repo-local venv 正常安装的工具；verify/scanner/PowerShell 委托都
  使用 `-I`，hostile `PYTHONPATH` 不能提前返回零；canonical pytest 同样不能形成 collect-only 假 PASS。
- [x] 3.4 实现两个 portable scans、`scripts/verify.py`，并把三个 PowerShell scripts 改为 thin wrappers；
  删除 Ruff skip 与重复 scan 实现。
- [x] 3.5 运行 verification runner + AgentLoop/chat/worktree reverification adjacent regressions。

## 4. Specs, Docs, And Debt Sweep

- [x] 4.1 同步 grounded provider 与 verification runner delta specs；更新由本阶段改变的 architecture/feature/
  rules/README/test commands。
- [x] 4.2 把 current-fact 文档的 predecessor final packet 修正为 `7ecc…`，记录 candidate/pushed commit
  `2c0d0d4…`，不改历史 receipt 内容。
- [x] 4.3 Stage Debt Sweep 检查 changed runtime/tests、直接 caller、验证入口与事实所有者文档；记录 Ruff
  successor 和 process-tree containment deferred boundary。

## 5. Verification, Review, And Controlled Delivery

- [x] 5.1 Focused/adjacent tests、full pytest、changed-file Ruff、portable scans、active OpenSpec strict/all
  non-strict 与 `git diff --check` 通过；重测 full Ruff residual；canonical verify 明确只被该 residual 阻断，
  不得误报 full PASS。
- [x] 5.2 冻结 implementation packet，完成 internal + 两个独立 implementation slots；same-slot remediation
  关闭全部 P0/P1并让 final receipts 绑定同一 packet。
- [ ] 5.3 在 v1 authority/archive gate 下归档 change；对 archive 后的完整 staged semantic subject 重建 exhaustive
  manifest/diff，并让同两个 implementation reviewers 刷新到该 final post-archive packet。只有 final receipts
  ready 后才写 schema-valid review-set/delivery-binding two-file evidence tail，并重验 exact staged index/manifest；
  archive 变换或其他 semantic tail 不得自动继承 pre-archive “reviewed”结论。
- [ ] 5.4 冻结 v1 `archive` ceiling 并 dry-run 证明 implement/commit/archive actions allowed、merge/push
  blocked；只有 live base/endpoint/branch/tip 未漂移时才形成本阶段 post-archive local candidate，不得
  merge/push。
- [ ] 5.5 不进入 model patch authoring；从 exact local candidate 规划独立
  `clear-repository-ruff-baseline` 机械阶段。只有该阶段让 full pytest、full Ruff 与 canonical verify 可重复
  全绿后，controller 才把两阶段 commits 一起 ff-only merge，并以 explicit refspec + exact-old-OID lease
  push；same-endpoint reconciliation 后分别报告 technical/human/VCS verdict。
