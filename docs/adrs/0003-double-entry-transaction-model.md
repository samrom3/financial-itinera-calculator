# ADR-0003: Double-Entry Transaction Model

## Status

Accepted

## Context

V0 treated money movements ambiguously, making it hard to track where money came from or went.

## Decision

All value mutation occurs strictly via Transactions emitted to the SimulationStateUpdater. Transactions are typed as
Income, Expense, or Transfer.

**Clarifying note (added alongside ADR-0015):** Despite the ADR title, fitinera's transaction model is a **typed
single-entry transaction model** (`Income`, `Expense`, `Transfer`) inspired by double-entry principles — not a true
double-entry system with debit/credit journal entries. Each transaction type carries a single amount and one or two
account references, rather than a balanced set of postings. The title "Double-Entry Transaction Model" is retained for
historical continuity. See [`docs/research/issue-31-accounting-model.md`](../research/issue-31-accounting-model.md),
Section 9 (Gap 5) for further discussion.

## Consequences

Perfect conservation of money within the defined financial system.
