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

______________________________________________________________________

## Phase 2: Write team-state.json and Initialise Team

______________________________________________________________________

## Phase 3: Dispatch Loop

______________________________________________________________________

## Phase 4: Back-Pressure Gate

______________________________________________________________________

## Phase 5: Completion and PR Offer
