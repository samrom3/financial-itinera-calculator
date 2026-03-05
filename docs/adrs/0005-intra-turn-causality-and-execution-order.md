# ADR-0005: Intra-Turn Causality & Execution Order

## Status

Accepted

## Context

In a sequential pipeline, does Flow #2 see the account balances *before* or *after* Flow #1's transactions have been
applied?

## Decision

The SimulationStateUpdater will immediately apply (or simulate applying) changes so that subsequent Flows in the
pipeline see the updated balance state via the SimulationStateView.

## Consequences

Order of Flow configuration strictly matters.
