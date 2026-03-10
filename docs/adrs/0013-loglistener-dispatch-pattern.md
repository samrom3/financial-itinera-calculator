# ADR-0013: LogListener Dispatch Pattern

## Status

Accepted

## Context

ADR-0011 mandated a unified `SimulationLogger` interface so that both `Flow.executeFlow()` and
`MetricGenerator.evaluate()` receive the same logger, ensuring all messages from a turn are captured together. That
decision left the *implementation* of `_SimulationLoggerImpl` unchanged: it accumulated messages in a `List[str]` and
delegated directly to `logging.getLogger("fitinera.engine")`. Both destinations were hard-coded.

This creates an extensibility problem: users who need a different log sink (structured JSON, a message queue, a test
double that captures messages in memory) have no supported hook. The only option is to monkey-patch Python's `logging`
module or read `result.log_messages` — a field that ADR-0012 removes from `SimulationResult`.

A listener-dispatch pattern is the standard solution: the logger implementation holds a list of registered sink objects
and calls the appropriate method on each one. Sinks are provided at construction time and can be swapped, combined, or
omitted freely. This is the same pattern used by Python's own `logging.Logger.handlers`.

This ADR builds directly on ADR-0011's unified-interface mandate: the `SimulationLogger` protocol signature is
unchanged; only the concrete implementation changes.

## Decision

`_SimulationLoggerImpl` is refactored to dispatch all log calls to a registered list of `LogListener` instances rather
than accumulating messages internally or calling `logging.getLogger` directly.

### `LogListener` protocol

```python
class LogListener(Protocol):
    def debug(self, msg: str) -> None: ...
    def info(self, msg: str) -> None: ...
    def warning(self, msg: str) -> None: ...
    def error(self, msg: str) -> None: ...
```

`LogListener` is exported from `fitinera`'s public API.

### Built-in implementations

| Class                   | Behaviour                                                                                                                                     |
| ----------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `PythonLoggingListener` | Delegates each call to `logging.getLogger("fitinera.engine")` at the corresponding Python logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `ListLogListener`       | Appends `[LEVEL] msg` strings to `self.messages: List[str]` in chronological order; useful in tests and for programmatic inspection           |

Both are exported from `fitinera`'s public API.

### `_SimulationLoggerImpl` dispatch semantics

`_SimulationLoggerImpl.__init__` accepts `listeners: List[LogListener]`. On each log call, the impl iterates the list in
registration order and invokes the corresponding method on every listener. If any listener raises, the exception
propagates immediately out of `_SimulationLoggerImpl` — no swallowing. This means a misbehaving listener halts the
engine, which is intentional: silent listener failures would corrupt observability guarantees.

### Default configuration

`EngineConfiguration.log_listeners` defaults to `[PythonLoggingListener()]`. This preserves the pre-existing behaviour
of writing messages to the `fitinera.engine` Python logger, maintaining operator visibility with zero configuration
changes for existing users.

### Opt-out

Users who want no logging pass `log_listeners=[]` to `EngineConfiguration`. This is a supported, documented option.

### Portability intent

The `LogListener` protocol is deliberately minimal (four methods, all accepting a single `str`). The intent is that
future sinks — structured JSON writers, ZeroMQ publishers, Apache Pulsar producers, OpenTelemetry spans — can implement
the protocol without pulling in fitinera internals. Synchronous, in-process dispatch is the only supported model; async
listeners are explicitly out of scope.

## Consequences

- **Positive: extensible log routing.** Users can register any combination of listeners without modifying fitinera
  internals.
- **Positive: test-friendly.** `ListLogListener` gives tests a deterministic, in-memory log capture. No patching of
  Python's `logging` module or reading `result.log_messages` is needed.
- **Positive: explicit opt-out.** Passing `log_listeners=[]` suppresses all output without touching Python's logging
  configuration.
- **Negative: breaking change for callers using `result.log_messages`.** Those callers must now register a
  `ListLogListener` and read `listener.messages`. This is expected and documented.
- **`_SimulationLoggerImpl` internal properties removed.** `has_error`, `error_message`, and `messages` are removed (see
  also ADR-0012). Message accumulation is the responsibility of `ListLogListener`, not the impl.
- **ADR-0011 is not superseded.** The unified-interface mandate (both `Flow` and `MetricGenerator` receive the same
  `SimulationLogger`) remains in force. ADR-0013 changes the *implementation* of the logger; ADR-0011 governs the
  *protocol signature* that user code depends on.
