# Flow Development Guide

This guide is the canonical reference for writing custom `Flow` and `MetricGenerator` components in fitinera. It covers
the contracts, available APIs, condition composition, pipeline ordering, and a fully annotated worked example.

______________________________________________________________________

## What is a Flow?

A `Flow` is a computational component that **mutates** the simulation state once per turn. It is the primary extension
point in fitinera: every financial event — income, expenses, debt payments, portfolio rebalancing, label transitions —
is expressed as a `Flow`.

Flows are plain Python classes. They implement a single method:

```python
class Flow(Protocol):
    def executeFlow(
        self,
        view: SimulationStateView,
        updater: SimulationStateUpdater,
        logger: SimulationLogger,
    ) -> Optional[FitineraError]: ...
```

There is no base class to inherit from. Any object that exposes `executeFlow(view, updater, logger)` satisfies the
`Flow` protocol. If you prefer compile-time enforcement, you can explicitly inherit from `Flow` — this gives IDE
autocomplete and mypy will verify your implementation at the class definition site rather than only at call sites.

______________________________________________________________________

## What is a MetricGenerator?

A `MetricGenerator` is a **read-only** computational component that derives a value from the current simulation state.
It does not emit transactions, mutate balances, or update person labels — those are the exclusive domain of `Flow`.

```python
class MetricGenerator(Protocol):
    def evaluate(self, view: SimulationStateView, logger: SimulationLogger) -> Any: ...
```

**Evaluation semantics:** MetricGenerators are not evaluated once per turn in the way Flows are. Instead:

- Any Flow can call `view.get_metric("name")` to trigger evaluation at that exact intra-turn point (lazy evaluation).
- All registered MetricGenerators are also evaluated at the **end of each turn** to populate `Turn.metrics` in the
  snapshot.

This means a MetricGenerator may be evaluated multiple times within a single turn if several Flows call `get_metric`.

**Logger access:** `evaluate(view, logger)` receives the same per-turn `SimulationLogger` instance as Flows. Use
`logger.warning()` to report anomalies (unrecognised account types, missing data) without resorting to Python's
`logging` module directly.

**Registration and access:** register in `EngineConfiguration.metrics`; call via `view.get_metric("name")` from any
Flow.

```python
class NetWorthGenerator(MetricGenerator):
    def evaluate(self, view: SimulationStateView, logger: SimulationLogger) -> float:
        assets = sum(
            a.balance for a in view.get_accounts() if a.get_label("Type") == "ASSET"
        )
        liabilities = sum(
            a.balance for a in view.get_accounts() if a.get_label("Type") == "LIABILITY"
        )
        return assets - liabilities
```

Register it once in `EngineConfiguration.metrics` and call `view.get_metric("Net_Worth")` from any Flow.

______________________________________________________________________

## The `executeFlow` Contract

```python
def executeFlow(
    self,
    view: SimulationStateView,
    updater: SimulationStateUpdater,
    logger: SimulationLogger,
) -> Optional[FitineraError]: ...
```

### `view` — `SimulationStateView`

Read-only access to the current and past simulation state.

| Method                                 | Returns              | Notes                                                                          |
| -------------------------------------- | -------------------- | ------------------------------------------------------------------------------ |
| `view.get_accounts()`                  | `List[AccountState]` | All accounts, live balances reflect transactions so far this turn              |
| `view.get_person(person_id)`           | `Optional[Person]`   | Returns `None` if not found; always check before use                           |
| `view.get_metric(name)`                | `Any`                | Lazily evaluates the named `MetricGenerator`; returns `None` if not registered |
| `view.get_start_date()`                | `Date`               | The `Date` the simulation began                                                |
| `view.get_current_date()`              | `Date`               | The `Date` of the turn being executed right now                                |
| `view.get_elapsed_duration()`          | `TurnDuration`       | Months elapsed since start; `.years` and `.years_frac` are derived             |
| `view.get_current_turn_transactions()` | `List[Transaction]`  | Transactions emitted so far within the current turn                            |

