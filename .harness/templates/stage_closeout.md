# Stage Closeout Template

用于最终 runtime/test 状态已经验证和 review 后的收口。archive、merge、push 完成后只写一次
final handoff；不要为每个动作复制近似状态。

## Stage Result

- Stage: `<name>`
- Risk: `<low / medium / high>`
- Delivered: `<capability or process change>`
- Preserved boundaries: `<contracts and non-goals>`
- Archive: `<path or not applicable>`

## Verification

- Focused checks: `<commands and results>`
- Full verify: `<result / not required with reason>`
- OpenSpec validation: `<result>`
- Git diff checks: `<result>`

## Review Evidence

- Final runtime/test change: `<identifier or not applicable>`
- Internal review: `<findings / no findings and residual risk>`
- External review: `<findings / not required / not requested>`
- Remediation and re-review: `<result>`
- Stage Debt Sweep paths: `<actual paths inspected>`
- Remaining debt: `<PROGRESS location or none>`
- Reviewed change manifest/diff: `<paths and hashes>`
- Final implementation review set: `<path, required slots, host-retained packet hash>`
- Post-packet evidence tail: `<only review-set.json and delivery-binding.json / gate reopened>`
- Replay reviewed subject: `<all event/receipt projections included before packet freeze / none>`
- Replay activation/cohort: `<dormant; v1 through terminal / externally activated v2 with host evidence>`

## Archive And Integration

- Archive froze reviewed runtime: `<yes / not applicable>`
- Runtime changed after archive: `<no / reopened gates>`
- Authority binding: `<stage, epoch, record hash, scope digest, action ceiling; mechanical-only>`
- Live host authority: `<verified externally / absent / stale>`
- Exact candidate and target binding: `<candidate HEAD, effective endpoint fingerprint, target branch, authorized old tip>`
- Merge result: `<not attempted / exact ff-only verified / blocked>`
- Push result: `<not_attempted / unknown / verified>`
- Unknown-outcome reconciliation: `<same-endpoint read-only result / not applicable>`
- External terminal/replay state (v2 only): `<host query result; never written after candidate/push>`
- Live Git/OpenSpec state checked by: `<commands, not copied hashes>`

Report `technical_ready`, `human_authorized`, and `vcs_pushed` separately. After the final reviewed packet, only the
schema-valid two-file evidence tail may be written; after the exact candidate commit, final handoff is report-only and
must not create another repository write.

Do not report v2 active from repository validators, templates, hashes, or
fixtures. Until later `provider_neutral.stage_state_cas/v1` activation exists,
replay is dormant/mechanical-only and the introducing/in-flight v1 stages use
the pre-change process through terminal.

## Final Documentation

- PROGRESS updates: `<durable facts only>`
- HANDOFF updates: `<next-session context only>`
- Harness reset: `<done / active stage remains>`
- Next safe action: `<planning or blocker; do not create V-next here>`
