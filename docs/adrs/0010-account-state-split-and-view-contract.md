# ADR-0010: AccountState Split from Account and SimulationStateView Contract Extension

## Status

Accepted

## Context

The simulation engine needs to track mutable per-account balances across turns while flows execute within a turn. The
existing `Account` type is a frozen dataclass used both as a constructor argument in `SimulationScenario` and as an
immutable snapshot in each `Turn`. This design works well for historical records but cannot serve as live mutable state
for the engine loop.

Flows must observe the current (post-transaction) balance mid-turn so that ordering within the pipeline produces correct
results (ADR-0005). Requiring flows to reconstruct balance by replaying transactions would be complex and error-prone.
Conversely, making `Account` mutable would corrupt the frozen `Turn` snapshot and violate the audit trail guarantee
(ADR-0002).

Additionally, flows needed a way to query elapsed simulation time and current-turn transactions, neither of which was
available on `SimulationStateView`.

## Decision

We introduce `AccountState` as a separate, non-frozen (mutable) dataclass with fields `id: str`, `balance: float`, and
`labels: Dict[str, str]`. The engine maintains one `AccountState` per account as live state. `Account` remains frozen
and is used exclusively for `SimulationScenario` configuration and `Turn` snapshots.

`SimulationStateView.get_accounts()` return type is changed from `List[Account]` to `List[AccountState]` — flows always
see the live state, never a stale snapshot.

At turn-end, the engine produces a fresh frozen `Account(id=state.id, balance=state.balance)` for the `Turn` snapshot,
keeping the historical record immutable.

`SimulationStateView` is extended with four new methods: `get_start_date() -> Date`, `get_current_date() -> Date`,
`get_elapsed_duration() -> ElapsedDuration`, and `get_current_turn_transactions() -> List[Transaction]`. These allow
time-relative flows (e.g. inflation) and intra-turn-order-aware flows (e.g. rebalancing) to read the state they need
without reaching outside the protocol.

No `PersonState` type is introduced; the engine uses plain dicts for live person state and constructs fresh frozen
`Person` snapshots on each `get_person()` call via `dataclasses.replace()`.

## Consequences

**Positive:**

- Flows always see the latest balances within a turn, satisfying ADR-0005 (intra-turn causality).
- The `Turn` snapshot remains fully immutable, preserving the audit trail per ADR-0002.
- `AccountState` is a simple, predictable type that flows can reason about without replaying transactions.
- `ElapsedDuration` provides a reusable primitive for all time-sensitive flow calculations, avoiding repeated calendar
  arithmetic in individual flows.

**Negative / Tradeoffs:**

- Two account types (`Account` and `AccountState`) exist with overlapping fields; callers must understand which to use
  in which context.
- `SimulationStateView.get_accounts()` is a breaking change to the protocol contract — any existing implementor must
  update its return type.
- Flows that inadvertently hold a reference to an `AccountState` after the turn ends will observe stale state in
  subsequent turns if the engine does not replace the objects; the engine must reuse the same `AccountState` objects
  across turns (mutation in place) to avoid this.
