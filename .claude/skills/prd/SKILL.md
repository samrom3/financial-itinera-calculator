---
name: prd
description: "Multi-phase PRD generator for fitinera features. Outputs plans/<branch>-prd.md ready for /prd-tasks."
argument-hint: "<feature description or path/to/seedling.md>"
user-invocable: true
disable-model-invocation: true
---

# PRD Generator

Create detailed Product Requirements Documents that are clear, actionable, and suitable for implementation by junior
developers or AI agents.

______________________________________________________________________

## Critical Review Mandate

> **Your primary job is to _critique_ the requirements you receive — not simply agree with them.** The user is paying
> for your judgement, not your compliance. An agent that rubber-stamps every input is worse than useless: it lets
> conflicting requirements slip through and causes implementing agents to get stuck with irreconcilable constraints.

Before accepting any requirement at face value, actively search for and surface:

1. **Explicit conflicts within the input** — contradictory requirements, goals that work against each other, acceptance
   criteria that are mutually exclusive.
2. **Implicit conflicts against the existing codebase** — requirements that contradict existing ADRs, break established
   patterns in `CLAUDE.md`, conflict with the current domain model in `src/fitinera/`, or violate conventions in
   `CONTRIBUTING.md`. Read `CLAUDE.md`, scan `docs/adrs/`, and search `src/fitinera/` before accepting any requirement.
3. **Ambiguities that hide conflicts** — vague requirements that seem compatible but would force contradictory
   implementation choices once an agent tries to write code.

When conflicts are detected, **push back** — clearly state the conflict, why it matters, and propose concrete
alternatives. **Do not proceed to the next phase until conflicts are resolved.**

> **Seedling philosophy:** A seedling PRD is the operator's intent distilled into a draft document — it gives the skill
> a head start and reduces unnecessary round-trips. But a seedling is not sacred: if it contains conflicts, challenge
> them just as you would any other input.

______________________________________________________________________

## The Job

### Phase 0: Environment Setup

1. Read `$ARGUMENTS` (the text typed after `/prd`). If empty, ask the user for input.
2. **Detect input type:**
   - If `$ARGUMENTS` is a path to an existing `.md` file → **seedling mode** (use the file as a baseline draft).
   - Otherwise → **text description mode** (generate from scratch).
3. Derive `<slug>` as a short, lowercase-kebab-case label:
   - Seedling mode: derive from the seedling document's title.
   - Text mode: derive from the feature description (e.g., "Account Rollover" → `account-rollover`).
4. Generate `<branch>` as `feat-<slug>` (e.g., `feat-account-rollover`).
5. Update `.claude/settings.json`: set `env.CLAUDE_CODE_TASK_LIST_ID` to `<branch>`.
6. Create the `plans/` directory if it does not exist:
   ```
   mkdir -p plans
   ```
7. Create a symlink so task files are accessible under `plans/<branch>`:
   ```
   ln -sf ~/.claude/tasks/<branch> plans/<branch>
   ```
   (This makes `plans/<branch>` a symlink to `~/.claude/tasks/<branch>`, creating both directories if needed.)

### Phase 1: Draft PRD (baseline)

1. If `plans/<branch>-prd.md` already exists, move it to `plans/archive/<branch>-prd.md` before continuing.

2. **Before generating anything:** Read `CLAUDE.md`, scan `docs/adrs/`, and search `src/fitinera/` for existing code
   related to the feature. Identify any conflicts between what is being requested and what already exists. This research
   is mandatory in both modes.

3. **Branch on input mode:**

   **Seedling mode:**

   - Read the seedling file. Preserve the author's structure, intent, and any existing sections.
   - Review the seedling for internal conflicts and conflicts against the existing codebase (from step 2).
   - Ask 2–3 targeted clarifying questions focused on conflicts, gaps, and ambiguities (not repeating what the seedling
     already says).
   - Expand the seedling into a complete PRD, filling in all missing template sections.

   **Text description mode:**

   - Ask 3–5 clarifying questions (focus on: problem/goal, core functionality, scope/boundaries, success criteria). At
     least one question must probe potential conflicts with existing functionality uncovered in step 2.
   - Generate a complete PRD from scratch.

4. The generated PRD must follow the annotated example in `references/example-prd.md` and include **Design
   Considerations** and **Open Questions**.

5. Developer stories should follow the scaffold-first / implement-second pattern for any new or changed API surface
   (see `/prd-tasks` for the authoritative definition of this pattern).

6. Save to `plans/<branch>-prd.md`.

### Phase 2: Design refinement (questions + expand open questions)

1. Review the PRD's **Design Considerations** and ask a targeted series of design questions.
2. **Explicitly cross-check** each proposed design choice against existing ADRs and `CLAUDE.md` patterns. If a design
   choice contradicts an existing decision, surface this as a conflict requiring resolution (potentially via a new ADR
   that supersedes the old one).
3. Append newly discovered questions to the **bottom of the Open Questions section** (keep existing; add an "Added in
   Phase 2" subsection).
4. Update `plans/<branch>-prd.md` with the refined design considerations and updated open questions.

### Phase 3: Final refinement (answer all open questions + final pass)

1. Ask the user **all remaining Open Questions**.
2. Refine the PRD one final time based on the answers.
3. **Final conflict sweep:** Before saving, verify that no requirement in the PRD contradicts another, and that no
   requirement conflicts with the existing codebase as understood from the Phase 1 research. If any conflict is found,
   raise it with the user and resolve before saving.
4. Save the final version to `plans/<branch>-prd.md`.

> **Important:** Do NOT start implementing. Just create the PRD.

______________________________________________________________________

## Before Saving

- [ ] Phase 0 completed: `<branch>` chosen (`feat-<slug>`), `CLAUDE_CODE_TASK_LIST_ID` updated in
  `.claude/settings.json`, `plans/` directory exists, symlink `plans/<branch>` → `~/.claude/tasks/<branch>` created
- [ ] Input mode detected: seedling (file path) or text description
- [ ] `CLAUDE.md`, `docs/adrs/`, and `src/fitinera/` searched for conflicts before generating
- [ ] Phase 1 PRD includes all 9 sections (see `references/example-prd.md`), including Design Considerations and Open
  Questions
- [ ] Seedling mode: author's structure and intent preserved; only gaps/ambiguities questioned
- [ ] User input gathered in each phase as needed
- [ ] Incorporated user's answers into the PRD after each refinement phase
- [ ] Phase 2 cross-checked all design choices against existing ADRs and `CLAUDE.md` patterns
- [ ] Phase 3 final conflict sweep completed — no intra-PRD contradictions, no codebase conflicts
- [ ] Developer stories are small, specific, and follow the scaffold-first pattern (see `/prd-tasks`)
- [ ] Functional requirements are numbered (`FR-###`) and unambiguous
- [ ] Any old `plans/<branch>-prd.md` is archived to `plans/archive/`
- [ ] Non-goals section clarifies Goal section boundaries
- [ ] Any newly discovered questions were appended to the bottom of **Open Questions** (with a phase marker)
