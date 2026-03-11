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

## Consequences

**Positive:**

- Plain `Account(...)` construction is now a hard error at import/construction time, not a silent bug discovered later.
  This prevents un-typed accounts from entering scenarios.
- The factory methods (`to_state`, `to_snapshot`) establish a clear, consistent round-trip contract between the frozen
  snapshot and mutable live state layers.
- Existing label-based dispatch (e.g. `get_label("Type") == "ASSET"`) is preserved for backward compatibility with flows
  that rely on labels, while the type hierarchy provides an alternative structural dispatch path.

**Negative / Tradeoffs:**

- All existing test fixtures and engine code that used `Account(...)` or `AccountState(...)` directly required a
  mechanical migration to `AssetAccount(...)` / `LiabilityAccount(...)`. This was a broad but low-risk change.
- Future account types (e.g. `PensionAccount`) must subclass `Account` and `AccountState`; there is no escape hatch to
  add an un-typed account to a scenario.
- The two-class parallelism (`Account` ↔ `AccountState`, `AssetAccount` ↔ `AssetAccountState`, etc.) adds nominal naming
  overhead that contributors must understand.
