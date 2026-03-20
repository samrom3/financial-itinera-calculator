# team-state.json Schema

`plans/<branch>-team-state.json` is the authoritative task state registry for a hyperteam run. It
is written at the start of Phase 2 and mutated by the Team Lead and gate agent throughout the run.

______________________________________________________________________

## Top-level structure

```json
{
  "metadata": { ... },
  "tasks": [ ... ],
  "gate_iterations": 0
}
```

______________________________________________________________________

## `metadata`

| Field           | Type   | Description                                                      |
|-----------------|--------|------------------------------------------------------------------|
| `branch`        | string | Git branch name (e.g. `"feat-account-rollover"`).               |
| `slug`          | string | Short identifier derived from branch (e.g. `"account-rollover"`). |
| `prd_path`      | string | Relative path to the PRD file (e.g. `"plans/feat-account-rollover-prd.md"`). |
| `status`        | string | Overall run status. One of: `"running"`, `"complete"`.          |
| `created_at`    | string | ISO 8601 timestamp when the file was first written.             |

### Example

```json
"metadata": {
  "branch": "feat-account-rollover",
  "slug": "account-rollover",
  "prd_path": "plans/feat-account-rollover-prd.md",
  "status": "running",
  "created_at": "2026-03-14T10:00:00Z"
}
```

______________________________________________________________________

## `tasks`

Array of task objects. Each object represents one unit of work derived from the PRD DAG or created
as a gate remediation entry.

| Field              | Type                   | Default | Description                                                        |
|--------------------|------------------------|---------|---------------------------------------------------------------------|
| `id`               | string                 |         | Unique task identifier (e.g. `"FEAT-account-rollover-01"`).        |
| `title`            | string                 |         | Short human-readable title.                                         |
| `description`      | string                 |         | Full task description including acceptance criteria.                |
| `type`             | string                 |         | One of: `"FEAT"`, `"DOC"`, `"GATE"`.                              |
| `status`           | string                 |         | One of: `"pending"`, `"in_progress"`, `"completed"`, `"validated"`, `"failed"`, `"blocked"`. |
| `blocked_by`       | array of string        |         | IDs of tasks that must reach `"validated"` (for FEAT tasks) or `"completed"` (for DOC tasks) before this task becomes unblocked. |
| `started_at`       | string \| null         | `null`  | ISO 8601 timestamp when an agent picked up this task, or `null`.   |
| `completed_at`     | string \| null         | `null`  | ISO 8601 timestamp when the task reached `"completed"`, or `null`. |
| `validator_result` | string \| null         | `null`  | Gate validator verdict: `"PASS"`, `"FAIL"`, or `null` if not yet validated. |
| `validator_notes`  | array of string \| null| `null`  | Array of specific findings from validator. `null` until validated; `[]` for clean PASS; list of strings for FAIL findings. |
| `validated_at`     | string \| null         | `null`  | Timestamp when validator completed; `null` until validator runs.   |

### Status transitions

```
pending → in_progress → completed → validated
                      ↘ failed
                                  ↘ blocked  (after second validator FAIL)
```

- `pending`: not yet started; all blockers may or may not be complete.
- `in_progress`: an agent has claimed the task.
- `completed`: the agent finished and committed its work.
- `validated`: a gate check confirmed the work meets acceptance criteria.
- `failed`: Set by a worker that cannot complete its task after retries. The team lead will attempt one re-dispatch before escalating to `blocked`.
- `blocked`: task failed validation twice and cannot proceed without manual intervention. `AskUserQuestion` was used to notify the user.

### Example task objects

Pending task (not yet started):

```json
{
  "id": "FEAT-account-rollover-02",
  "title": "Implement RolloverFlow business logic",
  "description": "As a developer, I want ...\n\nAcceptance Criteria:\n- [ ] ...",
  "type": "FEAT",
  "status": "pending",
  "blocked_by": ["FEAT-account-rollover-01"],
  "started_at": null,
  "completed_at": null,
  "validator_result": null,
  "validator_notes": null,
  "validated_at": null
}
```

Completed task (validator PASS):

```json
{
  "id": "FEAT-account-rollover-01",
  "title": "Scaffold RolloverParams dataclass and RolloverFlow API stubs",
  "description": "As a developer, I want ...\n\nAcceptance Criteria:\n- [ ] ...",
  "type": "FEAT",
  "status": "validated",
  "blocked_by": [],
  "started_at": "2026-03-14T10:05:00Z",
  "completed_at": "2026-03-14T10:45:00Z",
  "validator_result": "PASS",
  "validator_notes": [],
  "validated_at": "2026-03-14T11:00:00Z"
}
```

Failed task (validator FAIL):

```json
{
  "id": "FEAT-account-rollover-03",
  "title": "Add rollover end-to-end tests",
  "description": "As a developer, I want ...\n\nAcceptance Criteria:\n- [ ] ...",
  "type": "FEAT",
  "status": "failed",
  "blocked_by": ["FEAT-account-rollover-02"],
  "started_at": "2026-03-14T11:10:00Z",
  "completed_at": "2026-03-14T11:50:00Z",
  "validator_result": "FAIL",
  "validator_notes": ["Missing test for edge case: zero-balance rollover", "pre-commit failed: ruff E501 in tests/fitinera/test_rollover.py"],
  "validated_at": "2026-03-14T12:05:00Z"
}
```

______________________________________________________________________

## `gate_iterations`

Integer. Starts at `0` when the file is first written. Incremented by 1 each time a gate iteration
fails (checks 3–5). Used by the iteration guard: if `gate_iterations` is **4 or higher**, the gate
agent uses `AskUserQuestion` to ask the user before creating more remediation work.

______________________________________________________________________

## Full example

```json
{
  "metadata": {
    "branch": "feat-account-rollover",
    "slug": "account-rollover",
    "prd_path": "plans/feat-account-rollover-prd.md",
    "status": "running",
    "created_at": "2026-03-14T10:00:00Z"
  },
  "tasks": [
    {
      "id": "FEAT-account-rollover-01",
      "title": "Scaffold RolloverParams dataclass and RolloverFlow API stubs",
      "description": "As a developer, I want ...",
      "type": "FEAT",
      "status": "validated",
      "blocked_by": [],
      "started_at": "2026-03-14T10:05:00Z",
      "completed_at": "2026-03-14T10:45:00Z",
      "validator_result": "PASS",
      "validator_notes": [],
      "validated_at": "2026-03-14T11:00:00Z"
    },
    {
      "id": "GATE-account-rollover-01",
      "title": "Back-pressure gate check",
      "description": "Run all five gate checks per references/gate-task-template.md.",
      "type": "GATE",
      "status": "pending",
      "blocked_by": ["FEAT-account-rollover-01"],
      "started_at": null,
      "completed_at": null,
      "validator_result": null,
      "validator_notes": null,
      "validated_at": null
    }
  ],
  "gate_iterations": 0
}
```
