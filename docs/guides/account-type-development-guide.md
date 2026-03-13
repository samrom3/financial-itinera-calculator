# Account Type Development Guide

This guide is the canonical reference for extending the fitinera account type hierarchy. It covers when to subclass
`AssetAccount` vs `LiabilityAccount`, how to implement the required factory methods, and how built-in flows interact
with new subtypes automatically.

For the design rationale behind the typed hierarchy, see [ADR-0014](../adrs/0014-typed-account-hierarchy-with-abc.md).

______________________________________________________________________

## The Account Hierarchy

Fitinera models accounts as two parallel, mirrored hierarchies:

```
Account (ABC, frozen=True)          AccountState (ABC, mutable)
├── AssetAccount       ←→           ├── AssetAccountState
└── LiabilityAccount   ←→           └── LiabilityAccountState
```

`Account` subclasses are **immutable frozen dataclasses** used in `SimulationScenario` configuration and Turn history.
`AccountState` subclasses are **mutable dataclasses** maintained by the engine during a simulation run.

The factory methods `to_state()` (on `Account`) and `to_snapshot()` (on `AccountState`) form the only coupling between
the two hierarchies. Direct construction of the abstract base classes (`Account(...)` or `AccountState(...)`) raises
`TypeError` at runtime.

______________________________________________________________________

## When to subclass `AssetAccount` vs `LiabilityAccount`

### Use `AssetAccount` when the account represents value the simulation owner **holds**

Asset accounts have a positive-balance convention: a balance of `10_000.0` means the owner holds ten thousand units of
currency. Examples:

- Savings accounts, current/checking accounts
- Investment or brokerage portfolios
- Cash holdings, emergency funds
- Pension pots (accumulation phase)

### Use `LiabilityAccount` when the account represents a debt the simulation owner **owes**

Liability accounts track outstanding obligations. By convention, they carry **positive** balances representing the
amount of debt owed (e.g. a $300,000 mortgage is stored as `balance=300_000.0`). Net worth is calculated as
`total assets − total liabilities`, both positive. Examples:

- Mortgages
- Personal loans or student loans
- Credit card balances

A `__post_init__` validator on `LiabilityAccount` raises `ValueError` if `balance < 0`, catching misconfiguration at
scenario construction time. See [ADR-0015](../adrs/0015-liability-balance-sign-convention.md) for the full rationale.

If an account does not fit cleanly into either category (e.g. a complex instrument that is simultaneously asset and
liability), model it as an `AssetAccount` with an explanatory label and document the convention in the scenario.

> **Migration note (ADR-0015):** Prior to ADR-0015, liability balances were stored as negative numbers. If you have
> user-written flows or conditions that check liability balance thresholds, you must update them. For example, a
> condition like `acct.balance > -50_000` (checking a negative balance approaching zero) should become
> `acct.balance < 50_000` (checking a positive balance decreasing toward zero). Similarly, `acct.balance < 0` no longer
> indicates "debt exists" — under the positive convention, `acct.balance > 0` means "debt exists."

______________________________________________________________________

## Implementing a new account subtype: `SavingsAccount`

The following worked example adds a `SavingsAccount` subtype that carries an interest rate alongside the standard `id`,
`balance`, and `labels` fields.

### Step 1 — Define the frozen snapshot subclass

```python
from dataclasses import dataclass
from fitinera import AssetAccount, AssetAccountState


@dataclass(frozen=True)
class SavingsAccount(AssetAccount):
    """A frozen snapshot of a savings account with a named interest rate.

    Args:
        id: Unique account identifier.
        balance: Current account balance.
        annual_rate: Annual interest rate as a decimal (e.g. 0.04 for 4 %).
        labels: Optional semantic annotations.
    """

    annual_rate: float = 0.0

    def to_state(self) -> "SavingsAccountState":
        """Produce a SavingsAccountState initialised from this snapshot.

        Returns:
            A SavingsAccountState with id, balance, labels, and annual_rate
            copied from this snapshot, ready for in-place mutation by the engine.
        """
        return SavingsAccountState(
            id=self.id,
            balance=self.balance,
            labels=dict(self.labels),
            annual_rate=self.annual_rate,
        )
```

### Step 2 — Define the mutable live-state subclass

```python
@dataclass
class SavingsAccountState(AssetAccountState):
    """Mutable live state of a savings account.

    Maintained by the engine during a simulation run. Carries the same
    ``annual_rate`` as the snapshot so flows can read it without needing
    to look up the original scenario configuration.
    """

    annual_rate: float = 0.0

    def to_snapshot(self) -> SavingsAccount:
        """Produce a frozen SavingsAccount snapshot from the current state.

        Returns:
            A frozen SavingsAccount with id, balance, labels, and annual_rate
            copied from the current mutable state.
        """
        return SavingsAccount(
            id=self.id,
            balance=self.balance,
            labels=dict(self.labels),
            annual_rate=self.annual_rate,
        )
```

