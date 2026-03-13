# ADR-0015: Liability Balance Sign Convention

## Status

Accepted

## Context

Fitinera's typed account hierarchy (ADR-0014) distinguishes `AssetAccount` from `LiabilityAccount` at the type level.
Prior to this decision, liability balances were stored as **negative numbers** — a $300,000 mortgage was represented as
`LiabilityAccount(id="Mortgage", balance=-300_000.0)`. Net worth was computed as a simple sum of all account balances,
relying on the negative sign to subtract liabilities automatically.

This convention originated from plain-text accounting tools (beancount, hledger, ledger-cli) that use signed balances
for mathematical consistency across five account types. However, fitinera is a **personal finance simulation tool**, not
a general-purpose ledger engine. The negative convention introduced several problems:

- **User confusion.** Scenario authors must remember that a larger debt is a more negative number. Writing
  `balance=-300_000.0` for "I owe $300,000" is unintuitive.
- **Threshold condition inversion.** A condition like "trigger when mortgage drops below $50,000" requires
  `balance > -50_000` (not `< 50_000`), which is error-prone.
- **Industry misalignment.** GAAP, IFRS, and all major consumer financial software (Quicken, YNAB, QuickBooks, Xero)
  store liabilities as positive magnitudes. Net worth is explicitly `Assets − Liabilities`, both positive.

Research documented in [`docs/research/issue-31-accounting-model.md`](../research/issue-31-accounting-model.md)
evaluated four alternative patterns (sign flip, method override, per-account ledger, full double-entry journal entries)
and concluded that positive liability balances with method-override encapsulation (Pattern B) is the preferred path.

## Decision

We adopt the **positive liability balance convention**: liability balances are stored as positive numbers representing
the amount owed. A $300,000 mortgage is `LiabilityAccount(id="Mortgage", balance=300_000.0)`.

### `apply_delta` method override

Rather than adding `isinstance` checks in the engine's `emit_transaction`, the sign-inversion logic is encapsulated in
the account type hierarchy via an `apply_delta(delta: float)` abstract method on `AccountState`:

- `AssetAccountState.apply_delta(delta)` → `self.balance += delta` (passthrough)
- `LiabilityAccountState.apply_delta(delta)` → `self.balance -= delta` (inverted)

The engine calls `acct.apply_delta(+amount)` or `acct.apply_delta(-amount)` to express intent ("this account gains/loses
value") without knowing the account type. This is the first behavioral override enabled by ADR-0014's typed hierarchy,
validating its design intent of "put behavior in the type, not in the dispatcher."

### `LiabilityAccount` validator

A `__post_init__` validator on `LiabilityAccount` raises `ValueError` for `balance < 0`. This catches misconfiguration
at scenario construction time — consistent with ADR-0014's philosophy of "hard errors early."

### `NetWorthGenerator` update

`NetWorthGenerator.evaluate` is updated from `sum(all balances)` to `sum(asset balances) - sum(liability balances)`
using `isinstance` dispatch against `AssetAccountState` and `LiabilityAccountState`.

### Relationship to other ADRs

- **ADR-0014** (Typed Account Hierarchy): `apply_delta` is the first behavioral override enabled by the hierarchy.
- **ADR-0003** (Transaction Model): the `Income`/`Expense`/`Transfer` transaction types remain unchanged; flows express
  intent and the account type handles sign semantics.

## Consequences

**Positive:**

- Scenario authors write `LiabilityAccount(balance=300_000.0)` — intuitive and aligned with how users think about debt.
- Threshold conditions read naturally: "mortgage below $50,000" is `balance < 50_000`.
- Aligned with GAAP, IFRS, and all major consumer financial software.
- The engine is fully type-agnostic — `apply_delta` encapsulates sign semantics, so future account types (e.g.
  `EquityAccount`) can define their own balance arithmetic without engine changes.
- The `__post_init__` validator prevents silent misconfiguration (negative liability = accidentally adds to net worth).

**Negative / Tradeoffs:**

- **Breaking change for user-written flows.** Any user code that checks liability balance thresholds must be updated:
  conditions like `acct.balance < -50_000` (checking a negative balance) become `acct.balance < 50_000` (checking a
  positive balance). Similarly, `acct.balance > 0` no longer means "liability is overpaid" — it now means "debt exists."
- All test fixtures with liability balances required a mechanical sign flip — broad but low-risk.
- The `__post_init__` validator means `LiabilityAccountState.to_snapshot()` will raise `ValueError` if a liability
  balance goes negative during simulation (e.g. an overpaid mortgage). Flows must ensure liability balances do not cross
  zero, or handle the edge case explicitly.
