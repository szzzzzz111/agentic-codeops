## MODIFIED Requirements

### Requirement: Worktree Git Metadata Reads Use A Hardened Shared Runner

系统 SHALL use a shared fixed-argv Git metadata runner for V21 inspection metadata reads. The runner MUST use `shell=False`, `GIT_OPTIONAL_LOCKS=0`, an independent timeout, and an output byte hard limit enforced before metadata content is retained, decoded, or exposed.

The runner MUST kill and reap the Git subprocess on timeout, stdout oversize, reader failure, reader non-completion, process-start failure, non-zero exit, malformed output, or exception. It MUST safely degrade inspection without retry, repair, mutation, raw stderr, raw exception text, local absolute paths, or unbounded stdout exposure.

#### Scenario: Oversize metadata safely degrades inspection

- **WHEN** Git metadata output exceeds the hard limit
- **THEN** the metadata runner kills and reaps the process when possible
- **AND** inspection reports a safe partial result
- **AND** it MUST NOT retain, decode, or expose content beyond the configured cap
