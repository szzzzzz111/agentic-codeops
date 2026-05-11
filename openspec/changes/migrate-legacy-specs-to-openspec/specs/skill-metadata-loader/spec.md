## ADDED Requirements

### Requirement: Discover skill metadata files

The system SHALL provide `load_skill_metadata(repo_path)` to discover `.agents/skills/*/SKILL.md` files inside the repository.

#### Scenario: Skill metadata file exists

- **WHEN** a repository contains `.agents/skills/example/SKILL.md`
- **THEN** the loader considers it a skill metadata source

#### Scenario: Skills directory is missing

- **WHEN** `.agents/skills` does not exist
- **THEN** the loader returns an empty list

### Requirement: Parse minimal frontmatter metadata

The loader SHALL parse only YAML frontmatter fields `name` and `description`, and SHALL return those fields with relative repository `path`.

#### Scenario: Valid metadata

- **WHEN** `SKILL.md` contains valid `name` and `description` frontmatter
- **THEN** the loader returns `name`, `description`, and relative `path`

#### Scenario: Stable ordering

- **WHEN** multiple skills exist
- **THEN** the loader returns them in stable path order

### Requirement: Skill metadata output is bounded and safe

The loader MUST NOT execute skills, load complete skill bodies, return complete skill bodies, inject skill content into prompts, or return local absolute paths.

#### Scenario: Skill body is present

- **WHEN** `SKILL.md` has body content after frontmatter
- **THEN** the returned metadata does not include that body content

#### Scenario: Path output

- **WHEN** metadata is returned
- **THEN** `path` is relative to `repo_path`

### Requirement: Invalid skill metadata fails fast

The loader SHALL fail fast for missing required metadata, malformed frontmatter lines, unclosed frontmatter, or frontmatter that exceeds configured read limits.

#### Scenario: Missing description

- **WHEN** `SKILL.md` lacks `description`
- **THEN** the loader raises an error

#### Scenario: Invalid frontmatter line

- **WHEN** frontmatter contains a non-empty non-comment line without `:`
- **THEN** the loader raises an error

#### Scenario: Unclosed frontmatter is bounded

- **WHEN** frontmatter does not close before the read limit
- **THEN** the loader raises an error without reading unbounded content

### Requirement: Skill metadata loader is not chat decision logic

The current skill metadata loader MUST NOT be connected to `/chat`, `CodeAgent`, `ToolExecutor`, real LLM selection, progressive disclosure, or skill execution.

#### Scenario: Chat request

- **WHEN** `/chat` handles a user request
- **THEN** it does not use skill metadata for decision-making
