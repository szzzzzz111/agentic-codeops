## ADDED Requirements

### Requirement: List safe repository files

The system SHALL provide a read-only `list_files(repo_path)` tool that returns allowed text-like files relative to `repo_path`.

#### Scenario: Normal files are listed

- **WHEN** a repository contains ordinary source files
- **THEN** `list_files` returns those files as relative paths

#### Scenario: Unsafe files are skipped

- **WHEN** a repository contains ignored directories, hidden directories, sensitive files, or binary files
- **THEN** `list_files` omits those entries

### Requirement: Read safe repository files

The system SHALL provide a read-only `read_file(repo_path, file_path, max_chars)` tool that reads text files inside `repo_path` and limits returned content.

#### Scenario: Repository file is read

- **WHEN** `read_file` targets an allowed file inside `repo_path`
- **THEN** it returns UTF-8 text content up to `max_chars`

#### Scenario: Repository escape is rejected

- **WHEN** `read_file` targets a path outside `repo_path`
- **THEN** it rejects the request

#### Scenario: Sensitive file is rejected

- **WHEN** `read_file` targets a sensitive file such as `.env` or key material
- **THEN** it rejects the request

### Requirement: Search safe repository files

The system SHALL provide a read-only `search_code(repo_path, keyword, max_results)` tool that searches allowed text files and returns file path, line number, and line text.

#### Scenario: Keyword match returns location

- **WHEN** an allowed file contains the search keyword
- **THEN** `search_code` returns a result with `file_path`, `line_number`, and `line_text`

#### Scenario: Missing keyword returns empty results

- **WHEN** no allowed file contains the keyword
- **THEN** `search_code` returns an empty list

#### Scenario: Sensitive content is not returned

- **WHEN** a sensitive file contains the keyword
- **THEN** `search_code` does not return content from that file

### Requirement: File tools are read-only

Repository file tools MUST NOT write files, delete files, or execute shell commands.

#### Scenario: Tool capability boundary

- **WHEN** file tools are used
- **THEN** they only list, read, or search allowed repository text files
