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
1. **Implicit conflicts against the existing codebase** — requirements that contradict existing ADRs, break established
   patterns in `CLAUDE.md`, conflict with the current domain model in `src/fitinera/`, or violate conventions in
   `CONTRIBUTING.md`. Read `CLAUDE.md`, scan `docs/adrs/`, and search `src/fitinera/` before accepting any requirement.
1. **Ambiguities that hide conflicts** — vague requirements that seem compatible but would force contradictory
   implementation choices once an agent tries to write code.

When conflicts are detected, **push back via AskUserQuestion** — clearly state the conflict, why it matters, and propose
concrete alternatives. **Do not proceed to the next phase until conflicts are resolved.**

> **Seedling philosophy:** A seedling PRD is the operator's intent distilled into a draft document — it gives the skill
> a head start and reduces unnecessary round-trips. But a seedling is not sacred: if it contains conflicts, challenge
> them just as you would any other input.

______________________________________________________________________

## The Job

### Phase 0: Environment Setup

1. Read `$ARGUMENTS` (the text typed after `/prd`). If empty, ask the user for input using **AskUserQuestion**.
1. **Detect input type:**
   - If `$ARGUMENTS` is a path to an existing `.md` file → **seedling mode** (use the file as a baseline draft).
   - Otherwise → **text description mode** (generate from scratch).
1. Derive `<slug>` as a short, lowercase-kebab-case label:
   - Seedling mode: derive from the seedling document's title.
   - Text mode: derive from the feature description (e.g., "Account Rollover" → `account-rollover`).
1. Generate `<branch>` as `feat-<slug>` (e.g., `feat-account-rollover`).
1. Update `.claude/settings.json`: set `env.CLAUDE_CODE_TASK_LIST_ID` to `<branch>`.
1. Create the `plans/` directory if it does not exist:
   ```
   mkdir -p plans
   ```
1. Create a symlink so task files are accessible under `plans/<branch>`:
   ```
   ln -sf ~/.claude/tasks/<branch> plans/<branch>
   ```
   (This makes `plans/<branch>` a symlink to `~/.claude/tasks/<branch>`, creating both directories if needed.)

### Phase 1: Draft PRD (baseline)

1. If `plans/<branch>-prd.md` already exists, move it to `plans/archive/<branch>-prd.md` before continuing.

1. **Before generating anything:** Read `CLAUDE.md`, scan `docs/adrs/`, and search `src/fitinera/` for existing code
   related to the feature. Identify any conflicts between what is being requested and what already exists. This research
   is mandatory in both modes.

1. **Branch on input mode:**

   **Seedling mode:**

   - Read the seedling file. Preserve the author's structure, intent, and any existing sections.
   - Review the seedling for internal conflicts and conflicts against the existing codebase (from step 2).
   - Ask 2–3 targeted clarifying questions via **AskUserQuestion** focused on conflicts, gaps, and ambiguities (not
     repeating what the seedling already says).
   - Expand the seedling into a complete PRD, filling in all missing template sections.

   **Text description mode:**

   - Ask 3–5 clarifying questions via **AskUserQuestion** (focus on: problem/goal, core functionality, scope/boundaries,
     success criteria). At least one question must probe potential conflicts with existing functionality uncovered in
     step 2.
   - Generate a complete PRD from scratch.