**Intra-turn visibility ([ADR-0005](../adrs/0005-intra-turn-causality-and-execution-order.md)):** transactions emitted
earlier in the pipeline are immediately visible to later flows in the same turn. `view.get_accounts()` always reflects
the current, live balance — not the snapshot from the previous turn.

### `updater` — `SimulationStateUpdater`

Controlled write access for the current turn only.

| Method                                                 | Effect                                               |
| ------------------------------------------------------ | ---------------------------------------------------- |
| `updater.emit_transaction(transaction)`                | Applies the transaction and appends it to the buffer |
| `updater.update_person_label(person_id, facet, value)` | Immediately changes a person's label value           |

### `logger` — `SimulationLogger`

| Method                | Effect                                                       |
| --------------------- | ------------------------------------------------------------ |
| `logger.debug(msg)`   | Low-level trace message (visible at DEBUG log level)         |
| `logger.info(msg)`    | Informational message (e.g. flow skipped)                    |
| `logger.warning(msg)` | Non-fatal anomaly                                            |
| `logger.error(msg)`   | Error-level observational log — does not halt the simulation |

Use `logger.error` for non-halting error-level observations (e.g. a downstream service needed retries but eventually
succeeded — worth alerting the user, but the simulation can continue). Use `logger.warning` for expected edge cases that
should be visible but are not fatal. To halt the simulation for a genuine unrecoverable condition, return a
`FitineraError` subclass instance instead — see "When to return vs. when to log" below.

______________________________________________________________________

## When to return vs. when to log

Fitinera draws a sharp line between **error signaling** (returning a `FitineraError` value) and **error observation**
(logging at `ERROR` level). Understanding this distinction is essential for writing well-behaved flows.

### Return `FitineraError` for genuine unrecoverable conditions

Return a `FitineraError` subclass instance when the simulation **cannot meaningfully continue** — the invariant is
broken and proceeding would produce misleading results. Return `None` on the normal (continue) path. Returning a halt is
**rare**. Every flow that can return a halt must document the return type in its `executeFlow` docstring under a
`Returns:` section so callers are never surprised.

```python
def executeFlow(
    self,
    view: SimulationStateView,
    updater: SimulationStateUpdater,
    logger: SimulationLogger,
) -> Optional[FitineraError]:
    """Check account solvency and halt if the balance is negative.

    Args:
        view: Read-only view of the current simulation state.
        updater: Write interface (unused by this flow).
        logger: Logging interface for audit messages.

    Returns:
        None to continue the simulation, or SolvencyViolationError when the
        account balance falls below zero.
    """
    account = view.get_account(self.account_id)
    if account.balance < 0:
        return SolvencyViolationError(
            f"Account '{self.account_id}' is insolvent: balance={account.balance:.2f}"
        )
    return None
```

### Use `logger.error()` for non-halting error-level observations

Use `logger.error()` when something went wrong or unexpected but the simulation can still continue and the result is
still meaningful. The log entry alerts the user without stopping the run.

```python
# A web-service retry eventually succeeded — log at ERROR to surface the alert,
# but do not halt the simulation.
logger.error(
    f"ExchangeRateFlow: rate service returned 503; used fallback rate {fallback_rate}"
)
```

### `FitineraError` subtype guidance

| FitineraError subtype    | When to use                                                                                   |
| ------------------------ | --------------------------------------------------------------------------------------------- |
| `InternalError`          | An invariant that should never occur has been violated (programming error or corrupt state)   |
| `InvalidArgumentError`   | A construction-time argument is invalid (caught at `__init__` time, not during `executeFlow`) |
| `NotFoundError`          | A required entity (account, person) does not exist and the flow cannot proceed without it     |
| `SolvencyViolationError` | An account's balance has fallen below its solvency floor (subtype of `InternalError`)         |

______________________________________________________________________

## Writing a `LogListener`

`LogListener` implementations receive every log message dispatched by the engine. They must be:

- **Fast**: called synchronously on the engine's main thread during every flow execution; never block on I/O, network,
  or locks inside a listener.
- **Synchronous**: async implementations are not supported. Off-load to a queue if you need async delivery.
- **Deterministic**: avoid side effects that depend on external state. Listeners run inside the simulation loop and
  non-deterministic behaviour will make simulations harder to reproduce.
