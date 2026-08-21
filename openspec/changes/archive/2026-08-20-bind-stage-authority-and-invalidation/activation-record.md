# Prospective Activation Record

- Change: `bind-stage-authority-and-invalidation`
- Authority: pre-change RepoPilot L3 workflow plus the live direct-user confirmation bound by authority epoch 1.
- Activation point: after validator negative tests, supported Codex/OpenCode apply/archive entrypoint wiring, focused verification, and this record exist; applies prospectively to this stage's archive/merge/push and later stages.
- Claim ceiling: the repository hash proves only the bytes of this record. It does not prove user identity, host message provenance, or activation chronology; the live controller must verify those facts separately.
- Runtime boundary: process-only. No `app/**`, public API, runtime subagent, background Git, credential handling, PR automation, rebase, non-fast-forward push, or history rewrite capability is activated.

## Activation Preconditions Observed Before This Record

- Stage-authority focused tests: `49 passed` after RED failure for the absent validator and later manifest/delivery helpers.
- Combined authority, independent-review, and CLI structural tests: `120 passed`.
- Changed Python Ruff: PASS.
- OpenSpec strict change validation: PASS.
- OpenSpec all validation: `24 passed, 0 failed`.
- Full pytest: `599 passed, 3 failed`; the three failures are unchanged baseline failures outside this stage's allowed paths.
- Full Ruff: `96` inherited findings outside this stage's changed Python files; no changed-Python finding remains.
- PowerShell is unavailable on this host, so PowerShell wrapper scripts are not claimed as executed; their structural checks are reproduced separately before closeout.

This record activates the new gate prospectively. It does not retroactively claim that the new validator authorized its own plan or earlier implementation writes.
