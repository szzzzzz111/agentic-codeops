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

## Archive And Integration

- Archive froze reviewed runtime: `<yes / not applicable>`
- Runtime changed after archive: `<no / reopened gates>`
- Merge/push authorization and result: `<result>`
- Live Git/OpenSpec state checked by: `<commands, not copied hashes>`

## Final Documentation

- PROGRESS updates: `<durable facts only>`
- HANDOFF updates: `<next-session context only>`
- Harness reset: `<done / active stage remains>`
- Next safe action: `<planning or blocker; do not create V-next here>`
