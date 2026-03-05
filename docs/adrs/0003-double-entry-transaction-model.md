# ADR-0003: Double-Entry Transaction Model

## Status

Accepted

## Context

V0 treated money movements ambiguously, making it hard to track where money came from or went.

## Decision

All value mutation occurs strictly via Transactions emitted to the SimulationStateUpdater. Transactions are typed as
Income, Expense, or Transfer.

## Consequences

Perfect conservation of money within the defined financial system.
