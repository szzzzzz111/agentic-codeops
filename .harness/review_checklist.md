# 当前 Review 清单

Active OpenSpec change：none。`evaluate-governed-run-cohort` 已归档到
`openspec/changes/archive/2026-09-03-evaluate-governed-run-cohort/`（authority epoch 8）。

Risk：high / L3。plan 与 implementation 各需两个 fresh empty-context slots。旧 CLI 路线 packet/receipt 均不可复用。

## Scope And Authority

- [x] 用户明确授权 Codex App fresh task + independent worktree 路线的 plan、implementation、re-review 与一次实验。
- [x] 实现与一次实验未写原脏 worktree；用户随后授权在阶段完成条件成立时完成 archive、commit、ff-only merge 与 lease push。
- [x] live `origin/main`、local tracking ref 与 planning base 均为 `b7a8439fac9013f5ad59c308c4b16d333d466ddb`。
- [x] epoch 5 implement record 的 scope/allowed-files/base/action binding 通过 mechanical validator。
- [x] epoch 6 closeout record 的 archive authority preflight 绑定最终 pre-archive packet。

## Plan Contract

- [x] 一个 fresh task、一个 App worktree、一个 handshake turn、一个 coding turn；无 retry/resume/replacement task。
- [x] handshake 只回复 `READY_FOR_TASK` 且不得改文件；controller 在 coding turn 前证明 baseline clean/exact HEAD/same repo。
- [x] stage/task 必须是同一 porcelain 集合中的 live non-prunable worktree；无关 prunable 历史记录只排除自身。
- [x] coding prompt 只允许精确修改 `README.md` 第一行、禁止 commit、最终只回复 `READY_FOR_REVIEW`。
- [x] task-worktree mutation authority 绑定完整 README before/after digest；stage worktree 仍不允许写 `README.md`。
- [x] 候选脚本只做 in-memory host observation bridge；唯一 JSON 必须由 EOF 封口，buffered duplicate、未封口/超时均
  fail closed；不调用 App task API、不启动 Codex/provider process。
- [x] completion 只允许 exact README bytes/digest，无 untracked/index/其他 path；`ruff` 强制 `RUFF_NO_CACHE=true` 并绑定同一 endpoint snapshot。
- [x] 六类故障覆盖 task/observation、baseline、claim、scope、snapshot、verification/receipt/evaluator。
- [x] repository summary 固定 `host_observed_unverified`；真实 task 只由 controller native tool metadata支持。
- [x] claim ceiling排除 runtime subagent、OS isolation、authenticated provenance、semantic completion、human approval、product acceptance 和 Git delivery。

## Plan Review Gate

- [x] internal plan review 对齐 proposal/design/tasks/spec/Harness/authority。
- 两个 fresh empty-context reviewer slots 与 validator 的最终结论只记录在 subject packet 外的
  `.harness/reviews/evaluate-governed-run-cohort/plan/review-set.json` evidence tail；不得回写本 checklist 冒充已审事实并
  造成 packet 自失效。

## Implementation Gate

- [x] HostTaskObservation strict parsing/correlation、buffered duplicate、EOF 封口与 timeout RED tests 转绿。
- [x] Baseline（含无关 prunable 历史记录）、exact mutation、snapshot/receipt 六类 RED tests 转绿。
- [x] 真实 whitelist `ruff` 在无缓存 fixture 上不创建 `.ruff_cache`，runner-before/post snapshot 相同。
- [x] 候选脚本无 Codex/provider spawn、无 App API/runtime integration、无 raw/durable task material。
- [x] Focused tests、changed-file Ruff、canonical verification、`git diff --check` 与固定版
  `@fission-ai/openspec@1.11.0` strict 均已真实通过。
- [x] 新 implementation packet 经两个 fresh slots 复核相同 bytes，P0/P1 清零。

## One Real Task Gate

- [x] Native create result 证明一个 fresh Codex App task 与 App worktree。
- [x] Handshake final 是 exact `READY_FOR_TASK`，且 task worktree baseline clean/exact base。
- [x] 唯一 coding turn completed，final exact `READY_FOR_REVIEW`，无 retry/extra turn。
- [x] Reviewed bridge 输出同 snapshot `ready_for_review/VERIFICATION_PASSED`，并保持 source unverified 与所有 claim ceiling。
- [x] 最终报告 task/worktree residual state；未自动 archive/delete/commit/merge/push。

## Archive And Delivery

- [x] 更新完成事实后冻结 pre-archive packet，原 A/B 两席复审同一 bytes 且 P0/P1 清零。
- [x] Archive authority preflight 消费最终 pre-archive review set；OpenSpec archive 同步长期 spec。
- [x] 归档后同步 durable progress、OpenSpec index 与 Harness final state，完成 canonical verification 和 strict/all validation。
- [ ] 原 A/B 两席复审同一 final post-archive packet，P0/P1 清零并刷新 review-set。
- [ ] Delivery binding、精确 staged index 与 commit authority preflight 绑定同一 packet。
- [ ] 创建单一 candidate，ff-only 合并到 main，以 exact-old-OID lease 显式 push，并从同 endpoint 对账。
