# 当前 Review 清单

Active OpenSpec change：无。

当前没有 active stage review checklist。启动新阶段前，必须先按最新 RepoPilot 工作流重新创建
或同步 `.harness/allowed_files.md` 与本文件。

最近完成阶段：`add-stage-change-replay`。

- OpenSpec archive：`openspec/changes/archive/2026-08-21-add-stage-change-replay/`
- Risk：high / L3 / process-only；改变 repository development workflow 的 material-change invalidation、
  replay lineage 与 action-readiness 机械合同，但未增加 RepoPilot runtime 能力。
- Authority：direct-user approval 由宿主独立核对；later-v1 epoch 2 线性绑定 exact scope、push ceiling、
  origin/main/authorized tip。Repo record/hash/validator 的 claim ceiling 固定为 `mechanical_consistency_only`。
- Final implementation review：A/B 两个 first-round reviewers 的全部 P1/P2 均完成原 same-slot remediation
  re-review；最终共同 packet 为 `bce8efe0…eea7`，两席均为 READY / NO_FINDINGS。
- Capability boundary：replay/v2 固定为 `blocked_on_external_host_capability`。11 个 caller-supplied adapter
  只能提供机械一致性；缺少 external host capability/native attestation 时，所有 action（含
  `reconcile_push`）均 `requested_action_ready=false`。
- Verification：focused replay/authority `363 passed`；full pytest `916 passed, 3 failed`，3 项均为既有
  baseline；changed Python Ruff、`py_compile`、`git diff --check` PASS；OpenSpec active strict PASS，
  archive 后无 active change且 all `24 passed, 0 failed`。
- Inherited debt：model-provider recursion-depth 1 项，以及当前 shell 无 `python` 命令导致
  verification-runner 2 项；full Ruff 96 项同样为既有 baseline，因此未宣称 full repository verification PASS。
- Archive result：reviewed change 已归档到上述路径，archive authority/live remote stop conditions 与
  archive-after validation 已完成。
- Closeout ceiling：finite candidate、ff-only merge、exact-old-OID lease push、same-endpoint reconciliation
  与 `vcs_pushed=verified` 尚未由本清单声明完成；由 controller 按 final packet 与两文件 evidence tail
  顺序继续，不在 candidate 后回写仓库。
