# Phase 1 — Resume

This path is taken when `plans/<branch>-team-state.json` already exists.

______________________________________________________________________

## Step 1 — Read authoritative state

- Read `plans/<branch>-team-state.json` (authoritative source of truth).
- Read `plans/<branch>-progress.txt` if it exists (for context only).

______________________________________________________________________

## Step 2 — Reconcile state

- Tasks with `status: completed` or `status: validated` are done — leave them.
- Any task with `status: in_progress` was interrupted — reset it to `pending`.
- `team-state.json` wins over `progress.txt` if they disagree.

______________________________________________________________________

## Step 3 — Render resume summary

Prepare a summary listing:

- Tasks already done: IDs and titles of all `completed` / `validated` tasks.
- Tasks remaining: IDs and titles of all `pending` tasks (after the reset in Step 2).
- Current `gate_iterations` count.

______________________________________________________________________

## Step 4 — Confirm with user

Use `AskUserQuestion` to present the summary and ask:

> Found existing run for `<branch>`.
> Completed: N tasks — <list of completed task IDs and titles>
> Remaining: M tasks — <list of remaining task IDs and titles>
> Gate iterations so far: G
>
> Continue with remaining tasks?

______________________________________________________________________

## Step 5 — Proceed or stop

- **If user confirms** — proceed to Phase 2 with `team-state.json` as-is. The team lead will pick
  up all `pending` tasks from where the run left off.
- **If user declines** — stop here. Leave state files unchanged.