### Step 3 — Use the new type in a `SimulationScenario`

```python
from fitinera import SimulationScenario, Person, Age

scenario = SimulationScenario(
    initial_accounts=[
        SavingsAccount(id="High-Yield Savings", balance=20_000.0, annual_rate=0.04),
    ],
    initial_persons=[
        Person(id="Sam", age=Age(years=40), expectancy=Age(years=99)),
    ],
)
```

### Step 4 — Write a flow that uses the subtype

Flows that need the `annual_rate` field can narrow the type with `isinstance`:

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


class SavingsInterestFlow(Flow):
    """Credits monthly interest to every SavingsAccountState in the simulation.

    Iterates all live accounts and applies pro-rated monthly interest to any
    account that is an instance of ``SavingsAccountState``. Accounts of other
    types are silently skipped.
    """

    def executeFlow(
        self,
        view: SimulationStateView,
        updater: SimulationStateUpdater,
        logger: SimulationLogger,
    ) -> Optional[FitineraError]:
        """Credit monthly interest to all SavingsAccountState instances.

        Args:
            view: Read-only view of the current simulation state.
            updater: Write interface for emitting interest transactions.
            logger: Logging interface for audit messages.

        Returns:
            None — this flow never halts the simulation.
        """
        for account in view.get_accounts():
            if not isinstance(account, SavingsAccountState):
                continue
            monthly_rate = (1 + account.annual_rate) ** (1 / 12) - 1
            interest = account.balance * monthly_rate
            if interest <= 0:
                continue
            updater.emit_transaction(
                Income(
                    amount=interest,
                    to_account=account.id,
                    labels={"IncomeType": "INTEREST"},
                )
            )
            logger.info(
                f"SavingsInterestFlow: credited {interest:.2f} to '{account.id}'."
            )
        return None
```

______________________________________________________________________

## How `isinstance`-based flows interact with new subtypes automatically

Built-in flows such as `AssetSolvencyGuardFlow` dispatch using `isinstance` checks against `AssetAccountState`. The
important property is:

**Any new subclass of `AssetAccountState` is automatically included in `isinstance` checks against
`AssetAccountState`.**

For example, `SavingsAccountState` is a subclass of `AssetAccountState`, which is a subclass of `AccountState`.
`AssetSolvencyGuardFlow` iterates:

```python
for account in view.get_accounts():
    if isinstance(account, AssetAccountState) and account.balance < 0:
        return SolvencyViolationError(...)
```

will automatically guard `SavingsAccountState` instances — no change to the flow or the engine is required.

This means the extension contract is simply: **subclass the right base, implement the two factory methods, done**. Flows
written against `AssetAccountState` or `LiabilityAccountState` gain awareness of your new subtype for free.

______________________________________________________________________

## `BrokerageAccount` — the next planned extension (#29)

`BrokerageAccount(AssetAccount)` and `BrokerageAccountState(AssetAccountState)` are the next planned addition to the
hierarchy (tracked in issue #29). A brokerage account is an asset account that additionally carries portfolio metadata
such as an allocation mix or a target return rate.

The implementation pattern is identical to `SavingsAccount` above:

1. `BrokerageAccount(AssetAccount)` — frozen dataclass with extra fields (e.g. `equity_fraction: float`).
1. `BrokerageAccountState(AssetAccountState)` — mutable dataclass with the same extra fields.
1. `to_state()` / `to_snapshot()` overrides that preserve the extra fields in the round-trip.

No engine changes, no flow changes — the extension point is designed to absorb new subtypes without ripple effects.

______________________________________________________________________

## Checklist for a new account subtype

Before opening a PR with a new account subtype:

1. Does it subclass the correct base (`AssetAccount` for held value, `LiabilityAccount` for owed debt)?
1. Does the frozen `Account` subclass implement `to_state()` returning the corresponding `AccountState` subclass?
1. Does the mutable `AccountState` subclass implement `to_snapshot()` returning the corresponding `Account` subclass?
1. Does `to_state()` copy all extra fields into the new `AccountState`?
1. Does `to_snapshot()` copy all extra fields back into the new `Account`?
1. Are there tests for the `to_state()` → `to_snapshot()` round-trip (all fields preserved)?
1. Are there tests that confirm the new type is an instance of both its concrete class and the abstract base?
1. Are the new types exported from `fitinera/__init__.py` and listed in `__all__`?
