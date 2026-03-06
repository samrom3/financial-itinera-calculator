---
name: prd-tasks
description: "Converts a fitinera PRD into dependency-ordered TaskCreate calls with scaffold-first pattern. Run after /prd."
user-invocable: true
disable-model-invocation: true
---

# PRD Task Creator

Converts existing PRDs into tasks via Claude's `TaskCreate` tool for autonomous agent execution.

______________________________________________________________________

## The Job

### Phase 0: Pre-Flight Validation

Before doing anything else, run these checks in order. **Stop and surface each issue as you encounter it.**

#### Step 1 — Validate the symlink

1. Read `.claude/settings.json` and extract the value of `env.CLAUDE_CODE_TASK_LIST_ID` → this is `<branch>`.
1. Check that `plans/<branch>` exists **and** is a symlink pointing to `~/.claude/tasks/<branch>`.
1. Determine the currently checked-out git branch (`git branch --show-current`).
1. Compare the git branch name to `<branch>`:
   - **If they match** — proceed to Step 2.
   - **If they do NOT match** — tell the user:
     > The current git branch (`<actual-git-branch>`) does not match the task list branch (`<branch>`). Would you like
     > to continue anyway, or pause so you can check out a different branch?
   - Use **AskUserQuestion** and wait for their response. If they say pause, **stop here** — do not continue.

#### Step 2 — Validate branch name vs Claude settings

1. Confirm that `<branch>` in `.claude/settings.json` matches the branch slug used in the PRD file's story IDs.
1. **If they do not match**, warn the user:
   > ⚠️ The `CLAUDE_CODE_TASK_LIST_ID` in `.claude/settings.json` (`<branch>`) does not appear to match the PRD's branch
   > context. You may need to update settings or re-run the `/prd` skill.

#### Step 3 — Warn about stale Claude Code session

1. If the **PRD skill** (`prd`) was invoked earlier in this same Claude Code session (i.e., `.claude/settings.json` was
   updated during this session), the running session may still be using the **old** `CLAUDE_CODE_TASK_LIST_ID` value.
1. In that case, warn the user:
   > ⚠️ It looks like the PRD skill was run during this session, which updated `.claude/settings.json`. You need to
   > **restart your Claude Code session** so the tasks agent picks up the new `CLAUDE_CODE_TASK_LIST_ID` value. Please
   > restart and re-invoke this skill.
1. Use **AskUserQuestion** to confirm whether the user wants to continue or restart. If they say restart, **stop here**.

Once all three steps pass, proceed to Phase 1.

______________________________________________________________________

### Phase 1: Convert PRD to Tasks

Take the PRD at `plans/<branch>-prd.md` and create one task per developer story using `TaskCreate`.

______________________________________________________________________

## TaskCreate Arguments

For each developer story extracted from the PRD, call `TaskCreate` with these arguments:

### Subject

```
FEAT-<slug>-##: [Story title]
```

(Sequential, two-digit zero-padded, e.g. `FEAT-account-rollover-01`.)

### Description

Full story description, expanded acceptance criteria, plus the Required Final Criteria appended at the bottom:

```
As a developer, I want [action] so that [benefit].

Acceptance Criteria:
- [ ] [Concrete, testable criterion]
- [ ] [Additional criteria from PRD…]
- [ ] Pre-commit passes (uv run pre-commit run)
- [ ] Tests written in DAMP style with Google-style docstrings
- [ ] TDD cycle followed: test first → implement → refactor
```

______________________________________________________________________

## Story Size: The Number One Rule

**Each story must be completable in ONE autonomous agent iteration (one context window).**

Each iteration spawns a fresh agent instance with no memory of previous work. If a story is too big, the agent runs out
of context before finishing and produces broken code.

### Right-sized stories (fitinera/Python examples):

- Add a new `frozen=True` dataclass to `src/fitinera/models/`
- Implement a single `Flow` subclass with its unit tests
- Add a new builder for a parameter class
- Scaffold a new API surface with `NotImplementedError` stubs (API-first step)
- Implement the behaviour behind a previously scaffolded API (implementation step)

### Too big (split these):

- "Implement the entire account rollover pipeline" — split into: model → flow → integration
- "Add the full computation engine" — split into one story per domain model or flow subclass
- "Refactor the API" — split into one story per endpoint or pattern change

**Rule of thumb:** If you cannot describe the change in 2–3 sentences, it is too big.

______________________________________________________________________

## Scaffold-First / Implement-Second Pattern

For **any task involving new or changed APIs**, split the work into at least two stories:

1. **Scaffold story:** Create the API surface — function signatures, class skeletons, type hints, `NotImplementedError`
   stubs — and write tests against this API as if it were implemented. The goal is to validate API ergonomics, parameter
   completeness, and computational flow _before_ writing logic. This story is complete when the scaffolded API imports
   cleanly and tests exist (tests will fail on `NotImplementedError`).