- **Non-raising (by preference)**: if a listener raises, the exception propagates immediately out of
  `_SimulationLoggerImpl` and halts the engine. This is the intended safety behaviour — a broken log sink should not
  silently swallow messages — but it means listener bugs become simulation crashes. Test listeners thoroughly.

### Minimal `LogListener` example

```python
from fitinera import LogListener


class PrintListener:
    """Prints every log message to stdout — useful for debugging."""

    def debug(self, msg: str) -> None:
        print(f"[DEBUG] {msg}")

    def info(self, msg: str) -> None:
        print(f"[INFO] {msg}")

    def warning(self, msg: str) -> None:
        print(f"[WARNING] {msg}")

    def error(self, msg: str) -> None:
        print(f"[ERROR] {msg}")
```

Register it via `EngineConfiguration`:

```python
config = EngineConfiguration(
    ...,
    log_listeners=[PrintListener()],
)
```

To disable all logging (e.g. in tight benchmark loops), pass `log_listeners=[]`.

______________________________________________________________________

## Emitting Transactions

All transactions are **immutable dataclasses**. Emit them via `updater.emit_transaction()`.

### `Income` — money entering from outside the simulation

```python
from fitinera import Income

updater.emit_transaction(
    Income(
        amount=5000.0,
        to_account="Joint Checking",
        labels={"IncomeType": "ACTIVE"},
    )
)
```

`Income` increases `to_account.balance` by `amount`.

### `Expense` — money leaving the simulation

```python
from fitinera import Expense

updater.emit_transaction(
    Expense(
        amount=2500.0,
        from_account="Joint Checking",
        labels={"Category": "HOUSING"},
    )
)
```

`Expense` decreases `from_account.balance` by `amount`.

### `Transfer` — money moving between accounts within the simulation

```python
from fitinera import Transfer

updater.emit_transaction(
    Transfer(
        amount=1000.0,
        from_account="Joint Checking",
        to_account="Brokerage",
    )
)
```

`Transfer` decreases `from_account.balance` and increases `to_account.balance` by `amount`.

The `labels` field on every transaction is optional (`dict[str, str]`). Use it to annotate transactions for downstream
inspection via `view.get_current_turn_transactions()`.

______________________________________________________________________

## Reading State in Practice

### Checking person status before acting

Always verify that the person exists and is living before emitting income or expenses tied to them:

```python
def executeFlow(self, view, updater, logger):
    person = view.get_person(self.person_id)
    if person is None:
        logger.warning(f"Person '{self.person_id}' not found; skipping.")
        return
    if not person.living():
        logger.info(f"Person '{self.person_id}' is no longer living; skipping.")
        return
    if person.get_label("Status") != "Working":
        logger.info(f"Person '{self.person_id}' is not working; skipping income.")
        return
    updater.emit_transaction(Income(amount=self.amount, to_account=self.to_account))
```

### Using elapsed time

`view.get_elapsed_duration().months` is the zero-based turn index (0 at the first turn):

```python
turn_index = view.get_elapsed_duration().months  # 0, 1, 2, ...
inflated = self.base_amount * (1 + self.annual_rate / 12) ** turn_index
```

### Using the current calendar date

```python
current_date = view.get_current_date()
is_december = current_date.month == 12
```

### Inspecting this turn's transactions

To compute a derived quantity from transactions already emitted this turn (e.g. to calculate a minimum buffer based on
current expenses), use `view.get_current_turn_transactions()`:

```python
from fitinera import Expense

total_expenses = sum(
    t.amount
    for t in view.get_current_turn_transactions()
    if isinstance(t, Expense) and t.from_account == self.account_id
)
```

______________________________________________________________________

## Using Conditions

A `Condition` is a predicate evaluated against a `SimulationStateView`. Conditions decouple triggering logic from the
flow body, making both reusable and testable in isolation.

### Built-in conditions

