# Tasks

## 1. Freeze And Plan

- [x] Freeze planning base, remote target, exact 92-finding/53-file inventory, allowlist, non-goals, verification contract, and stop conditions.
- [x] Complete independent plan review and authority implement preflight.

## 2. Safe Mechanical Fixes

- [x] Apply Ruff safe fixes only; review the resulting import and syntax changes.
- [x] Recount residual rules and confirm no path escape.

## 3. Manual Residual Cleanup

- [x] Fix remaining BLE001, B023, RUF046, S110, FURB162 and other frozen residuals with minimal behavior-preserving edits; preserve the three existing TRY004 exception types and the 14 existing outer boundary catches (one same-line S110) using only the authorized exact line-level suppressions.
- [x] Run the full regression suite over every nontrivial manual edit.

## 4. Verification

- [x] Full pytest passes (`971 passed`).
- [x] Full Ruff and canonical `python -I scripts/verify.py` pass without skipped tools.
- [x] Stage-doc, skill-eval, OpenSpec, and diff checks pass (OpenSpec `25 passed, 0 failed`).

## 5. Review And Delivery

- [ ] Archive the change, freeze exhaustive implementation packet, and close independent review findings.
- [ ] Validate evidence tail and exact staged index; create the second finite candidate commit.
- [ ] Revalidate live target, ff-only merge both commits, exact-old-OID lease push, and verify remote parity.
