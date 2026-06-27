## ADDED Requirements

### Requirement: Current Documentation Facts Have Narrow Ownership

RepoPilot documentation SHALL avoid duplicating volatile current-stage facts
across multiple durable files. Each current-facing document MUST keep to its
owned fact type:

- `README.md` owns the human-facing project facade, current capability
  snapshot, quick start, and links to deeper docs.
- `docs/ARCHITECTURE.md` owns stable runtime boundaries and durable
  relationships between components.
- `docs/PROGRESS.md` owns stage history, durable decisions, validation
  evidence, and unresolved debt.
- `docs/AGENT_RULES.md` owns long-term collaboration, branch, review, debt
  sweep, and documentation ownership rules.
- `HANDOFF_TO_NEXT_CHAT.md` owns next-session action context, blockers, and
  safe next steps.
- `docs/FEATURE_LIST.json` owns acceptance-oriented capability inventory and
  pass/fail status.
- `.harness/allowed_files.md` and `.harness/review_checklist.md` own the active
  stage write boundary and review gate evidence.

#### Scenario: Stage closeout updates current facts

- **WHEN** a stage is archived, merged, pushed, or otherwise changes current
  stage state
- **THEN** the agent updates only documents whose owned facts changed
- **AND** it avoids repeating the same volatile status in unrelated documents

#### Scenario: Architecture document references recent stages

- **WHEN** `docs/ARCHITECTURE.md` mentions a recent stage
- **THEN** the wording describes stable architecture boundaries or implemented
  runtime relationships
- **AND** it does not describe transient implementation tasks as current work

### Requirement: Volatile Repository State Comes From Live Commands

RepoPilot SHALL treat Git and OpenSpec commands as the source of truth for
branch, HEAD, remote sync, and active OpenSpec change state. Durable documents
MUST NOT require repeated exact HEAD or remote hash updates across multiple
files.

#### Scenario: Next session needs current repository state

- **WHEN** an agent starts or resumes a stage
- **THEN** it checks live `git status --short --branch`, recent commits, remote
  sync when needed, and `openspec list`
- **AND** it does not rely on stale prose as proof of current Git/OpenSpec state

### Requirement: Drift Checks Target Current Facts Without Rewriting History

RepoPilot deterministic documentation checks SHALL target current-state files
and current guidance sections for mechanically searchable stale wording. They
MUST NOT treat archived OpenSpec changes or historical PROGRESS entries as
current truth merely because they contain old stage wording.

#### Scenario: Stale wording appears in current guidance

- **WHEN** README, HANDOFF, Harness files, FEATURE_LIST notes, or the current
  PROGRESS guidance describe a completed stage as future, pending, unmerged, or
  backlog
- **THEN** the stage docs scan fails with a clear finding

#### Scenario: Historical archive contains old roadmap wording

- **WHEN** an archived OpenSpec change or historical PROGRESS entry contains
  wording that was true for that past stage
- **THEN** deterministic drift checks do not fail solely because of that
  historical wording
