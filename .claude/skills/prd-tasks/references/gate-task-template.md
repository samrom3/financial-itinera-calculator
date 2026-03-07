# Back-Pressure Gate Task Template

This is a reusable template for the `GATE-<slug>-01` task description. When creating the gate task via `TaskCreate`,
substitute `<slug>` and `<branch>` with the actual values, then use the text below as the task description.

______________________________________________________________________

## Gate Task Description (copy into TaskCreate)

```
You are the back-pressure gate agent. Perform all five checks below IN ORDER.

## Check 1 — Documentation–code alignment

Verify that all docs/, README.md, CONTRIBUTING.md content matches the implemented code.

- If mismatched AND the PRD makes it clear which is correct → fix the out-of-sync artifact.
- If mismatched AND the PRD is ambiguous → ask the user to resolve the difference. Append the
  resolution to a new "Implementation Conflict Resolutions" section at the bottom of the PRD file
  (plans/<branch>-prd.md). Do not modify any other section of the PRD.

## Check 2 — ADR sync

Verify that all applicable design choices made during implementation have been documented as ADRs
(per .agents/skills/writing-adrs/SKILL.md) and that each ADR's Status field is set correctly
(Accepted, Rejected, Superseded, etc.). If ADRs are out of sync, update them and re-validate.

## Check 3 — Pre-commit checks

Run: uv run pre-commit run
This includes unit tests. Must exit 0.

## Check 4 — Acceptance criteria

Verify every acceptance criterion in each developer story in the PRD has been met.

## Check 5 — Success metrics

Verify every success metric listed in the PRD's Success Metrics section has been met.

## Progress file logging

After every check (pass or fail) and after every user interaction, append a summary to
plans/<branch>-progress.txt. Use this format:

## [Date/Time] - GATE-<slug>-NN
- Checks passed: [list]
- Checks failed: [list with details]
- User decisions: [any questions asked and how the user responded]
- Remediation tasks created: [list of task IDs, or "none"]
- Next gate: [GATE-<slug>-NN+1 if created, or "N/A — all checks passed"]
---

## Failure escalation

If checks 1–2 fail, fix them in-place as described above.

If checks 3–5 fail:

1. ITERATION GUARD: If the current gate task suffix is -04 or higher, ask the user before
   proceeding. The message must include:
   - The current gate iteration number.
   - A summary of which checks have been failing and whether the same checks have failed
     repeatedly across prior gate iterations (recurring) or are new failures — read
     plans/<branch>-progress.txt to determine this.
   - What problems still remain and what remediation tasks would be created if the user approves.
   - A clear question: should the escalation proceed, or should the user intervene directly?
   Do not proceed with steps 2–3 until the user responds. This guard applies on every gate
   iteration from -04 onward.

2. Use TaskCreate for each discrete problem category to create remediation tasks.

3. Create another GATE-<slug>-NN task (increment the suffix) that is is_blocked_by all newly
   created remediation tasks. This creates a re-validation loop with an audit trail.
```

______________________________________________________________________

## Task format reminder

- **Subject:** `GATE-<slug>-01: Final back-pressure gate check`
- **Dependencies:** `is_blocked_by` **all** `DOC-` and `FEAT-` tasks. Blocks nothing.
- **Numbering:** Each successive gate increments its suffix (`-01`, `-02`, `-03`, …).
