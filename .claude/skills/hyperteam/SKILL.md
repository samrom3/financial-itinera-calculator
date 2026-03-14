---
name: hyperteam
description: "Reads a PRD, derives a task DAG, gets user approval, writes team-state.json, and orchestrates an agent team with lead, workers, and validators. Replaces the /prd-tasks + /hyperworker two-step workflow."
user-invocable: true
disable-model-invocation: true
---

# Hyperteam

Converts a PRD into an autonomous agent team that executes the full task DAG, tracks state in
`plans/<branch>-team-state.json`, and offers PR creation when all tasks pass the back-pressure gate.

______________________________________________________________________

## Phase 0: Pre-Flight and PRD Ingestion

Before doing anything else, run these checks in order. **Stop and surface each issue as you encounter it.**

### Step 1 — Read settings and derive branch/slug

1. Read `.claude/settings.local.json` and extract the value of `env.CLAUDE_CODE_TASK_LIST_ID` → this is `<branch>`.
2. Derive `<slug>` from `<branch>` by stripping the leading `feat-` prefix if present.
   - Example: `feat-hyperteam-skill` → `hyperteam-skill`
   - Example: `feat-account-rollover` → `account-rollover`
   - If `<branch>` does not start with `feat-`, use `<branch>` as `<slug>` unchanged.

### Step 2 — Verify git branch

1. Determine the currently checked-out git branch (`git branch --show-current`).
2. Compare the git branch name to `<branch>`:
   - **If they match** — proceed to Step 3.
   - **If they do NOT match** — use `AskUserQuestion` to ask the user:
     > The current git branch (`<actual-git-branch>`) does not match the task list branch (`<branch>`). Would you like
     > to continue anyway, or pause so you can check out the correct branch?
   - Wait for their response. If they say pause, **stop here** — do not continue.

### Step 3 — Detect fresh start vs. resume

1. Check whether `plans/<branch>-team-state.json` exists.
   - **If absent** — this is a fresh start. Proceed to Phase 1.
   - **If present** — this is a resume. Skip to Phase 1-Resume.

______________________________________________________________________

## Phase 1: Derive Task DAG and User Approval

### Phase 1: Fresh Start

This section applies when `plans/<branch>-team-state.json` does **not** exist (detected in Phase 0, Step 3).

#### Step 1 — Read and parse the PRD

1. Read `plans/<branch>-prd.md` in full.
2. Extract all developer stories. Stories are headings that match:
   - `### FEAT-*` — feature implementation stories
   - `### DOC-*` — documentation stories
3. For each story, capture:
   - **Title** — the heading text after the `### ` prefix (strip leading ID prefix if present, e.g. `### FEAT-hyperteam-skill-04: Phase 1` → title is `Phase 1`)
   - **Description** — all body text under that heading until the next `###` heading
4. Preserve the order stories appear in the PRD — this is the dependency order.

> **Note:** The scaffold-first pattern is applied by the `/prd` skill when the PRD is authored. Phase 1 does not re-split
> stories; it maps each PRD story to exactly one task entry.

#### Step 2 — Assign task IDs

Assign IDs sequentially in the order stories appear in the PRD, using two-digit zero-padded counters:

- FEAT stories → `FEAT-<slug>-01`, `FEAT-<slug>-02`, … (independent counter)
- DOC stories → `DOC-<slug>-01`, `DOC-<slug>-02`, … (independent counter)
- GATE → `GATE-<slug>-01` (always exactly one, created last)

#### Step 3 — Infer dependencies

1. Build an ordered list of all FEAT and DOC task IDs in PRD order.
2. For each task, set `blocked_by` to the IDs of all tasks that appear **before** it in the PRD and that it logically
   requires. Use the following heuristic:
   - Each FEAT task is blocked by the FEAT task immediately preceding it (linear chain by default).
   - DOC tasks that document a feature area block the FEAT tasks covering that same area.
   - If two tasks are clearly independent (different modules, no shared interfaces), they may run in parallel — omit the
     dependency between them.
   - Prefer the minimal set of necessary gates; allow parallelism where possible.
