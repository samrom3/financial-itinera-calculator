# ADR-0007: Flow Observability & Error Handling via Logger

## Status

Accepted

## Context

Complex custom logic within Flows needs a way to communicate state to the user or gracefully halt the simulation if
assumptions are broken.

## Decision

Inject a SimulationLogger into executeFlow(). The logger supports debug, info, warning, and error messages.

## Consequences

Emitting an error shifts responsibility to the Engine to halt execution and return a failed SimulationResult.