1. **Implementation story (depends on scaffold):** Fill in the stubs with real logic until all tests from the scaffold
   story pass. Then refactor for high code quality.

It is acceptable — and expected — to iterate between scaffold and implementation stories if the API design needs
adjustment based on implementation discoveries. When that happens, create a follow-up scaffold-adjustment story.

______________________________________________________________________

## Story Ordering: Dependencies First

Stories should be created in dependency order. Earlier stories must not depend on later ones.

**Correct order for fitinera:**

1. Domain models (`src/fitinera/models/`) — frozen dataclasses, value objects
1. Flows and computations (`src/fitinera/flows/`) — business logic subclasses
1. API surface (`src/fitinera/`) — public interface scaffolding, then implementation
1. Integration or cross-cutting concerns

**Wrong order:**

1. Flow implementation (depends on a model that does not exist yet)
1. Model definition

______________________________________________________________________

## Required Final Criteria

Append these criteria to **every** story's acceptance criteria:

- Pre-commit passes (`uv run pre-commit run`)
- Tests written in DAMP style with Google-style docstrings
- TDD cycle followed: test first → implement → refactor

______________________________________________________________________

## Conversion Rules

1. **Each developer story becomes one `TaskCreate` call**
1. **IDs**: Sequential `FEAT-<slug>-01`, `FEAT-<slug>-02`, etc. (zero-padded, two-digit) — used in the Subject
1. **Create tasks in dependency order** (domain models → flows/computations → API surface → integration)
1. **Subject**: `FEAT-<slug>-##: [Story title]`
1. **Description**: Full story description + all acceptance criteria + Required Final Criteria

______________________________________________________________________

## Functional Requirements Cross-Check

After extracting stories, cross-check against the **Functional Requirements** section (if present):

1. Read every numbered FR (e.g., `FR-1`, `FR-2`, …) in the PRD.
1. For each FR, verify it is traceable to at least one story's acceptance criteria.
1. If an FR is **not covered** by any story:
   - If it fits naturally as acceptance criteria on an existing story, add it there.
   - Otherwise, create a new story specifically for that FR.
1. After all tasks are created, list the FR → story mapping so traceability is visible.

**Every functional requirement must be implemented. If a story doesn't cover it, no agent will.**

______________________________________________________________________

## Splitting Large PRDs

If a PRD has big features, split them:

**Original:**

> "Add account rollover pipeline"

**Split into separate `TaskCreate` calls:**

1. `FEAT-account-rollover-01`: Scaffold `RolloverParams` dataclass and `RolloverFlow` API stubs
1. `FEAT-account-rollover-02`: Implement `RolloverFlow.run()` logic
1. `FEAT-account-rollover-03`: Add `RolloverParamsBuilder` with fluent interface
1. `FEAT-account-rollover-04`: Integration test: full period-close → rollover pipeline

Each is one focused change that can be completed and verified independently.

______________________________________________________________________

## Example

**Input PRD (abbreviated):**

```markdown
# Account Rollover

## Developer Stories

- FEAT-account-rollover-01: Scaffold RolloverParams and RolloverFlow API
- FEAT-account-rollover-02: Implement RolloverFlow logic

## Functional Requirements

- FR-1: RolloverParams must be immutable (frozen=True)
- FR-2: RolloverFlow.run() must return a Transaction object
- FR-3: A zero-amount rollover must be skipped
```

**Output: `TaskCreate` calls**

**Task 1:**

- **Subject:** `FEAT-account-rollover-01: Scaffold RolloverParams and RolloverFlow API`
- **Description:**
  ```
  As a developer, I want typed stubs for RolloverParams and RolloverFlow so that I can validate the
  API surface and write tests before implementing real logic.

  Acceptance Criteria:
  - RolloverParams frozen dataclass in src/fitinera/models/ with fields: from_period_id, to_period_id, amount, account_id
  - RolloverFlow subclass in src/fitinera/flows/ with run() stub raising NotImplementedError
  - Tests exist covering the expected API shape (will fail on NotImplementedError)
  - Pre-commit passes (uv run pre-commit run)
  - Tests written in DAMP style with Google-style docstrings
  - TDD cycle followed: test first → implement → refactor
  ```

**Task 2:**

- **Subject:** `FEAT-account-rollover-02: Implement RolloverFlow logic`
- **Description:**
  ```
  As a developer, I want RolloverFlow.run() to produce a rollover transaction so that the pipeline
  correctly carries balances across periods.

  Acceptance Criteria:
  - RolloverFlow.run() emits a Transaction carrying the rollover amount
  - All scaffold-story tests now pass
  - Zero-amount rollover is skipped (FR-3)
  - Pre-commit passes (uv run pre-commit run)
  - Tests written in DAMP style with Google-style docstrings
  - TDD cycle followed: test first → implement → refactor
  ```

