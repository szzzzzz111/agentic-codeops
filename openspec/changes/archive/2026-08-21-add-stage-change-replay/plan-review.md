# Plan Review

## Scope And Claim Ceiling

- Stage: `add-stage-change-replay`
- Risk / human depth: `high` / `L3`
- Final plan packet: `b8f6172b43d16ebcaf0fb9cc649b7cc4f5575bf1824c51c6062bc78648dd5ec6`
- Repository receipts and validator PASS prove only mechanical consistency. Direct-user authority, reviewer dispatch provenance, activation chronology, the future host CAS capability, implementation readiness, and Git delivery remain external.
- The planned replay validator and v2 templates are dormant. This introducing stage and every in-flight v1 stage remain on the pre-change v1 workflow through terminal.

## Review Slots

- Slot A: `/root/change_replay_plan_review_a`, `fork_turns=none`, no other current-stage first-round result visible.
- Slot B: `/root/change_replay_plan_review_b`, `fork_turns=none`, no other current-stage first-round result visible.
- Both slots independently rebuilt every declared packet and remained read-only.
- Same-model correlation remains. Slot A accidentally observed one historical review set from a different completed stage while locating the receipt schema; it reported that exposure, did not use it as current-stage evidence, and did not view Slot B's current-stage conclusion.

## Complete Finding Lineage

### Slot A

- First round, packet `d066a47ce82d870da9efa85849f3472cfebd00015ff0ce6fa5f1159c5bdd5152`: opened `A-CR-P1-001` through `A-CR-P1-005`, `A-CR-P2-006`, and `A-CR-P2-007`.
- First remediation, packet `facd5d30ab8ae9160939b8b35c8054ed24136c3ace4fcef0931cc19439167c55`: closed the original seven and opened `A-CR-RR-P1-008` and `A-CR-RR-P1-009`.
- Second remediation, packet `dd6ff36da41ecae6ed7ed1e7bb36fdff9a5b545cd223c4a10a1f7a23f54acd46`: closed `A-CR-RR-P1-008` and `A-CR-RR-P1-009`; `READY / NO_FINDINGS`.
- Template/cohort refresh, packet `dafd53dcf7752ed8210a96b5d3554ada87249cb0ae2c9511ff064840a5048f2e`: `READY / NO_FINDINGS`.
- Final exact refresh, packet `b8f6172b43d16ebcaf0fb9cc649b7cc4f5575bf1824c51c6062bc78648dd5ec6`: `READY / NO_FINDINGS`; all nine Slot A findings closed.

### Slot B

- First round, packet `d066a47ce82d870da9efa85849f3472cfebd00015ff0ce6fa5f1159c5bdd5152`: opened `CRPB-P1-001` through `CRPB-P1-005`, `CRPB-P2-006`, and `CRPB-P2-007`.
- First remediation, packet `facd5d30ab8ae9160939b8b35c8054ed24136c3ace4fcef0931cc19439167c55`: closed the original seven and opened `CRPB-P1-008`, `CRPB-P1-009`, `CRPB-P1-010`, and `CRPB-P2-011`.
- Second remediation, packet `dd6ff36da41ecae6ed7ed1e7bb36fdff9a5b545cd223c4a10a1f7a23f54acd46`: closed `CRPB-P1-008` through `CRPB-P2-011` and opened `CRPB-P1-012`.
- Template/cohort refresh, packet `dafd53dcf7752ed8210a96b5d3554ada87249cb0ae2c9511ff064840a5048f2e`: partially remediated `CRPB-P1-012`, which remained open because proposal/checklist summaries still conflicted.
- Final exact refresh, packet `b8f6172b43d16ebcaf0fb9cc649b7cc4f5575bf1824c51c6062bc78648dd5ec6`: closed `CRPB-P1-012`; `READY / NO_FINDINGS`; all twelve Slot B findings closed.

## Final Plan Contract

- The repository implementation is a dormant, `mechanical_consistency_only` validator/model. It does not claim `provider_neutral.stage_state_cas/v1` exists and cannot activate itself.
- Current Codex/OpenCode entrypoints retain the pre-change gate. A later separately reviewed and direct-user-approved host-integration stage is required before blocking replay can apply to newly created v2 stages.
- Introducing and in-flight v1 stages, including owner-authorized replacement epochs, stay on the pre-change later-v1 path without replay events until terminal.
- Host state for any future activation must bind the initial workspace identity; sibling clones, linked worktrees, symlink roots, and caller-selected roots cannot reuse it.
- Delivery v2 binds only exact pre-candidate inputs; it never contains a future candidate/tree OID and cannot be rewritten after candidate creation.

## External Facts

- The controller observed both reviewer dispatches and their `fork_turns=none` configuration in the current host task; repository bytes do not machine-prove that provenance.
- The independent-review gate predates this stage. Its activation reference is checked mechanically, while activation chronology remains an external controller check.
- Controller execution after the final plan bytes: strict change validation PASS, all OpenSpec validation `24 passed, 0 failed`, and `git diff --check` PASS.
- Implementation has not started. No validator behavior, tests, host CAS adapter, archive, candidate, merge, or push is established by this plan review.
