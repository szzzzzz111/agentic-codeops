# Context

The planning base already contains deterministic fail-closed verification. The sole repository gate failure is the frozen Ruff inventory: 92 findings in 53 files. The cleanup spans many files but is mechanically narrow.

# Decisions

1. Run `ruff check . --fix` without `--unsafe-fixes`; inspect the exact diff.
2. Resolve remaining rules by rule family: bind loop variables explicitly, preserve established exception types, narrow exception handling where behavior is known, and make syntax-only modernizations.
3. Do not suppress findings through config, global ignore, per-file ignore, or blanket `noqa`. The only allowed line-level suppressions are the three frozen `TRY004` raises, plus the 14 existing `BLE001` outer fail-closed/fallback boundaries (the best-effort worktree failure-state update may include `S110` on the same line). Every site requires a rationale; no new site is authorized.
4. Preserve behavior with focused tests for every non-import manual edit, then run full pytest and the canonical verifier.
5. Stop on any new affected path, semantic ambiguity, test regression, or live Git target drift.

# Risk Controls

- Safe autofix and manual edits are reviewed separately.
- Exception and time-parsing edits receive direct regression coverage or are rejected.
- The final packet is archived and independently reviewed before candidate construction.
