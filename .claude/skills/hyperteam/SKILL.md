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