**FR → Story traceability (listed after all tasks are created):**

| FR   | Covered by               |
| ---- | ------------------------ |
| FR-1 | FEAT-account-rollover-01 |
| FR-2 | FEAT-account-rollover-02 |
| FR-3 | FEAT-account-rollover-02 |

______________________________________________________________________

## Phase 1.5: Documentation Authoring Tasks

**After all implementation stories are created (Phase 1) but before setting dependencies (Phase 2), create documentation
tasks for files that are known ahead of time from the finalized PRD.**

Documentation written early becomes the source of truth that implementation agents align with. This eliminates
mismatches between docs and code.

### What qualifies as a documentation task

Any documentation artifact whose content can be derived from the PRD's design decisions, functional requirements, or API
shapes:

- `docs/` files referenced or implied by the PRD (e.g., developer guides, architecture overviews)
- `README.md` updates (new feature descriptions, usage examples, API reference changes)
- `CONTRIBUTING.md` updates (new conventions, workflow changes)
- Any other documentation artifacts mentioned in the PRD

### Task format

- **Subject prefix:** `DOC-<slug>-##` (e.g., `DOC-account-rollover-01`) — distinct from `FEAT-` to make them visually
  identifiable in the task DAG.
- **Numbering:** Sequential two-digit zero-padded, independent of `FEAT-` numbering.
- **Sizing:** Same rules as implementation stories — each must be completable in one agent iteration.
- **Description:** Instruct the agent to write the documentation content based on the PRD's design decisions, functional
  requirements, and API shapes. The agent should write the documentation **as if the feature were already implemented**,
  establishing the contract that implementation agents will fulfil.

### Dependency rule

`DOC-` tasks block `FEAT-` tasks that touch the same areas. For example, if a `DOC-` task writes the API reference for a
module, the `FEAT-` task that implements that module should be `is_blocked_by` the `DOC-` task. This ensures
implementation agents have documentation to align with before they start coding.

______________________________________________________________________

## Phase 2: Set Task Dependencies

**After all tasks have been created via `TaskCreate` (both `DOC-` and `FEAT-` tasks), use the `TaskUpdate` tool to
explicitly set the dependencies between tasks.**

### Step 1: Analyze and Build the Dependency Tree

1. Gather the full set of just-created tasks (their IDs and summaries).
1. For each task, determine which other tasks it "blocks" (must finish before another can start) and which it
   "is_blocked_by" (must wait for another to finish).
   - Use the intent, technical dependencies, and the story ordering above (domain models → flows → API surface →
     integration).
   - Each task should be considered from the perspective of **a single autonomous stack-owning worker**: whoever claims
     a task owns all required layers, does their own code, tests, config, and QA — no handoffs.
   - Only add a dependency if the task's work **genuinely can't begin** before another is finished (i.e., if waiting is
     necessary for correctness or to avoid rework).
   - Prefer minimal dependency chains; only encode necessary gates, not organisational process or review steps.
   - Scaffold stories always block their corresponding implementation stories.
   - **`DOC-` tasks block `FEAT-` tasks that touch the same areas** (see Phase 1.5).

### Step 2: Update Task Records

1. For each task, use `TaskUpdate` to set the `blocks` and `is_blocked_by` fields based on the dependency tree from Step
   1\.
   - Example: If `FEAT-account-rollover-01` must finish before `FEAT-account-rollover-02` can begin, set
     `FEAT-account-rollover-01` to `blocks=["FEAT-account-rollover-02"]` and `FEAT-account-rollover-02` to
     `is_blocked_by=["FEAT-account-rollover-01"]`.
   - Only set dependencies after **all** tasks have been created.
1. Record the final dependency mapping (task ID → blocked/blocks relationships) immediately after the FR → story
   traceability map.

### Guidance

- Always prefer the smallest, necessary set of gates to allow as much parallelisation as possible.
- The "single worker owns their full stack" model means docs, QA, and code for a feature can often proceed together.
- Only gate tasks when a technical or testable precondition **must** be satisfied first.

______________________________________________________________________

## Phase 3: Back-Pressure Gate Task

**After all dependencies are set (Phase 2), create one final high-level back-pressure gate task that depends on all other
tasks.**

This task is the last thing that runs. It validates that everything is aligned and correct before the feature branch is
considered done.

### Task format

- **Subject:** `GATE-<slug>-01: Final back-pressure gate check`
- **Dependencies:** `is_blocked_by` **all** `DOC-` and `FEAT-` tasks. Blocks nothing.

### Gate task description

The description must instruct the executing agent to perform all five checks below, **in order**:

