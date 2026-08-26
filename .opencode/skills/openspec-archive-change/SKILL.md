---
name: openspec-archive-change
description: Archive a completed change in the experimental workflow. Use when the user wants to finalize and archive a change after implementation is complete.
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
   `scripts/validate_stage_authority.py` with `--required-action archive`, the
   exact flags documented in `.harness/test_commands.md`, the full
   host-retained exact envelope including remote name, the actual implementation
   review set, required slot count, and host-retained reviewed packet hash. The
   validator must consume the exhaustive current review manifest and
   independent-review validator. Any mismatch blocks sync and archive before
   mutation. PASS is mechanical-only and does not establish live human
   authority.

   Replay is dormant until a separately reviewed host activation proves
   `provider_neutral.stage_state_cas/v1`. The introducing and all in-flight
   stages remain pre-change v1 through terminal and retain later-v1 authority
   replacement. Repository hashes, v2 templates, CLI flags, fixtures, or a
   shadow PASS cannot select v2 or authorize/block archive.

   For a future host-activated v2 cohort only, authority core precedes replay;
   host-retained workspace/terminal/gate snapshots and event/receipt heads are
   mandatory. Archive may mutate only at the exact `archive` frontier (or a
   code-owned no-change transition), never through an unaffected bypass.

5. **Assess delta spec sync state**

   Check for delta specs at `openspec/changes/<name>/specs/`. If none exist, proceed without sync prompt.

   **If delta specs exist:**
   - Compare each delta spec with its corresponding main spec at `openspec/specs/<capability>/spec.md`
   - Determine what changes would be applied (adds, modifications, removals, renames)
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
- After activation, never downgrade a failed/missing shared archive gate to a
  warning or interactive override
- Keep replay dormant for v1; an activated v2 stage requires exact-frontier
  equality and host-retained CAS state before sync/archive
- Archive does not authorize merge or push; those remain controller-only
