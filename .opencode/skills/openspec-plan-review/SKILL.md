---
name: openspec-plan-review
description: Use for independent OpenCode review of RepoPilot OpenSpec stage plans before implementation.
---

# OpenSpec Plan Review

Review the stage plan only. Do not edit files or implement code.

## Workflow

1. For first-round review, create a new isolated review session. It
   MUST NOT reuse an implementation session or a session containing another first-round
   review conclusion. A candidate existing session is acceptable only when host
   evidence proves it contains neither.
2. Use session lookup/reuse only for the same slot's remediation re-review or
   to recover the same timed-out review attempt:

   ```powershell
   opencode session list
   opencode run --session <session_id> "<adversarial plan review brief>"
   ```

3. If terminal output times out or does not show a final answer, inspect the
   same session for final assistant review text before deciding the gate failed.
4. Report severity-ordered findings with trigger, impact, and recommendation.
5. If there are no blockers, state inspected areas and residual risk.

## Review Focus

- Scope drift against OpenSpec proposal/design/tasks/spec deltas.
- Mismatch between allowed files, review checklist, and planned implementation.
- Roadmap or README claims that make future capabilities sound implemented.
- Missing TDD, validation, internal review, or risk-contract required independent review slots and validated receipts.
- Runtime boundary violations such as `/chat` contract changes, provider wiring,
  default CI changes, promotion, commit/push automation, subagents, or connectors.

## Gate Rule

OpenCode review is complete only when final assistant review text exists, the
receipt binds the required final baseline, and all findings have been triaged.
A timeout alone is not success or failure. Session reuse never creates an extra
independent review slot.
