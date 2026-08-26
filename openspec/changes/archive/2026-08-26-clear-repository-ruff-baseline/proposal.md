# Why

The restored canonical verifier now fails closed on the repository's inherited Ruff debt: 92 findings across 53 files. Until that finite mechanical inventory is cleared, the verification baseline cannot be repeatably green and the approved delivery cannot be merged or pushed.

# What Changes

- Apply only Ruff safe fixes to the frozen 53-file inventory.
- Resolve remaining lint rules with the smallest behavior-preserving edits and regression evidence.
- Update current-fact progress/handoff counts, then prove full pytest, full Ruff, canonical verification, scanners, OpenSpec, and diff checks are green.

# Impact

No public API, runtime contract, permission, dependency, persistence, or network-default change is authorized. Global/per-file ignores, blanket suppressions, unsafe fixes, and adjacent refactors are forbidden. The only suppression exceptions are three exact `TRY004` lines whose existing exception types are preserved and 14 existing `BLE001` outer fail-closed/fallback boundaries (one also covers `S110`); no new suppression site is authorized. The verification-runner long-term spec path is included solely for the reviewed archive sync.
