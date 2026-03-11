# ADR-0014: Typed Account Hierarchy with ABC Enforcement

## Status

Accepted

## Context

ADR-0010 introduced `Account` (frozen snapshot) and `AccountState` (mutable live state) as two parallel representations
of an account in the simulation. Both were plain dataclasses — any code could instantiate `Account(id=..., balance=...)`
directly, including in `SimulationScenario` fixtures and engine turn snapshots.

As downstream features require distinguishing asset accounts from liability accounts (e.g. solvency guard logic,
net-worth calculation, type-safe flow dispatch), the model needs concrete subtypes: `AssetAccount`, `LiabilityAccount`,
`AssetAccountState`, and `LiabilityAccountState`. Two options existed for enforcing that only typed subclasses are used:

**Option A — ABC enforcement**: Make `Account` and `AccountState` abstract base classes (ABCs) with abstract factory
methods (`to_state()` / `to_snapshot()`). Direct instantiation of the abstract types raises `TypeError` at construction
time.

**Option B — NotImplementedError guards**: Keep `Account` and `AccountState` as concrete dataclasses but add
`to_state()` / `to_snapshot()` methods that raise `NotImplementedError`. This permits `Account(...)` to be constructed
directly, deferring the error to method call time.

## Decision

We adopt Option A: `Account` and `AccountState` both inherit from `abc.ABC` and declare abstract methods.
`Account.to_state()` returns the matching `AccountState` subtype; `AccountState.to_snapshot()` returns the matching
`Account` subtype.

`AssetAccount` and `LiabilityAccount` are `frozen=True` dataclasses (immutable snapshots). `AssetAccountState` and
`LiabilityAccountState` are non-frozen dataclasses (mutable live state, consistent with ADR-0010).

Python 3.13's `dataclass(frozen=True)` composes cleanly with `ABC` — the metaclass conflict that existed in older Python
versions does not occur. Verification confirmed that attempting `Account(...)` raises `TypeError` with a clear message,
while `AssetAccount(...)` and `LiabilityAccount(...)` construct normally.

The engine is updated to use `acct.to_state()` when initialising live state and `state.to_snapshot()` when producing
turn snapshots, replacing the previous direct `AccountState(...)` and `Account(...)` constructions.

### Mirrored Account / AccountState design and the factory method pattern

The two hierarchies mirror each other exactly:

```
Account (ABC, frozen)               AccountState (ABC, mutable)
├── AssetAccount       ←→           ├── AssetAccountState
└── LiabilityAccount   ←→           └── LiabilityAccountState
```

Each concrete `Account` subclass implements `to_state()` returning its paired `AccountState` subclass. Each concrete
`AccountState` subclass implements `to_snapshot()` returning its paired `Account` subclass. This factory method pattern
is the sole coupling between the two hierarchies — it keeps the round-trip contract explicit and discoverable without
introducing cross-hierarchy field duplication.

### Why `Account` is abstract and `SimulationScenario` annotation is tightened

Making `Account` abstract enforces at construction time that every account entering a `SimulationScenario` carries an
explicit type classification. Without ABC enforcement, a scenario author could write `Account(id="Savings", balance=0)`
and the error would only surface later — potentially in a guard flow — rather than at the point of misconfiguration.

The `SimulationScenario.accounts` annotation accepts `list[Account]`, which in practice means
`list[AssetAccount | LiabilityAccount]` (or any future subclass). The abstract base provides the annotation target; the
ABC prevents un-typed instances from satisfying the contract in any real scenario.

### Relationship to ADR-0004

ADR-0004 introduced a label system (`Facet: Value`) for Accounts, Transactions, and Persons. The typed hierarchy does
**not** supersede or remove labels. Labels remain the appropriate mechanism for semantic annotations that are:

- Open-ended or user-defined (e.g. `Category: "HOUSING"`, `IncomeType: "ACTIVE"`)
- Not structurally significant to the engine or built-in flows (e.g. display tags, custom metadata)
- Applied to entities other than accounts (Transactions, Persons)

The typed hierarchy replaces only the use of labels for **structural discrimination** between account types (previously
the `Type: "ASSET"` / `Type: "LIABILITY"` pattern). Built-in flows that previously dispatched on
`account.get_label("Type") == "ASSET"` can now use `isinstance(account, AssetAccountState)` instead. User-defined flows
that already use labels for other purposes are unaffected.

### `BrokerageAccount` as the next planned extension (#29)

`BrokerageAccount(AssetAccount)` and `BrokerageAccountState(AssetAccountState)` are the natural next extension of this
hierarchy. A brokerage account is an asset account (positive-balance, owned by the simulation participant) that also
carries portfolio metadata — e.g. an allocation mix, a benchmark return rate, or a list of holdings.

Adding `BrokerageAccount` requires only:

1. Subclassing `AssetAccount` (frozen dataclass) with additional fields.
1. Subclassing `AssetAccountState` (non-frozen dataclass) with corresponding mutable fields.
1. Overriding `to_state()` / `to_snapshot()` to preserve the new fields in the round-trip.

No engine changes are required. Flows that dispatch on `isinstance(account, AssetAccountState)` will automatically
include `BrokerageAccountState` instances — demonstrating that the hierarchy extension point works as designed.

## Consequences

**Positive:**

- Plain `Account(...)` construction is now a hard error at import/construction time, not a silent bug discovered later.
  This prevents un-typed accounts from entering scenarios.
- The factory methods (`to_state`, `to_snapshot`) establish a clear, consistent round-trip contract between the frozen
  snapshot and mutable live state layers.
- Existing label-based dispatch (e.g. `get_label("Type") == "ASSET"`) is preserved for backward compatibility with flows
  that rely on labels, while the type hierarchy provides an alternative structural dispatch path via `isinstance`.
- Future account subtypes (e.g. `BrokerageAccount`, `PensionAccount`) integrate automatically with any flow that uses
  `isinstance(account, AssetAccountState)` — no flow changes required for new subtypes.

**Negative / Tradeoffs:**

- All existing test fixtures and engine code that used `Account(...)` or `AccountState(...)` directly required a
  mechanical migration to `AssetAccount(...)` / `LiabilityAccount(...)`. This was a broad but low-risk change.
- Future account types (e.g. `PensionAccount`) must subclass `Account` and `AccountState`; there is no escape hatch to
  add an un-typed account to a scenario.
- The two-class parallelism (`Account` ↔ `AccountState`, `AssetAccount` ↔ `AssetAccountState`, etc.) adds nominal naming
  overhead that contributors must understand.
