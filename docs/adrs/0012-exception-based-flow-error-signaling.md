# ADR-0012: Exception-Based Flow Error Signaling

## Status

Accepted — Supersedes ADR-0007

## Context

ADR-0007 established that `Flow.executeFlow()` injects a `SimulationLogger` and that emitting a `logger.error()` call
signals a fatal failure, after which the engine checks `logger.has_error` and halts execution with a failed
`SimulationResult`.

This conflation of **observability** and **control flow** into a single mechanism has three concrete problems:

1. **Implicit halt semantics**: the `logger.error()` method sounds like a logging call but secretly acts as a halt
   signal. Nothing in the type system or call signature makes this visible. A Flow author can easily call
   `logger.error()` for a genuinely non-fatal observation (e.g. a retried request that eventually succeeded) and
   accidentally halt the simulation.

1. **Unreachable code after `logger.error()`**: because the engine checks `has_error` only *after* the flow returns, the
   flow continues executing after the fatal call. This forces flow authors to add a manual `return` immediately after,
   obscuring intent.

1. **`SimulationResult` pollution**: a failed simulation propagates error state via `success`, `error_message`, and
   `log_messages` fields — three fields added solely to carry post-mortem information that Python's native exception
   mechanism already provides for free.

Python exceptions are the idiomatic mechanism for signaling unrecoverable conditions and unwinding the call stack
immediately. This decision adopts them for that purpose.

## Decision

Flows signal **genuinely unrecoverable, simulation-halting conditions** by raising a `FitineraError` subclass exception.
The engine does not catch these exceptions — they propagate to the caller.

### Exception hierarchy

```python
class FitineraError(Exception): ...  # base class for all fitinera exceptions


class InternalError(
    FitineraError
): ...  # invariant violations; should never happen in correct usage


class InvalidArgumentError(FitineraError): ...  # bad construction-time arguments


class NotFoundError(FitineraError): ...  # referenced entity does not exist


class SolvencyViolationError(InternalError): ...  # account solvency constraint breached
```

All five names are exported from `fitinera`'s public API.

### Raise-vs-log philosophy

| Situation                                                                                              | Recommended action                                            |
| ------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------- |
| Unrecoverable condition that **must stop** the simulation                                              | Raise the appropriate `FitineraError` subclass                |
| Error-level observation that does **not** stop the simulation (e.g. retries that eventually succeeded) | Call `logger.error()`                                         |
| Informational / diagnostic message                                                                     | Call `logger.info()`, `logger.debug()`, or `logger.warning()` |

Raising is **rare**. The contract is: a Flow that can raise must document the raised type in its docstring under a
`Raises:` section, so callers are never surprised. If the condition is not documented, it should not be raised.

### Subtype guidance

| Subtype                  | When to use                                                                                             |
| ------------------------ | ------------------------------------------------------------------------------------------------------- |
| `InternalError`          | An invariant that should never be violated in correct usage is violated — indicates a programming error |
| `InvalidArgumentError`   | A Flow is constructed with arguments that are logically invalid (e.g. a negative amount, an empty ID)   |
| `NotFoundError`          | The Flow references an entity (account, person, …) that does not exist in the simulation state          |
| `SolvencyViolationError` | An account's balance has breached its solvency constraint — used by `AccountSolvencyGuardFlow`          |

### Engine behaviour

`SimulationEngine.run()` does **not** wrap `flow.executeFlow()` or `metric_generator.evaluate()` in try/except blocks.
Any raised exception propagates directly to the caller of `run()`. There is no `logger.has_error` check.

### `logger.error()` is now purely observational

`SimulationLogger.error()` remains in the protocol. It dispatches to registered `LogListener` instances at the ERROR
level. It has **no halt semantics** and no `has_error` flag. Using `logger.error()` never stops the simulation on its
own.

### `SimulationResult` simplification

`success`, `error_message`, and `log_messages` are removed from `SimulationResult`. The dataclass retains only
`turns: List[Turn]`. Callers that previously inspected `result.success == False` should now use
`pytest.raises(FitineraError)` (or the specific subtype). Callers that relied on `result.log_messages` should register a
`ListLogListener` (see ADR-0013) and inspect `listener.messages`.

## Consequences

- **Positive: unambiguous halt semantics.** Raising an exception unwinds the call stack immediately and is visible in
  the Flow's type annotations and docstring. There is no ambiguity about whether execution continues.
- **Positive: simpler engine loop.** Removing the `has_error` check after every flow eliminates conditional branching
  from the hot path.
- **Positive: leaner `SimulationResult`.** Three fields removed; the dataclass now contains only the data it was
  designed to hold.
- **Negative: breaking change for callers of `SimulationEngine.run()`.** Code that tested `result.success` or read
  `result.log_messages` must be updated. This is expected and acceptable — `fitinera` is pre-release with no
  backwards-compatibility obligation.
- **Negative: discipline required from Flow authors.** The raise-vs-log distinction must be internalised. The flow
  development guide and this ADR document the rule; tooling (type annotations, docstring conventions) reinforce it.
- **ADR-0007 superseded.** The `logger.error()`-as-halt-signal model described there no longer applies.
