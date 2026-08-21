---
name: openspec-archive-change
description: Use when the user explicitly asks to archive or finalize a completed OpenSpec change after implementation and review are complete.
license: MIT
compatibility: Requires openspec CLI.
metadata:
  author: openspec
  version: "1.0"
  generatedBy: "1.3.1"
---

Archive a completed change in the experimental workflow.

**Input**: Optionally specify a change name. If omitted, check if it can be inferred from conversation context. If vague or ambiguous you MUST prompt for available changes.

**Steps**

1. **If no change name provided, prompt for selection**

   Run `openspec list --json` to get available changes. Use the **AskUserQuestion tool** to let the user select.

   Show only active changes (not already archived).
   Include the schema used for each change if available.

   **IMPORTANT**: Do NOT guess or auto-select a change. Always let the user choose.

2. **Check artifact completion status**

   Run `openspec status --change "<name>" --json` to check artifact completion.

   Parse the JSON to understand:
   - `schemaName`: The workflow being used
   - `artifacts`: List of artifacts with their status (`done` or other)

   **If any artifacts are not `done`:**
   - Display warning listing incomplete artifacts
   - Use **AskUserQuestion tool** to confirm user wants to proceed
   - Proceed if user confirms

3. **Check task completion status**

   Read the tasks file (typically `tasks.md`) to check for incomplete tasks.

   Count tasks marked with `- [ ]` (incomplete) vs `- [x]` (complete).

   **If incomplete tasks found:**
   - Display warning showing count of incomplete tasks
   - Use **AskUserQuestion tool** to confirm user wants to proceed
   - Proceed if user confirms

   **If no tasks file exists:** Proceed without task-related warning.

4. **Run the stage-authority archive gate**

   After activation, archive and any pre-archive spec sync are fail-closed
   mutations. Before offering or invoking any sync action, run
   `scripts/validate_stage_authority.py --required-action archive` with the
   exact flags documented in `.harness/test_commands.md` and the full
   host-retained expected stage/epoch/record/risk/scope/base/action/remote/
   endpoint/branch/tip envelope. Also pass the actual mechanically valid final
   implementation review set, required slot count, and host-retained reviewed
   packet hash. Do not source expected values from the repository record.

   The validator must consume the current exhaustive review-subject manifest
   and actual independent-review validator. Missing/stale authority,
   insufficient ceiling, packet/manifest drift, unexpected review metadata,
   or any preflight failure blocks sync and archive before mutation; user
   confirmation of an incomplete-task warning cannot override this gate.
   Validator success remains mechanical-only and does not prove live human
   authority.

5. **Assess delta spec sync state**

   Check for delta specs at `openspec/changes/<name>/specs/`. If none exist, proceed without sync prompt.

   **If delta specs exist:**
   - Compare each delta spec with its corresponding main spec at `openspec/specs/<capability>/spec.md`
   - Determine what changes would be applied (adds, modifications, removals, renames)
   - Validate operation types before archive:
     - every requirement under `MODIFIED Requirements` or `REMOVED Requirements` MUST have an exact matching requirement header in the corresponding main spec
     - every genuinely new requirement MUST be under `ADDED Requirements`
     - a delta may contain separate `MODIFIED Requirements` and `ADDED Requirements` sections when it both changes an existing requirement and adds a new one
   - Treat an operation/header mismatch as a blocker to fix before running archive. `openspec validate <change>` passing does not prove archive sync will succeed.
   - Show a combined summary before prompting

   **Prompt options:**
   - If changes needed: "Sync now (recommended)", "Archive without syncing"
   - If already synced: "Archive now", "Sync anyway", "Cancel"

   If user chooses sync, use Task tool (subagent_type: "general-purpose", prompt: "Use Skill tool to invoke openspec-sync-specs for change '<name>'. Delta spec analysis: <include the analyzed delta spec summary>"). A sync mutation invalidates the pre-sync manifest and review packet: rerun affected verification, regenerate the exhaustive manifest/inventory, refresh every required implementation-review slot, and rerun `scripts/validate_stage_authority.py --required-action archive` against the new host-retained packet before proceeding. If sync is skipped or unnecessary, the first gate remains the archive preflight.

6. **Perform the archive**

   Create the archive directory if it doesn't exist:
   ```bash
   mkdir -p openspec/changes/archive
   ```

   Generate target name using current date: `YYYY-MM-DD-<change-name>`

   **Check if target already exists:**
   - If yes: Fail with error, suggest renaming existing archive or using different date
   - If no: Move the change directory to archive

   ```bash
   mv openspec/changes/<name> openspec/changes/archive/YYYY-MM-DD-<name>
   ```

   If the archive command aborts during spec sync, confirm no files changed, repair the delta operation/header mismatch, rerun strict change validation, and retry archive. Do not manually move a partially synced change.

7. **Display summary**

   Show archive completion summary including:
   - Change name
   - Schema that was used
   - Archive location
   - Whether specs were synced (if applicable)
   - Note about any warnings (incomplete artifacts/tasks)

**Output On Success**

```
## Archive Complete

**Change:** <change-name>
**Schema:** <schema-name>
**Archived to:** openspec/changes/archive/YYYY-MM-DD-<name>/
**Specs:** ✓ Synced to main specs (or "No delta specs" or "Sync skipped")

All artifacts complete. All tasks complete.
```

**Guardrails**
- Always prompt for change selection if not provided
- Use artifact graph (openspec status --json) for completion checking
- Don't block archive on warnings - just inform and confirm
- Preserve .openspec.yaml when moving to archive (it moves with the directory)
- Show clear summary of what happened
- If sync is requested, use openspec-sync-specs approach (agent-driven)
- If delta specs exist, always run the sync assessment and show the combined summary before prompting
- After activation, never downgrade a failed/missing stage-authority archive
  preflight to a warning or interactive override
- Archive does not authorize merge or push; return those actions to the
  controller-owned `repo-stage-workflow`

**Evals**

Use `references/evals.md` when changing this skill's description, archive preconditions, or sync-failure handling. Keep positive, negative, and edge cases current.
