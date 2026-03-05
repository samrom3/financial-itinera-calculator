# ADR-0001: The Pipeline Framework Paradigm

## Status

Accepted

## Context

V0 relied on rigid OOP builders that tangled state definition with execution logic.

## Decision

We will adopt a pipeline architecture. The simulation logic is defined as an ordered sequence of components
(EngineConfiguration) that process a starting data state (SimulationScenario).

## Consequences

Unlocks infinite flexibility. Users can inject custom logic anywhere in the simulation loop.
