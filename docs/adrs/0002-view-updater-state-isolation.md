# ADR-0002: View/Updater State Isolation

## Status

Accepted

## Context

Flows need to read past/current state and mutate the current state, but allowing direct mutation of the core state
objects risks corrupting the audit trail and timeline.

## Decision

Flow.executeFlow() will only receive a SimulationStateView (read-only) and SimulationStateUpdater (controlled writes).
The Engine handles applying the updater's staged changes to the actual Account and Turn objects.

## Consequences

Guarantees a pristine historical audit trail.
