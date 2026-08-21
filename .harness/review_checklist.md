# 当前 Review 清单

Active OpenSpec change：无。

当前没有 active stage review checklist。启动新阶段前，必须先按最新 RepoPilot 工作流重新创建
或同步 `.harness/allowed_files.md` 与本文件。

最近完成阶段：`bind-stage-authority-and-invalidation`。

- OpenSpec archive：`openspec/changes/archive/2026-08-20-bind-stage-authority-and-invalidation/`
- Risk：high / L3 / process-only；改变 repository development workflow 的 human-authority binding、
  invalidation 与 Git closeout failure semantics，但未增加 RepoPilot runtime Git automation。
- Plan authority：direct-user authority 由宿主独立核对；repo record/hash/validator 的 claim ceiling 固定为
  `mechanical_consistency_only`，不能证明用户身份、消息真实性、授权时序或 push 成功。
- Final implementation review：A/B 两个 first-round reviewers 的 blocking P1 均完成原 same-slot remediation
  re-review 并关闭。Focused Stage Debt Sweep 已完成，没有新增 in-scope blocking debt。
- Verification：focused remediation `92 passed`；authority + independent-review + CLI combined `163 passed`；
  changed Python Ruff PASS；OpenSpec pre-archive strict change PASS / all `24 passed, 0 failed`，post-archive all
  `23 passed, 0 failed`；`git diff --check` PASS。
- Inherited debt：full pytest `645 passed, 3 failed`；3 项为未修改路径的既有 baseline（model-provider
  recursion-depth 1 项、当前 shell 无 `python` 命令导致 verification-runner 2 项）。Full Ruff 的 96 项同样是
  既有 baseline，因此未宣称 full repository verification PASS。
- Archive result：reviewed change 已归档到上述路径；archive authority/live-host gate 与 archive-after
  validation 已完成。
- Closeout ceiling：finite candidate commit、merge、push、remote parity 和 `vcs_pushed=verified` 尚未由本清单
  声明完成；archived tasks 4.5–4.8 仍由 controller 按 final packet、两文件 evidence tail、exact candidate、
  ff-only merge、exact-old-OID lease 与 same-endpoint reconciliation 顺序收口。