3. The `GATE-<slug>-01` task is **always** blocked by **all** FEAT and DOC tasks.

#### Step 4 — Render ASCII DAG

Render a tree showing tasks, their titles, and dependency arrows. Use `└──` for children (tasks that are blocked by a
parent). Mark parallel tasks with `[parallel]` and the gate with `[blocked by all]`.

Example format:

```
Branch: <branch>

FEAT-<slug>-01 — <title>
└── FEAT-<slug>-02 — <title>
    └── FEAT-<slug>-03 — <title>
        └── ...

DOC-<slug>-01 — <title> [parallel]

GATE-<slug>-01 — Back-pressure gate [blocked by all]
```

Adjust the tree to reflect the actual dependency structure derived in Step 3. Tasks that are blocked only by the root
(first task) appear as children of that root. Truly independent parallel chains appear as separate top-level entries.

#### Step 5 — Ask for user approval

Use `AskUserQuestion` to present the full rendered DAG and ask:

> Here is the proposed task plan for `<branch>`:
>
> ```
> <rendered ASCII DAG>
> ```
>
> Does this plan look correct? Approve to proceed, or describe any changes you'd like to make.

Wait for the user's response.

- **If approved** — proceed to Step 6.
- **If changes requested** — apply the requested changes to the task list and dependency graph, re-render the DAG, and
  ask again. Repeat until the user approves.

#### Step 6 — Write team-state.json

Once the user approves the plan, write `plans/<branch>-team-state.json` with the following structure (matching
`references/team-state-schema.md`):

```json
{
  "metadata": {
    "branch": "<branch>",
    "slug": "<slug>",
    "prd_path": "plans/<branch>-prd.md",
    "status": "running",
    "created_at": "<ISO 8601 timestamp>"
  },
  "tasks": [
    {
      "id": "FEAT-<slug>-01",
      "title": "<story title>",
      "description": "<full story text including acceptance criteria>",
      "type": "FEAT",
      "status": "pending",
      "blocked_by": [],
      "started_at": null,
      "completed_at": null,
      "validator_result": null,
      "validator_notes": null
    },
    {
      "id": "DOC-<slug>-01",
      "title": "<story title>",
      "description": "<full story text>",
      "type": "DOC",
      "status": "pending",
      "blocked_by": ["FEAT-<slug>-01"],
      "started_at": null,
      "completed_at": null,
      "validator_result": null,
      "validator_notes": null
    },
    {
      "id": "GATE-<slug>-01",
      "title": "Back-pressure gate",
      "description": "Run all five gate checks per references/gate-task-template.md.",
      "type": "GATE",
      "status": "pending",
      "blocked_by": ["<all FEAT and DOC task IDs>"],
      "started_at": null,
      "completed_at": null,
      "validator_result": null,
      "validator_notes": null
    }
  ],
  "gate_iterations": 0
}
```

Rules:
- `metadata.created_at` — use the current UTC timestamp in ISO 8601 format (e.g. `"2026-03-14T10:00:00Z"`).
- All tasks have `"status": "pending"`, `"started_at": null`, `"completed_at": null`, `"validator_result": null`,
  `"validator_notes": null`.
- Task order in the `tasks` array: FEAT tasks first (in PRD order), then DOC tasks (in PRD order), then the GATE task.
- `blocked_by` arrays contain the exact task IDs (strings) as derived in Step 3.

After writing the file, proceed to Phase 2.

______________________________________________________________________

### Phase 1-Resume: Resuming from Existing State

This path is taken when `plans/<branch>-team-state.json` already exists (detected in Phase 0 Step 3).

**Step 1 — Read authoritative state**
- Read `plans/<branch>-team-state.json` (authoritative source of truth)
- Read `plans/<branch>-progress.txt` if it exists (for context only)

**Step 2 — Reconcile state**
- Tasks with `status: completed` or `status: validated` in team-state.json are done.
- Ignore any discrepancy between progress.txt and team-state.json — team-state.json wins.
- Identify remaining tasks: all tasks with `status: pending` or `status: in_progress` (treat in_progress as interrupted, reset to pending).