#### Check 1 — Documentation–code alignment

Verify that all `docs/`, `README.md`, `CONTRIBUTING.md` content matches the implemented code.

- If mismatched **and** the PRD makes it clear which is correct → fix the out-of-sync artifact.
- If mismatched **and** the PRD is ambiguous → use **AskUserQuestion** to resolve the difference. Append the resolution
  to a new **"Implementation Conflict Resolutions"** section at the bottom of the PRD file (`plans/<branch>-prd.md`).
  **Do not modify any other section of the PRD.**

#### Check 2 — ADR sync

Verify that all applicable design choices made during implementation have been documented as ADRs (per
`.agents/skills/writing-adrs/SKILL.md`) and that each ADR's `Status` field is set correctly (`Accepted`, `Rejected`,
`Superseded`, etc.). If ADRs are out of sync, update them and re-validate.

#### Check 3 — Pre-commit checks

Run `uv run pre-commit run`. This includes unit tests. Must exit 0.

#### Check 4 — Acceptance criteria

Verify every acceptance criterion in each developer story in the PRD has been met.

#### Check 5 — Success metrics

Verify every success metric listed in the PRD's **Success Metrics** section has been met.

### Failure escalation

If any of checks 1–2 fail, fix them in-place as described above.

If any of checks 3–5 fail, the gate agent must:

1. **Iteration guard:** If the current gate task suffix is **`-04` or higher** (i.e., this is the 4th or later
   back-pressure gate iteration), use **AskUserQuestion** before proceeding with the escalation steps below. The message
   must include:
   - The current gate iteration number.
   - A summary of which checks have been failing and whether the same checks have failed repeatedly across prior gate
     iterations (recurring) or are new failures.
   - What problems still remain and what remediation tasks would be created if the user approves.
   - A clear question: should the escalation proceed, or should the user intervene directly?

   **Do not proceed with steps 2–3 until the user responds.** This guard applies on **every** gate iteration from `-04`
   onward (i.e., `-04`, `-05`, `-06`, …).

1. Use **TaskCreate** for each discrete problem category to create remediation tasks.
1. Create another `GATE-<slug>-NN` task (increment the number suffix, e.g., `GATE-<slug>-02`, `GATE-<slug>-03`) that is
   `is_blocked_by` all newly created remediation tasks. This creates a re-validation loop with an audit trail.

> **Numbering convention:** Each successive gate task increments its suffix (`-01`, `-02`, `-03`, …) so you can see how
> many times the back-pressure gate had to re-run.

______________________________________________________________________

## Checklist Before Creating Tasks

Before calling `TaskCreate`, verify:

- [ ] **Phase 0 passed:** symlink `plans/<branch>` exists and points to `~/.claude/tasks/<branch>`
- [ ] **Phase 0 passed:** git branch matches `<branch>` (or user explicitly chose to continue)
- [ ] **Phase 0 passed:** `CLAUDE_CODE_TASK_LIST_ID` in `.claude/settings.json` is consistent with the PRD
- [ ] **Phase 0 passed:** no stale-session warning (or user explicitly chose to continue)
- [ ] Each story is completable in one iteration (small enough)
- [ ] Stories ordered: domain models → flows/computations → API surface → integration
- [ ] New/changed API stories follow scaffold-first / implement-second pattern
- [ ] Acceptance criteria are verifiable (not vague)
- [ ] No story depends on a later story
- [ ] Every functional requirement from the PRD is traceable to at least one story's acceptance criteria
- [ ] Documentation tasks (`DOC-`) identified for all known-ahead-of-time docs from the PRD

______________________________________________________________________

## Checklist After Task Creation (Phase 2 + Phase 3)

Before finishing, ensure:

- [ ] All `DOC-` documentation tasks have been created via `TaskCreate` (Phase 1.5)
- [ ] All `FEAT-` implementation tasks have been created via `TaskCreate` (Phase 1)
- [ ] FR → story traceability mapping is documented
- [ ] `DOC-` tasks block `FEAT-` tasks that touch the same areas
- [ ] For each task, `blocks` and `is_blocked_by` dependency fields have been set via `TaskUpdate`
- [ ] Dependency mapping is documented after the FR → story mapping
- [ ] `GATE-<slug>-01` back-pressure gate task created via `TaskCreate`, blocked by all other tasks (Phase 3)
- [ ] Gate task description includes all five checks (doc–code sync, ADR sync, pre-commit, acceptance criteria, success
  metrics)

______________________________________________________________________

## Checklist for Each Task

- [ ] Subject follows format: `FEAT-<slug>-##`, `DOC-<slug>-##`, or `GATE-<slug>-##: [Title]`
- [ ] Description includes full story description + all acceptance criteria + Required Final Criteria
