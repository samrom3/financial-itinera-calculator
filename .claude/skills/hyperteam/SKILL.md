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

## Phase 0: Pre-Flight

> **Prerequisites:** This skill requires the Agent Teams feature.
> Ensure `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is set in your environment.
> Also requires `gh` CLI installed and authenticated for PR creation.

Run these checks in order. **Stop and surface each issue as you encounter it.**

### Step 1 — Read settings and derive branch/slug

1. Read `.claude/settings.local.json` and extract `env.CLAUDE_CODE_TASK_LIST_ID` → this is `<branch>`.
2. Derive `<slug>` from `<branch>` by stripping the leading `feat-` prefix if present.
   - Example: `feat-hyperteam-skill` → `hyperteam-skill`
   - If `<branch>` does not start with `feat-`, use `<branch>` as `<slug>` unchanged.

### Step 2 — Verify git branch

1. Run `git branch --show-current`.
2. If the result matches `<branch>` — proceed.
3. If not — use `AskUserQuestion`:
   > The current git branch (`<actual>`) does not match the task list branch (`<branch>`). Continue
   > anyway, or pause to check out the correct branch?
4. If the user says pause, **stop here**.

### Step 3 — Detect fresh start vs. resume

Check whether `plans/<branch>-team-state.json` exists.

- **Absent** → Read `references/phase-1-fresh-start.md` and follow it in full, then return here
  and proceed to Phase 2.
- **Present** → Read `references/phase-1-resume.md` and follow it in full, then return here and
  proceed to Phase 2 (or stop if the user declines).

______________________________________________________________________

## Phase 2: Team Creation and Dispatch

### Step 1 — Create the team

Call `TeamCreate` with team name `<branch>`. The prompt should include the branch name and the
paths to `plans/<branch>-team-state.json`, `plans/<branch>-progress.txt`, and
`plans/<branch>-prd.md`.

### Step 2 — Dispatch the team lead

Dispatch `hyperteam-lead` via the Agent tool with `subagent_type: hyperteam-lead`, passing:

- `branch`: `<branch>`
- `team_state_path`: `plans/<branch>-team-state.json`
- `progress_path`: `plans/<branch>-progress.txt`
- Instruction: "Orchestrate all tasks in team-state.json until all FEAT and DOC tasks are
  validated/completed, then dispatch the GATE task."

### Step 3 — Wait

The main thread waits here. The team lead returns only after the GATE task passes. All worker,
validator, and gate dispatch happens inside the lead (see `.claude/agents/hyperteam-lead.md`).

______________________________________________________________________

## Phase 3: Back-Pressure Gate

> This phase runs **inside** the team lead's GATE dispatch — not on the main thread.
> The main thread remains at Phase 2 Step 3 while the gate runs.
> See `references/gate-task-template.md` for the full gate agent instructions.

The team lead returns to the main thread only after the GATE passes. Proceed to Phase 4.

______________________________________________________________________

## Phase 4: Completion and PR Offer

Read `references/phase-4-completion.md` and follow it in full.