**Step 3 — Render resume summary**
Present to the user:
- How many tasks completed (list their IDs and titles)
- How many tasks remaining (list their IDs and titles)
- Current gate_iterations count

**Step 4 — Confirm with user**
Use `AskUserQuestion` to ask:
> "Found existing run for `<branch>`. Completed: N tasks. Remaining: M tasks.
> [list of remaining task IDs and titles]
> Continue with remaining tasks?"

**Step 5 — Proceed**
- If user confirms: proceed to Phase 2 with the full team-state.json as-is (remaining tasks will be dispatched by the team lead)
- If user declines: stop here and leave state files unchanged

______________________________________________________________________

## Phase 2: Team Creation and Dispatch

This phase hands off to the team lead agent to orchestrate all task execution.

### Step 1 — Create the team

Call `TeamCreate` with team name `<branch>`. Pass a prompt to the team creation that includes: the branch name, the path
to `plans/<branch>-team-state.json`, the path to `plans/<branch>-progress.txt`, and the path to `plans/<branch>-prd.md`.
The `hyperteam-lead` sub-agent (defined in `.claude/agents/hyperteam-lead.md`) will serve as the team orchestrator.

The prompt should describe the work in natural language, for example:
> "Implement all tasks for `<branch>` as specified in `plans/<branch>-team-state.json`. Progress log:
> `plans/<branch>-progress.txt`. PRD: `plans/<branch>-prd.md`."

### Step 2 — Dispatch the team lead

Dispatch `hyperteam-lead` via the Agent tool with `subagent_type: hyperteam-lead`, providing all the above paths in the
prompt:

- Branch: `<branch>`
- `team_state_path`: `plans/<branch>-team-state.json`
- `progress_path`: `plans/<branch>-progress.txt`
- PRD path: `plans/<branch>-prd.md`
- Instruction: "Orchestrate all tasks in team-state.json until all FEAT and DOC tasks are validated. Then dispatch the
  GATE task."

### Step 3 — Wait

The main thread waits for the team lead to return. The lead handles all worker and validator dispatch internally (per its
sub-agent definition in `.claude/agents/hyperteam-lead.md`).

### What the team lead does (for reference — implemented in `.claude/agents/hyperteam-lead.md`)

- Reads `team-state.json`, finds unblocked tasks (those with `status: pending` and all `blocked_by` tasks at `validated`
  or `completed`)
- Dispatches up to 4 workers in parallel (Agent tool, `subagent_type: hyperteam-worker`)
- After each worker completes: atomically sets task `status` → `completed` in `team-state.json` AND appends a progress
  entry to `progress.txt` (read JSON → update status → write JSON, then append to progress.txt before any other agent
  reads them)
- After that, dispatches a validator (`subagent_type: hyperteam-validator`)
- After validator PASS: sets task `status` → `validated` in `team-state.json`, and unlocks dependent tasks
- After validator FAIL: appends validator notes to the task record in `team-state.json`, then re-dispatches the worker
  with those notes
- Status flow: `pending` → `in_progress` → `completed` (after worker done + progress.txt append) → `validated` (after
  validator PASS)
- Loops until all FEAT and DOC tasks have `status: validated`
- Dispatches the GATE task, then returns control to the main thread

> **Note:** Phase 3 (back-pressure gate detail) is handled after the team lead returns. Once all tasks except GATE are
> validated, the lead dispatches GATE and returns; the main thread then proceeds to Phase 3.

______________________________________________________________________

## Phase 3: Back-Pressure Gate

After the team lead returns (all FEAT and DOC tasks are `validated` and the GATE task has been
dispatched), the main thread enters this phase.

### Step 1 — Gate agent execution

The team lead dispatches the gate agent (per `.claude/agents/hyperteam-lead.md`) with the
instructions from `references/gate-task-template.md`. The gate agent runs all five checks in order:

1. **Check 1 — Documentation–code alignment:** verifies that `docs/`, `README.md`, and
   `CONTRIBUTING.md` match the implemented code. Fixes mismatches in-place if the PRD is
   unambiguous; asks the user if not.