```python
from fitinera import (
    ComparisonOperator,
    PersonAgeIs,
    PersonLabelIs,
    AccountBalanceIs,
    MetricCondition,
    Age,
)

GE = ComparisonOperator.GE
GT = ComparisonOperator.GT

# Fire when person "Sam" reaches age 65
retirement_trigger = PersonAgeIs("Sam", GE, Age(years=65))

# Fire when person "Sam" is already retired
is_retired = PersonLabelIs("Sam", "Status", "Retired")

# Fire when checking account balance exceeds $50,000
has_surplus = AccountBalanceIs("Joint Checking", GT, 50_000)

# Fire when net worth exceeds $1,000,000
millionaire = MetricCondition("Net_Worth", GT, 1_000_000.0)
```

All built-in conditions return `False` (never raise) when the referenced entity is not found (FR-013).

### Composing conditions

Use `ConditionAnd` and `ConditionOr` to build compound predicates. Both short-circuit.

```python
from fitinera import ConditionAnd, ConditionOr

# Retire when Sam is 65 AND net worth > $1M
compound = ConditionAnd(
    left=PersonAgeIs("Sam", GE, Age(years=65)),
    right=MetricCondition("Net_Worth", GT, 1_000_000.0),
)

# React when either Sam or Alex reaches 65
either_retired = ConditionOr(
    left=PersonAgeIs("Sam", GE, Age(years=65)),
    right=PersonAgeIs("Alex", GE, Age(years=65)),
)
```

### Using conditions inside a Flow

```python
from fitinera import Flow, PersonLabelIs


class RetirementDrawdownFlow(Flow):
    def __init__(self, person_id: str, amount: float, from_account: str):
        self._condition = PersonLabelIs(person_id, "Status", "Retired")
        self.amount = amount
        self.from_account = from_account

    def executeFlow(self, view, updater, logger):
        if not self._condition.evaluate(view):
            return
        updater.emit_transaction(
            Expense(amount=self.amount, from_account=self.from_account)
        )
```

______________________________________________________________________

## Pipeline Ordering Best Practices

Flows in `EngineConfiguration.flows` execute in the order they are listed. Because ADR-0005 establishes that each
transaction is immediately applied (intra-turn causality), **order matters**.

### General ordering principles

1. **Income flows first** — deposit salary/income before expenses are drawn.
1. **Expense flows second** — deduct living costs, mortgage payments, etc. after income.
1. **Interest flows after balances are updated** — `AccountInterestFlow` should run after income and before or after
   expenses depending on whether you want interest to compound on the post-income or post-expense balance.
1. **Rebalancing flows last** — `RebalanceExtraSavingsFlow` must run after `LivingExpenseFlow` because it uses
   `view.get_current_turn_transactions()` to compute the current-turn expense total. If `RebalanceExtraSavingsFlow` ran
   before `LivingExpenseFlow`, it would see zero expenses and compute a minimum buffer of zero, transferring the entire
   checking balance to brokerage.
1. **Guard flows last** — `AssetSolvencyGuardFlow` should be the final flow so that all mutations for the turn are
   complete before the guard inspects balances.
1. **Lifecycle flows (retirement transitions) after income** — if retirement is conditioned on net worth, place
   `PersonRetirementLabelFlow` after the income and interest flows that grow net worth; otherwise the transition fires
   one turn late.

### Canonical ordering example

```python
flows = [
    JobIncomeFlow(person_id="Sam", amount=8333, to_account="Checking"),
    AccountInterestFlow(account_id="Brokerage", annual_rate=0.07),
    LivingExpenseFlow(from_account="Checking", amount=4167, annual_inflation_rate=0.02),
    RebalanceExtraSavingsFlow(
        from_account="Checking",
        to_account="Brokerage",
        strategy=CurrentTurnExpenseStrategy(expense_multiplier=3.0),
    ),
    PersonRetirementLabelFlow(
        person_ids=["Sam"],
        condition=PersonAgeIs("Sam", ComparisonOperator.GE, Age(years=65)),
    ),
    AssetSolvencyGuardFlow(),  # always last
]
```

______________________________________________________________________

## Worked Example: `AnnualBonusFlow`

The following fully-annotated example implements a flow that deposits an annual bonus into a checking account every
December (the 12th month of each calendar year). It demonstrates:

