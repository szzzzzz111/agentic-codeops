## ADDED Requirements

### Requirement: Repository uses staged development workflow

The repository SHALL develop one small stage at a time and MUST keep stage scope explicit.

#### Scenario: New stage starts

- **WHEN** a new stage begins
- **THEN** the agent confirms the branch, current status, and current phase before modifying files

### Requirement: Allowed files define write scope

The repository SHALL maintain `.harness/allowed_files.md` as the current phase write boundary.

#### Scenario: Implementation begins

- **WHEN** an agent starts implementation
- **THEN** it only edits files allowed by `.harness/allowed_files.md`

### Requirement: Review checklist defines acceptance risks

The repository SHALL maintain `.harness/review_checklist.md` for current phase review criteria.

#### Scenario: Review occurs

- **WHEN** a change is reviewed
- **THEN** the reviewer checks scope, allowed files, tests, docs, architecture boundaries, and Roadmap accuracy

### Requirement: Verification is deterministic

The repository SHALL prefer deterministic verification using `scripts/verify.ps1`, pytest, and ruff.

#### Scenario: Change is completed

- **WHEN** a change is ready for review or merge
- **THEN** `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` is run or the inability to run it is documented

### Requirement: Handoff and progress stay current

The repository SHALL update `docs/PROGRESS.md` and `HANDOFF_TO_NEXT_CHAT.md` at the end of meaningful work.

#### Scenario: Work session ends

- **WHEN** a stage changes state or implementation completes
- **THEN** progress and handoff documents reflect branch, completed work, validation, unfinished items, and next steps

### Requirement: OpenSpec is project-level development workflow

The repository SHALL use OpenSpec for project-level proposal, design, tasks, specs, and archive when starting substantial new stages.

#### Scenario: New substantial stage

- **WHEN** a new substantial stage is planned
- **THEN** the agent creates or updates an OpenSpec change before implementation

### Requirement: OpenSpec does not imply runtime capability

OpenSpec, Superpowers, MCP, plugin, and external skill concepts MUST NOT be treated as RepoPilot runtime capabilities unless a stage spec explicitly opens that scope.

#### Scenario: OpenSpec workflow exists

- **WHEN** OpenSpec files or project-level AI skills are present
- **THEN** the application runtime behavior remains unchanged unless a dedicated product spec requires otherwise
