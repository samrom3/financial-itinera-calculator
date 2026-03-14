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

| Field              | Type            | Description                                                        |
|--------------------|-----------------|---------------------------------------------------------------------|
| `id`               | string          | Unique task identifier (e.g. `"FEAT-account-rollover-01"`).        |
| `title`            | string          | Short human-readable title.                                         |
| `description`      | string          | Full task description including acceptance criteria.                |
| `type`             | string          | One of: `"FEAT"`, `"DOC"`, `"GATE"`.                              |
| `status`           | string          | One of: `"pending"`, `"in_progress"`, `"completed"`, `"validated"`, `"failed"`. |
| `blocked_by`       | array of string | IDs of tasks that must reach `"completed"` before this one starts. |
| `started_at`       | string \| null  | ISO 8601 timestamp when an agent picked up this task, or `null`.   |
| `completed_at`     | string \| null  | ISO 8601 timestamp when the task reached `"completed"`, or `null`. |
| `validator_result` | string \| null  | Gate validator verdict: `"PASS"`, `"FAIL"`, or `null` if not yet validated. |
| `validator_notes`  | string \| null  | Free-text notes from the gate validator, or `null`.                |

### Status transitions

```
pending → in_progress → completed → validated
                      ↘ failed
```

- `pending`: not yet started; all blockers may or may not be complete.
- `in_progress`: an agent has claimed the task.
- `completed`: the agent finished and committed its work.
- `validated`: a gate check confirmed the work meets acceptance criteria.
- `failed`: the agent or gate check determined the task did not succeed; remediation needed.

### Example task object

```json
{
  "id": "FEAT-account-rollover-01",
  "title": "Scaffold RolloverParams dataclass and RolloverFlow API stubs",
  "description": "As a developer, I want ...\n\nAcceptance Criteria:\n- [ ] ...",
  "type": "FEAT",
  "status": "completed",
  "blocked_by": [],
  "started_at": "2026-03-14T10:05:00Z",
  "completed_at": "2026-03-14T10:45:00Z",
  "validator_result": null,
  "validator_notes": null
}
```

______________________________________________________________________

## `gate_iterations`

Integer. Starts at `0` when the file is first written. Incremented by `1` each time the gate agent
completes a full five-check pass (whether it passes or fails). The Team Lead reads this value when
deciding whether to apply the iteration guard (threshold: 4 or higher → ask the user before
creating further remediation entries).

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
      "status": "completed",
      "blocked_by": [],
      "started_at": "2026-03-14T10:05:00Z",
      "completed_at": "2026-03-14T10:45:00Z",
      "validator_result": null,
      "validator_notes": null
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
      "validator_notes": null
    }
  ],
  "gate_iterations": 0
}
```