2. **Check 2 — ADR sync:** verifies that all applicable design choices have ADRs with correct
   Status fields. Updates ADRs in-place if needed.
3. **Check 3 — Pre-commit checks:** runs `uv run pre-commit run`. Must exit 0.
4. **Check 4 — Acceptance criteria:** verifies every acceptance criterion in every PRD story has
   been met.
5. **Check 5 — Success metrics:** verifies every success metric in the PRD has been met.

After each check (pass or fail) and after every user interaction, the gate agent appends a summary
entry to `plans/<branch>-progress.txt` using the format defined in `gate-task-template.md`.

### Step 2 — Gate pass

If all five checks pass, the gate agent marks `GATE-<slug>-NN` as `completed` in
`plans/<branch>-team-state.json`, appends a final pass summary to `progress.txt`, and returns
control to the team lead. The team lead then returns to the main thread.

The main thread proceeds to Phase 4.

### Step 3 — Gate fail (checks 3–5)

If checks 1–2 fail, the gate agent fixes them in-place (as described in the gate-task-template).

If any of checks 3–5 fail, the gate agent follows this remediation sequence:

#### Iteration guard

Before writing any remediation entries, the gate agent reads `gate_iterations` from
`plans/<branch>-team-state.json`. If `gate_iterations` is **4 or higher**, the gate agent uses
`AskUserQuestion` to ask the user before proceeding. The message must include:

- The current gate iteration number.
- A summary of which checks have been failing and whether the same checks have failed repeatedly
  across prior gate iterations (recurring) or are new failures — determined by reading
  `plans/<branch>-progress.txt`.
- What problems still remain and what remediation entries would be written if the user approves.
- A clear question: should the escalation proceed, or should the user intervene directly?

The gate agent does **not** proceed with remediation until the user responds affirmatively.

#### Remediation steps

1. **Write remediation task entries to `team-state.json`:** The gate agent appends new task
   objects to the `tasks` array in `plans/<branch>-team-state.json`. Each new task has
   `"status": "pending"` and appropriate `blocked_by` entries referencing tasks they depend on.
   These are written directly to `team-state.json` — **not** created via an external task service
   (`TaskCreate` is not used for remediation entries; `team-state.json` is the single source of
   truth).

   Example remediation task entry:
   ```json
   {
     "id": "FEAT-<slug>-NN",
     "title": "<short description of remediation>",
     "description": "<details of what failed and what must be fixed>",
     "type": "FEAT",
     "status": "pending",
     "blocked_by": [],
     "started_at": null,
     "completed_at": null,
     "validator_result": null,
     "validator_notes": null
   }
   ```

2. **Append to `progress.txt`:** The gate agent appends a summary of each remediation entry to
   `plans/<branch>-progress.txt`, following the format in `gate-task-template.md`.

3. **Increment `gate_iterations`:** The gate agent increments `gate_iterations` by 1 in
   `plans/<branch>-team-state.json`.

4. **Add a new GATE entry to `team-state.json`:** The gate agent appends a new
   `GATE-<slug>-NN+1` task object to the `tasks` array with `"status": "pending"` and
   `blocked_by` set to the IDs of all remediation tasks just written (so the new gate only runs
   after remediation is complete).

   Example next-gate entry:
   ```json
   {
     "id": "GATE-<slug>-02",
     "title": "Back-pressure gate (iteration 2)",
     "description": "Re-run all five gate checks per references/gate-task-template.md.",
     "type": "GATE",
     "status": "pending",
     "blocked_by": ["FEAT-<slug>-NN"],
     "started_at": null,
     "completed_at": null,
     "validator_result": null,
     "validator_notes": null
   }
   ```

5. **Team lead re-enters the dispatch loop:** The gate agent signals completion (by returning).
   The team lead, upon receiving the gate result, re-reads `plans/<branch>-team-state.json` and
   continues its dispatch loop, picking up the new remediation tasks (which are now unblocked or
   will become unblocked as prior remediation completes) and eventually dispatching the new
   `GATE-<slug>-NN+1` task. The main thread remains waiting while the team lead iterates.

______________________________________________________________________

## Phase 4: Completion and PR Offer
