# ADR-0011: Unified Logger for Flow and MetricGenerator

## Status

Accepted

## Context

`Flow.executeFlow()` already received a `SimulationLogger` as its third argument, allowing flows to emit diagnostic
messages and signal fatal errors. `MetricGenerator.evaluate()` previously had no such access — it received only the
read-only `SimulationStateView`.

In practice, MetricGenerators can encounter conditions worth reporting: unrecognised account types, missing required
data, or computed values outside expected ranges. Without logger access, the only alternative was to import Python's
`logging` module directly inside the generator, bypassing the engine's unified observability layer and making those
messages invisible in `SimulationResult.log_messages`.

## Decision

Both `Flow.executeFlow()` and `MetricGenerator.evaluate()` receive a `SimulationLogger`:

```python
class Flow(Protocol):
    def executeFlow(
        self,
        view: SimulationStateView,
        updater: SimulationStateUpdater,
        logger: SimulationLogger,
    ) -> None: ...


class MetricGenerator(Protocol):
    def evaluate(self, view: SimulationStateView, logger: SimulationLogger) -> Any: ...
```

The logger passed to `MetricGenerator.evaluate()` is the same per-turn logger instance used for flows, so all messages
from a given turn are accumulated together in `SimulationResult.log_messages`.

`_SimulationLoggerImpl` now accumulates all messages in a `List[str]` (prefixed with their level), in addition to
delegating to the `fitinera.engine` Python logger for operator visibility.

## Consequences

- **Consistent observability**: all user extension points (Flows and MetricGenerators) use the same logging conventions
  and their output is captured in `SimulationResult.log_messages`.
- **Breaking change to `MetricGenerator.evaluate()`**: the signature changes from `(view) -> Any` to
  `(view, logger) -> Any`. This is a pre-release project (version `0.x`) with no backwards-compatibility obligation.
- **`SimulationResult` gains a `log_messages` field**: a `List[str]` containing all prefixed log messages from all
  turns, in chronological order. Error-turn messages are included even when the simulation halts early.
- **Per-flow error check**: the engine now checks `logger.has_error` after each individual flow call (not after all
  flows). The simulation halts immediately after the offending flow without executing subsequent flows in the same turn.
