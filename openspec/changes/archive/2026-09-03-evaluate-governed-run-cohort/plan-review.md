# Plan Review — Codex App host-managed one-shot

## Review target

- Authority epoch: 5
- Risk: high / L3
- Planning base: `b7a8439fac9013f5ad59c308c4b16d333d466ddb`
- Action ceiling: `implement`, including exactly one host-managed task experiment; excluding archive/commit/merge/push
- Runtime impact: none; `app/**` is read-only reuse

## Supersession

The previous local `codex exec` plan, implementation packet
`147f2bd9b78a527e9ca050ac489ff321cc2c6c4effbec402ef16c58ad98186f7`, and its review receipts are historical only.
They cannot support the epoch 5 plan or implementation gate because the producer, source binding, prompt, target path, verification label,
failure model, and host authority have changed.

## Internal review questions

1. Does the plan preserve the actual product question: can a real Coding Agent terminal/claim plus same-snapshot receipt drive the existing kernel once?
2. Is Codex App task creation clearly external development workflow rather than RepoPilot runtime capability?
3. Does the handshake provide a real clean baseline before mutation, rather than trusting the Agent's own report?
4. Can thread id, task terminal and App worktree be correlated without repository bytes claiming authenticated provenance?
5. Is the mutation fixed and mechanically checkable, with no dynamic prompt/argv or arbitrary target?
6. Are completion, runner-before and post-verification snapshots identical and bound to the receipt?
7. Do the six failure families fail closed without retry, fallback to local CLI, or platform expansion?
8. Does every success path keep completion, human approval, runtime integration, security and Git-delivery claims false?
9. Is one user-owned task/worktree residual explicitly reported instead of silently deleted or archived?
10. Is the task-worktree-only README mutation mechanically separated from stage-worktree allowed paths and bound to full-file digests?
11. Does the existing `ruff` runner run with cache disabled and leave the claim-bound snapshot unchanged?

## Internal disposition

- Scope is one host-managed task, not a cohort or runtime subagent platform.
- The local executable/HOME/credential blocker is removed because the script no longer launches Codex; source provenance becomes weaker
  and is explicitly fixed at `host_observed_unverified`.
- Baseline is captured only after a no-write handshake completes and before the unique coding turn.
- The target mutation and verification are intentionally simple; the experiment measures observation and evidence binding, not semantics.
- Native host task facts remain controller evidence and are not synthesized from repository JSON.
- The task-worktree-only mutation is bound to exact full-file digests; it does not add `README.md` to the stage worktree allowed paths.
- The bridge forces `RUFF_NO_CACHE=true`, with a real-runner no-cache/no-drift test required before the task launch.
- Plan remains blocked until epoch 5 mechanical validation and two fresh reviewer slots pass.

## Required independent review

- `codex-app-plan-a`: fresh empty-context reviewer, no current implementation conversation and no other reviewer conclusion.
- `codex-app-plan-b`: separate fresh empty-context reviewer with the same restrictions.
- Blocking threshold: P0/P1. P2/P3 require explicit disposition but do not silently expand scope.
- Both slots must review the same content-addressed packet; any plan change invalidates both receipts.