- Constructor parameterisation (person ID, amount, target account)
- Calendar-date gating via `view.get_current_date()`
- Person liveness and label checking
- A conditional `Income` emission with a descriptive label

```python
from typing import Optional

from fitinera import (
    Flow,
    FitineraError,
    Income,
    SimulationStateView,
    SimulationStateUpdater,
    SimulationLogger,
)


class AnnualBonusFlow(Flow):
    """Deposits an annual year-end bonus in December if the person is still working.

    The bonus is credited to ``to_account`` on the December turn of every
    simulated calendar year. No bonus is emitted if the person is deceased,
    retired, or not found in the simulation state.

    Args:
        person_id: Identifier of the person whose employment status is checked.
        amount: Gross bonus amount to deposit each December.
        to_account: Account identifier that receives the bonus.
    """

    def __init__(self, person_id: str, amount: float, to_account: str):
        self.person_id = person_id
        self.amount = amount
        self.to_account = to_account

    def executeFlow(
        self,
        view: SimulationStateView,
        updater: SimulationStateUpdater,
        logger: SimulationLogger,
    ) -> Optional[FitineraError]:
        """Emit the annual bonus income when the current turn falls in December.

        Guards:
        1. Only fires in the calendar month of December (month == 12).
        2. Person must exist in the simulation.
        3. Person must be living.
        4. Person must carry the label Status == 'Working'.

        Args:
            view: Read-only view of the current simulation state.
            updater: Write interface for emitting the bonus transaction.
            logger: Logging interface for audit messages.

        Returns:
            None in all cases — this flow never halts the simulation.
        """
        # Gate 1: only act in December
        current_date = view.get_current_date()
        if current_date.month != 12:
            return

        # Gate 2: person must exist
        person = view.get_person(self.person_id)
        if person is None:
            logger.warning(
                f"AnnualBonusFlow: person '{self.person_id}' not found; skipping bonus."
            )
            return

        # Gate 3: person must be living
        if not person.living():
            logger.info(
                f"AnnualBonusFlow: person '{self.person_id}' is not living; "
                "skipping bonus."
            )
            return

        # Gate 4: person must still be working
        status = person.get_label("Status")
        if status != "Working":
            logger.info(
                f"AnnualBonusFlow: person '{self.person_id}' is not working "
                f"(Status={status}); skipping bonus."
            )
            return

        # All guards passed — emit the bonus
        updater.emit_transaction(
            Income(
                amount=self.amount,
                to_account=self.to_account,
                labels={"IncomeType": "BONUS", "Month": "December"},
            )
        )
        logger.info(
            f"AnnualBonusFlow: deposited ${self.amount:,.2f} bonus for "
            f"'{self.person_id}' in {current_date.year}-12."
        )
        return None
```

### Usage in an `EngineConfiguration`

```python
from fitinera import EngineConfiguration, Date, TurnDuration

config = EngineConfiguration(
    start_date=Date(year=2026, month=1),
    max_turns=TurnDuration.of(years=40),
    metrics={},
    flows=[
        JobIncomeFlow(person_id="Sam", amount=8333, to_account="Checking"),
        AnnualBonusFlow(person_id="Sam", amount=10_000, to_account="Checking"),
        LivingExpenseFlow(from_account="Checking", amount=4000),
    ],
)
```

Because `AnnualBonusFlow` fires only in December, `view.get_current_turn_transactions()` in a downstream
`RebalanceExtraSavingsFlow` will see the bonus amount included in the balance for that turn — correctly increasing the
surplus available to sweep into investments.

______________________________________________________________________

## Summary Checklist

Before adding a new Flow to a pipeline:

1. Does it need to mutate state (balances or labels)? If not, use a `MetricGenerator` instead.
1. Are all guard conditions handled (person not found, wrong label, wrong date)?
1. Does `executeFlow` return `None` on the normal path and a `FitineraError` only for genuinely unrecoverable
   conditions, documented under a `Returns:` section in the Flow's docstring?
1. Does the flow's position in the pipeline respect intra-turn causality (ADR-0005)?
1. Does the flow accept its parameters via the constructor rather than hard-coding scenario-specific values?
