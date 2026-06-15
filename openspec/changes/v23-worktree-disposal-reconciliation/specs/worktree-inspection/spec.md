## ADDED Requirements

### Requirement: Worktree Git Metadata Reads Use A Hardened Shared Runner

系统 SHALL use a shared fixed-argv Git metadata runner for V21 inspection metadata reads. The runner MUST use `shell=False`, `GIT_OPTIONAL_LOCKS=0`, an independent timeout, and an output byte hard limit enforced before reading content.

Timeout, oversize, non-zero exit, malformed output, or exception MUST safely degrade inspection without retry or mutation.

#### Scenario: Oversize metadata safely degrades inspection

- **WHEN** Git metadata output exceeds the hard limit
- **THEN** inspection reports a safe partial result
- **AND** it MUST NOT read or expose the oversized content
