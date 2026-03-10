# ADR-0012: Return-Value Flow Error Signaling via FitineraResult Hierarchy

## Status

Accepted — Supersedes ADR-0007

## Context

ADR-0007 established that `Flow.executeFlow()` injects a `SimulationLogger` and that emitting a `logger.error()` call
signals a fatal failure, after which the engine checks `logger.has_error` and halts execution with a failed
`SimulationResult`.

This conflation of **observability** and **control flow** into a single mechanism had three concrete problems:

1. **Implicit halt semantics**: `logger.error()` sounds like a logging call but secretly acted as a halt signal. A Flow
   author could easily call it for a non-fatal observation and accidentally halt the simulation.

1. **Unreachable code after `logger.error()`**: the engine checked `has_error` only *after* the flow returned, so the
   flow continued executing. Authors needed a manual `return` immediately after, obscuring intent.

1. **`SimulationResult` pollution**: `success`, `error_message`, and `log_messages` fields were added solely to carry
   post-mortem information that belonged in a structured result type.

During PR review (#27) it was also identified that using Python's `Exception` hierarchy for halt signals was
inappropriate: simulation halt conditions are **value-level outcomes**, not exceptional control-flow events. They should
be expressible as plain data, inspectable without try/except, and composable with the engine's return type.

## Decision

Flows signal halt conditions by **returning a value**, not by raising an exception.

`Flow.executeFlow()` returns `Optional[FitineraError]`:

- `None` — simulation should continue.
- A `FitineraError` instance — unrecoverable condition; engine halts and embeds the error in `SimulationData.result`.

### FitineraResult hierarchy

All halt signals and the simulation outcome type form a single value hierarchy (not Python exceptions):

```python
class FitineraResult(ABC):  # abstract — ok(), message(), __str__
    ...


class FitineraSuccess(FitineraResult):  # ok() → True
    ...


class ReachedAllPersonsExpectancy(FitineraSuccess): ...


class ReachedMaxTurns(FitineraSuccess): ...


class FitineraError(FitineraResult):  # ok() → False; carries a message string
    def __init__(self, msg: str = "") -> None: ...


class InternalError(FitineraError): ...


class InvalidArgumentError(FitineraError): ...


class NotFoundError(FitineraError): ...


class SolvencyViolationError(InternalError): ...
```

`FitineraError` does **not** inherit from `Exception`. It is a plain Python class with an `ok()` predicate and a
`message()` string accessor.

### SimulationData

`SimulationResult` is renamed to `SimulationData`. Its structure:

```python
@dataclass(frozen=True)
class SimulationData:
    result: FitineraResult
    turns: List[Turn]
```

`result` is always a `FitineraResult` instance — either a `FitineraSuccess` subclass for normal completion or a
`FitineraError` subclass for an error halt. Callers inspect `result.ok()` to determine which.

### Engine behaviour

`SimulationEngine.run()` checks the return value of each `flow.executeFlow()` call:

```python
error = flow.executeFlow(view, updater, logger)
if error is not None:
    return SimulationData(result=error, turns=history)
```

Normal halt conditions are embedded the same way:

```python
return SimulationData(result=ReachedAllPersonsExpectancy(), turns=history)
return SimulationData(result=ReachedMaxTurns(), turns=history)
```

There is no try/except block and no `has_error` check.

### Return-vs-log philosophy

| Situation                                                     | Recommended action                                                   |
| ------------------------------------------------------------- | -------------------------------------------------------------------- |
| Unrecoverable condition that **must stop** the simulation     | Return the appropriate `FitineraError` subclass from `executeFlow()` |
| Error-level observation that does **not** stop the simulation | Call `logger.error()`                                                |
| Informational / diagnostic message                            | Call `logger.info()`, `logger.debug()`, or `logger.warning()`        |

Returning a `FitineraError` is **rare**. The contract is: a Flow that can return a `FitineraError` must document the
returned type in its docstring under a `Returns:` section, so callers are never surprised.

### Subtype guidance

| Subtype                  | When to use                                                                                             |
| ------------------------ | ------------------------------------------------------------------------------------------------------- |
| `InternalError`          | An invariant that should never be violated in correct usage is violated — indicates a programming error |
| `InvalidArgumentError`   | A Flow is constructed with arguments that are logically invalid (e.g. a negative amount, an empty ID)   |
| `NotFoundError`          | The Flow references an entity (account, person, …) that does not exist in the simulation state          |
| `SolvencyViolationError` | An account's balance has breached its solvency constraint — used by `AccountSolvencyGuardFlow`          |

### Module location

All result types (`FitineraResult`, `FitineraSuccess`, `FitineraError`, and all subclasses, plus `SimulationData`) live
in `fitinera.engine.result`. Import from `fitinera.engine.result` directly, or from the top-level `fitinera` package.
The module `fitinera.engine.exceptions` does not exist.

## Consequences

- **Positive: unambiguous halt semantics.** `executeFlow()` returning a non-None value is visible in the type signature.
  There is no ambiguity about whether execution continues — the engine checks immediately.
- **Positive: inspectable without try/except.** Callers can `data.result.ok()` or
  `isinstance(data.result, FitineraError)` without wrapping `engine.run()` in a try block.
- **Positive: simpler engine loop.** The hot path is a single `if error is not None` check per flow — no branching on
  logger state.
- **Positive: leaner SimulationData.** The renamed dataclass holds only `result` and `turns`; all post-mortem fields
  removed.
- **Negative: breaking change for existing callers.** Code that used `pytest.raises(FitineraError)` must be updated to
  inspect `data.result`. Code that read `result.success` or `result.log_messages` must be updated. This is acceptable —
  `fitinera` is pre-release with no backwards-compatibility obligation.
- **Negative: discipline required from Flow authors.** The return-vs-log distinction must be internalised. This ADR and
  the flow development guide document the rule; type annotations reinforce it.
- **ADR-0007 superseded.** The `logger.error()`-as-halt-signal model described there no longer applies.