1. The generated PRD must follow the [annotated example](#example-prd-annotated-reference) below and include **Design
   Considerations** and **Open Questions**.

1. Save to `plans/<branch>-prd.md`.

### Phase 2: Design refinement (questions + expand open questions)

1. Review the PRD's **Design Considerations** and ask a targeted series of design questions using **AskUserQuestion**.
1. **Explicitly cross-check** each proposed design choice against existing ADRs and `CLAUDE.md` patterns. If a design
   choice contradicts an existing decision, surface this as a conflict requiring resolution (potentially via a new ADR
   that supersedes the old one).
1. Append newly discovered questions to the **bottom of the Open Questions section** (keep existing; add an "Added in
   Phase 2" subsection).
1. Update `plans/<branch>-prd.md` with the refined design considerations and updated open questions.

### Phase 3: Final refinement (answer all open questions + final pass)

1. Ask the user **all remaining Open Questions** using **AskUserQuestion**.
1. Refine the PRD one final time based on the answers.
1. **Final conflict sweep:** Before saving, verify that no requirement in the PRD contradicts another, and that no
   requirement conflicts with the existing codebase as understood from the Phase 1 research. If any conflict is found,
   raise it via **AskUserQuestion** and resolve before saving.
1. Save the final version to `plans/<branch>-prd.md`.

> **Important:** Do NOT start implementing. Just create the PRD.

______________________________________________________________________

## Before Saving

- [ ] Phase 0 completed: `<branch>` chosen (`feat-<slug>`), `CLAUDE_CODE_TASK_LIST_ID` updated in
  `.claude/settings.json`, `plans/` directory exists, symlink `plans/<branch>` → `~/.claude/tasks/<branch>` created
- [ ] Input mode detected: seedling (file path) or text description
- [ ] `CLAUDE.md`, `docs/adrs/`, and `src/fitinera/` searched for conflicts before generating
- [ ] Phase 1 PRD includes all 9 sections, including Design Considerations and Open Questions
- [ ] Seedling mode: author's structure and intent preserved; only gaps/ambiguities questioned
- [ ] Used **AskUserQuestion** in each phase as needed
- [ ] Incorporated user's answers into the PRD after each refinement phase
- [ ] Phase 2 cross-checked all design choices against existing ADRs and `CLAUDE.md` patterns
- [ ] Phase 3 final conflict sweep completed — no intra-PRD contradictions, no codebase conflicts
- [ ] Developer stories are small, specific, and follow the story format in the annotated example below
- [ ] Functional requirements are numbered (`FR-###`) and unambiguous
- [ ] Any old `plans/<branch>-prd.md` is archived to `plans/archive/`
- [ ] Non-goals section clarifies Goal section boundaries
- [ ] Any newly discovered questions were appended to the bottom of **Open Questions** (with a phase marker)

______________________________________________________________________

## Example PRD (Annotated Reference)

> **[Guidance]** Brief description of the feature and the problem it solves. One paragraph max.

# Account Rollover

## 1. Introduction/Overview

> **[Guidance]** Describe the problem being solved and why it matters to the project. Keep it concise.

The fitinera pipeline currently lacks the ability to roll over balances between financial periods. When a period closes,
any remaining balance must carry forward to the next period's opening position. Without this, downstream flows produce
incorrect totals.

## 2. Goals

> **[Guidance]** Bullet-list what this feature accomplishes. Keep goals measurable.

- Enable period-close flows to emit a rollover transaction that seeds the subsequent period.
- Ensure rollover amounts are immutable once emitted (frozen dataclass).
- Provide a builder so callers can construct rollover parameters without long argument lists.

## 3. Developer Stories

> **[Guidance]** One story = one autonomous agent iteration. Each must fit in a single context window. Use the
> scaffold-first / implement-second pattern for any new or changed API surface. Story IDs follow format `FEAT-<slug>-NN`
> (two-digit zero-padded).

### FEAT-account-rollover-01: Scaffold RolloverParams and RolloverFlow API

**As a** developer, **I want** typed stubs for `RolloverParams` and `RolloverFlow` **so that** I can validate the API
surface and write tests before implementing real logic.

**Acceptance Criteria:**

- [ ] `RolloverParams` frozen dataclass exists in `src/fitinera/models/` with fields: `from_period_id`, `to_period_id`,
  `amount`, `account_id`
- [ ] `RolloverFlow` subclass exists in `src/fitinera/flows/` with `run()` stub raising `NotImplementedError`
- [ ] `RolloverParamsBuilder` exists and allows chained construction
- [ ] Tests exist in `tests/fitinera/` covering the expected API shape (tests will fail on `NotImplementedError`)
- [ ] Pre-commit passes (`uv run pre-commit run`)
- [ ] Tests written in DAMP style with Google-style docstrings

### FEAT-account-rollover-02: Implement RolloverFlow logic

**As a** developer, **I want** `RolloverFlow.run()` to produce a rollover transaction **so that** the pipeline correctly
carries balances across periods.

**Acceptance Criteria:**

- [ ] `RolloverFlow.run()` emits a `Transaction` carrying the rollover amount from `from_period_id` to `to_period_id`
- [ ] All scaffold-story tests now pass
- [ ] Edge cases covered: zero-amount skip, negative balance guard
- [ ] Pre-commit passes (`uv run pre-commit run`)
- [ ] TDD cycle followed: test first → implement → refactor

## 4. Functional Requirements

> **[Guidance]** Number every requirement. Each must be concrete, testable, and unmistakably in or out of scope.

- FR-1: `RolloverParams` must be immutable (`frozen=True`).
- FR-2: `RolloverFlow.run()` must return a `Transaction` object, not a raw dict.
- FR-3: A zero-amount rollover must be skipped (no transaction emitted).
- FR-4: `RolloverParamsBuilder` must provide a fluent interface (method chaining).

## 5. Non-Goals (Out of Scope)

> **[Guidance]** Be explicit about what this feature does NOT do. Prevents scope creep.

- No UI or API endpoint changes.
- No multi-currency conversion (out of scope for V1).
- No database migrations (fitinera uses in-memory computation only).

## 6. Design Considerations

> **[Guidance]** Architecture notes, relevant ADRs, known constraints.

- The scaffold-first / implement-second pattern is required per `CONTRIBUTING.md`.
- An ADR should be written if the rollover emission model differs from existing flow patterns.
- See ADR index in `docs/adrs/README.md` for existing decisions that may constrain this design.

## 7. Technical Considerations

> **[Guidance]** Environment, language, tooling constraints.

- Python ≥ 3.13
- Immutable dataclasses (`frozen=True`) for all value objects
- Parameter encapsulation via Builder pattern (per `CONTRIBUTING.md`)
- `uv run pre-commit run` must pass (lint + format + test)
- `uv run pytest tests/fitinera/ -v` must pass

## 8. Success Metrics

> **[Guidance]** How do we know this feature is done and correct?

- All acceptance criteria checked off.
- `uv run pre-commit run` exits 0 on all new/modified files.
- `uv run pytest tests/fitinera/ -v` exits 0 with no skipped rollover tests.

## 9. Open Questions

> **[Guidance]** Unresolved items that need answers before or during implementation. Phase 2 and Phase 3 will resolve
> these.

- OQ-1: Should zero-amount rollovers log a warning or fail silently?
- OQ-2: Is there an existing `Period` model, or should `from_period_id`/`to_period_id` be plain strings for now?
