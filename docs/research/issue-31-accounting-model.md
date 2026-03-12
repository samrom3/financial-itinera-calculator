# Issue #31 Research: Liability Balance Convention & Accounting Model Design

**Date:** 2026-03-12 **Scope:** Evaluates whether the fix proposed in issue #31 goes far enough, surveys alternative
design patterns, and recommends a path forward for fitinera.

______________________________________________________________________

## Table of Contents

1. [Background](#1-background)
1. [What Issue #31 Proposes](#2-what-issue-31-proposes)
1. [Scope of the Proposed Fix](#3-scope-of-the-proposed-fix)
1. [Industry Standards and Accounting Theory](#4-industry-standards-and-accounting-theory)
1. [Alternative Design Patterns](#5-alternative-design-patterns)
1. [Pattern Comparison Matrix](#6-pattern-comparison-matrix)
1. [Recommendation](#7-recommendation)
1. [Architectural Observations on fitinera's Typed Hierarchy](#8-architectural-observations-on-fitineras-typed-hierarchy)
1. [Gaps in the Current Issue #31 Proposal](#9-gaps-in-the-current-issue-31-proposal)

______________________________________________________________________

## 1. Background

fitinera is a monthly personal financial simulation engine. Accounts are classified into two types (via a typed ABC
hierarchy introduced in PR #30 / ADR-0014):

- **`AssetAccount` / `AssetAccountState`** — bank accounts, investments, cash holdings. Stored with **positive
  balances**.
- **`LiabilityAccount` / `LiabilityAccountState`** — mortgages, loans, credit cards. Currently stored with **negative
  balances** (e.g., a $300,000 mortgage = `-300_000.0`).

Transactions are typed as `Income(to_account, amount)`, `Expense(from_account, amount)`, or
`Transfer(from_account, to_account, amount)`. The engine (`_SimulationStateUpdaterImpl.emit_transaction`) applies
balance changes uniformly — it does not distinguish asset from liability accounts when doing arithmetic.

The `NetWorthGenerator` currently works by summing all account balances:
`sum(account.balance for account in view.get_accounts())`. This works because assets are positive and liabilities are
negative — the sum is naturally `assets + (−liabilities) = net worth`.

______________________________________________________________________

## 2. What Issue #31 Proposes

Issue #31 proposes switching to the **positive debt convention** — storing liability balances as positive numbers
representing "the amount owed":

| Concept                            | Before #31                                     | After #31                                       |
| ---------------------------------- | ---------------------------------------------- | ----------------------------------------------- |
| $300k mortgage                     | `balance = -300_000.0`                         | `balance = 300_000.0`                           |
| Monthly payment effect on mortgage | `balance += 1_600` (toward zero from negative) | `balance -= 1_600` (toward zero from positive)  |
| Net worth formula                  | `sum(all balances)`                            | `sum(asset balances) - sum(liability balances)` |

The proposed change touches:

- `engine/state.py` — invert balance deltas for `LiabilityAccountState` in `emit_transaction`
- `flows/metrics.py` — update `NetWorthGenerator` to subtract liabilities
- All test fixtures that initialize liability balances
- README and guide documentation

______________________________________________________________________

## 3. Scope of the Proposed Fix

### What changes, file by file

| File                                                   | Change Required                                                                                                                                 | Risk                     |
| ------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------ |
| `src/fitinera/engine/state.py`                         | Add `isinstance(acct, LiabilityAccountState)` dispatch to invert balance deltas in `emit_transaction`                                           | High — core engine logic |
| `src/fitinera/flows/metrics.py`                        | `NetWorthGenerator`: replace `sum(all)` with `assets − liabilities` using isinstance dispatch                                                   | Medium                   |
| `src/fitinera/flows/debt.py`                           | **No code change** — `MortgagePaymentFlow` emits a type-agnostic `Transfer`; the engine's new dispatch handles the sign inversion automatically | None                     |
| `tests/fitinera/integration/test_scenario_mortgage.py` | Flip `_MORTGAGE_INITIAL = -300_000.0` → `300_000.0`; invert balance-trend assertions                                                            | Medium                   |
| `tests/fitinera/flows/test_standard_flows.py`          | ~5–8 liability-balance assertions                                                                                                               | Medium                   |
| `tests/fitinera/models/test_account.py`                | ~6–8 liability-balance fixture values                                                                                                           | Medium                   |
| `tests/fitinera/engine/test_engine_run.py`             | ~3–5 liability account setup lines                                                                                                              | Low–Medium               |
| `tests/fitinera/flows/test_task08_flows.py`            | 1–2 liability setup lines                                                                                                                       | Low                      |
| `tests/fitinera/test_e2e_scaffolding.py`               | Mortgage balance + `NetWorthGenerator` usage                                                                                                    | Low                      |
| `README.md`                                            | `LiabilityAccount(balance=-300000)` → positive; update `NetWorthGenerator` example                                                              | Low                      |
| `docs/guides/account-type-development-guide.md`        | Clarify "positive balance = debt owed" convention                                                                                               | Low                      |
| New `docs/adrs/0015-liability-sign-convention.md`      | Document the decision and rationale                                                                                                             | New                      |

**Effort estimate:** ~3–5 hours of mechanical changes plus testing. No architectural uncertainty.

### Is this the full scope?

The issue as written is complete for the minimum viable sign-flip. It does **not** address a few adjacent concerns
raised in this research, which are discussed in [Section 9](#9-gaps-in-the-current-issue-31-proposal).

______________________________________________________________________

## 4. Industry Standards and Accounting Theory

### Double-entry bookkeeping normal balances

Classical double-entry bookkeeping (codified since Luca Pacioli, 1494; the foundation of GAAP and IFRS) defines a
**normal balance** for each account type — the side of the ledger (debit or credit) that increases the account's value:

| Account Type   | Normal Balance        |
| -------------- | --------------------- |
| Asset          | Debit (positive)      |
| Liability      | **Credit (positive)** |
| Equity         | Credit (positive)     |
| Revenue/Income | Credit (positive)     |
| Expense        | Debit (positive)      |

In standard financial reporting (balance sheet, net worth statements), **all values are expressed as positive
magnitudes**. A $300,000 mortgage appears as `300,000` in the Liabilities column. Net worth is explicitly
`Assets − Liabilities`, both positive.

### What industry software does

Every major consumer and professional financial tool stores liabilities as positive values:

- **Quicken, YNAB, Mint / Intuit Credit Karma, Monarch Money** — all display mortgage/loan balances as positive debt
  figures; net worth is calculated as `Total Assets − Total Liabilities`.
- **QuickBooks, Xero, FreshBooks** — built on double-entry; liability accounts carry positive magnitudes; the balance
  sheet equation is `Assets = Liabilities + Equity` (all positive).
- **CFI/Wall Street Prep financial models** — explicitly note that the "negative liability" convention is a modeling
  shortcut for internal column-sum arithmetic, not the standard reporting convention.

### The notable exception: beancount and ledger-cli

The plain-text accounting ecosystem (beancount, hledger, ledger-cli) deliberately uses **negative balances for
liabilities and equity**, choosing mathematical consistency over user intuition:

- A $300,000 mortgage shows as `-300,000` in `Liabilities:Mortgage`.
- Net worth = `sum(all account balances)` = `assets + (−liabilities)`, giving zero when solvent — consistent with the
  accounting equation `Assets + Liabilities_signed + Equity_signed = 0`.
- beancount's own documentation explicitly acknowledges that this is **a known source of confusion** for users; the
  GnuCash wiki similarly notes the need to negate liability balances when displaying them.

These tools make this tradeoff because they are general-purpose **double-entry ledger engines** — mathematical
consistency across all five account types is paramount. fitinera is a **personal finance simulation tool**, where user
clarity and natural scenario-authoring should dominate.

### Conclusion from standards research

The positive-debt convention (issue #31's proposal) is aligned with GAAP, IFRS, and all user-facing financial software.
The negative-liability convention (current fitinera state) mirrors ledger-engine internals that are documented as
counterintuitive by their own maintainers. Issue #31 moves fitinera in the right direction.

______________________________________________________________________

## 5. Alternative Design Patterns

Three patterns were evaluated beyond the simple sign flip.

### Pattern A: Positive Liability Convention (Issue #31 — recommended baseline)

Store liability balances as positive numbers. Invert delta application in the engine for `LiabilityAccountState`. Update
`NetWorthGenerator` to subtract liabilities.

This is what issue #31 proposes. The section below discusses whether to implement the inversion in the engine or via a
method override on `AccountState`.

**New modules introduced:** 0 (one updated, one documented via ADR)

______________________________________________________________________

### Pattern B: Method Override Encapsulation (Enhancement to Pattern A)

Instead of putting the sign-inversion logic in `emit_transaction` via `isinstance` checks, push the arithmetic semantics
into the account types themselves via a virtual `apply_delta(delta: float)` method:

```python
# On AssetAccountState:
def apply_delta(self, delta: float) -> None:
    self.balance += delta


# On LiabilityAccountState:
def apply_delta(self, delta: float) -> None:
    self.balance -= (
        delta  # inverted: positive liability decreases when "receiving" value
    )
```

The engine's `emit_transaction` becomes type-agnostic:

```python
if isinstance(transaction, Transfer):
    src.apply_delta(-transaction.amount)  # source loses value
    dst.apply_delta(
        +transaction.amount
    )  # destination gains value (inverted for liability)
```

This is architecturally cleaner: the engine expresses **intent** (this account gains/loses value) and the account type
encapsulates **how that maps to a balance change**. Future account types (e.g., `EquityAccount`, `RevenueAccount`) can
define their own sign semantics without touching the engine.

**Advantages over naked isinstance in engine:**

- Engine remains fully type-agnostic — no account-type knowledge in `state.py`
- Each account type's arithmetic is testable in isolation
- Follows ADR-0014's intent: "put behavior in the type, not in the dispatcher"
- Future account subtypes (e.g., `PensionAccountState`) inherit or override without engine changes

**Disadvantages:**

- Adds a new abstract method to `AccountState` (nominal ceremony)
- Sign logic is distributed across two types rather than centralized in one engine method

**New modules introduced:** 0 (two methods added to existing account types)

______________________________________________________________________

### Pattern C: Per-Account Transaction Ledger (Independent enhancement)

Instead of a single mutable `balance: float`, each `AccountState` maintains an **append-only list of ledger entries**
(postings) alongside the running balance. The balance remains a float for O(1) flow reads; the ledger enables rich
time-series queries.

```python
@dataclass
class LedgerEntry:
    turn: int
    amount: float
    transaction_ref: Transaction


@dataclass
class AccountState(ABC):
    id: str
    balance: float
    labels: Dict[str, str]
    ledger: list[LedgerEntry] = field(default_factory=list)  # new
```

**What this unlocks for metric developers:**

| Current capability                              | With per-account ledger                           |
| ----------------------------------------------- | ------------------------------------------------- |
| `account.balance` — point-in-time               | `account.balance_at(turn=N)` — historical         |
| Turn-level transaction buffer (whole-turn only) | Per-account posting history                       |
| Net worth at current turn                       | Net worth time series over all turns              |
| No per-account income/expense breakdown         | `total_income_to(account_id, from_turn, to_turn)` |

**Fit for simulation:** Very high. A simulation library projecting 30 years of monthly data is exactly the use case for
time-series account history.

**Complexity:** Medium. The engine's `emit_transaction` appends to the ledger in addition to updating `balance`. Flows
see no API change (`.balance` still works). Metrics gain new capabilities.

**Memory:** Negligible. 360 turns × 10 accounts × 3 postings/turn × ~200 bytes/entry ≈ 2 MB.

**New modules introduced:** 0 (one new inner type `LedgerEntry` added to `models/account.py`, or extracted to a new
`models/ledger.py`)

**Important:** This pattern is **orthogonal to the sign convention question**. It can be done before, after, or
independently of issue #31.

______________________________________________________________________

### Pattern D: Full Double-Entry Journal Entries (Not recommended)

Replace `Income`/`Expense`/`Transfer` with explicit debit/credit `JournalEntry` + `Posting` types:

```python
@dataclass(frozen=True)
class Posting:
    account_id: str
    debit: float = 0.0
    credit: float = 0.0


@dataclass(frozen=True)
class JournalEntry:
    postings: tuple[Posting, ...]
    # invariant: sum(debits) == sum(credits)
```

A mortgage payment becomes:

```python
JournalEntry(
    postings=(
        Posting(account_id="mortgage", debit=1_500),  # reduces liability (debit side)
        Posting(account_id="checking", credit=1_500),  # reduces asset (credit side)
    )
)
```

**Fundamental advantage:** Eliminates sign ambiguity at the model level. The account type determines whether a debit
increases or decreases the balance; no special engine dispatch is needed for liabilities.

**Why this is not recommended for fitinera:**

1. **Audience mismatch.** Flow developers are not accountants. `Income(to_account="savings", amount=5000)` is instantly
   readable. Constructing a correct `JournalEntry` requires knowing which side of the ledger a debit vs credit falls on
   for each account type.
1. **Breaks the existing public API.** All existing flows, user-written flows, and tests would need to be migrated.
1. **No additional simulation value.** The `Income`/`Expense`/`Transfer` vocabulary maps cleanly to how users think
   about money flows. The DEB vocabulary adds precision useful for historical bookkeeping but not for forward-projecting
   scenarios.
1. **Can be layered on top later.** If fitinera ever adds an accounting/bookkeeping mode, journal entries could be
   generated from the existing transaction types as a reporting layer, not a replacement.

**New modules introduced:** 2 (`models/journal_entry.py`, `models/posting.py`) plus migration of all flows and tests.

______________________________________________________________________

## 6. Pattern Comparison Matrix

| Criterion                             | Pattern A: Sign Flip (Issue #31)              | Pattern B: Method Override (Enhancement)     | Pattern C: Per-Account Ledger            | Pattern D: Full DEB Journal Entries |
| ------------------------------------- | --------------------------------------------- | -------------------------------------------- | ---------------------------------------- | ----------------------------------- |
| **Fixes liability sign convention**   | Yes                                           | Yes                                          | No (orthogonal)                          | Yes                                 |
| **User understandability**            | High improvement                              | High improvement                             | No change                                | Regression (requires DEB knowledge) |
| **Flow developer API impact**         | None — flows unchanged                        | None — flows unchanged                       | None — `.balance` still works            | Breaking — all flows rewritten      |
| **Metric developer new capabilities** | Moderate — `assets − liabilities` is explicit | Same as A                                    | High — time-series per-account history   | Moderate — debit/credit totals      |
| **Engine complexity change**          | Low — add isinstance branch                   | Low — add abstract method + 2 overrides      | Medium — append ledger entries + balance | High — replace apply logic entirely |
| **New modules introduced**            | 0                                             | 0                                            | 0–1 (`LedgerEntry` may be its own model) | 2+ (plus migrations)                |
| **New test coverage needed**          | ~15–20 fixture updates + 1 engine unit test   | ~15–20 fixture updates + 2 method unit tests | Per-account ledger tests (new)           | Entire flow test suite migration    |
| **Reversibility**                     | Hard (sign inversion touches many fixtures)   | Hard                                         | Easy (additive change)                   | Very hard                           |
| **Recommended?**                      | Yes — minimum viable                          | Yes — preferred implementation path          | Yes — separate issue                     | No                                  |

______________________________________________________________________

## 7. Recommendation

### Does issue #31 go far enough?

**Yes, as a baseline — but two enhancements are worth considering.**

Issue #31 correctly identifies the sign convention problem, and its scope (engine, metrics, tests, docs) is accurate.
The fix is necessary and well-defined.

However, the research surfaced two decisions worth making explicitly:

#### Decision 1: Where to put the sign inversion logic

Issue #31 proposes putting `isinstance(acct, LiabilityAccountState)` checks directly in `emit_transaction` (Pattern A).
This works, but **Pattern B (method override)** is architecturally superior:

- The engine should express "this account gains value" / "this account loses value" — intent, not mechanism.
- The account type should encapsulate what "gaining value" means for its balance arithmetic.
- This is exactly the kind of polymorphism ADR-0014's typed hierarchy was designed to enable.

**Recommendation:** Implement the sign flip via an `apply_delta(delta: float)` abstract method on `AccountState`,
overridden in `AssetAccountState` (passthrough) and `LiabilityAccountState` (inverted). The engine calls
`acct.apply_delta(+amount)` or `acct.apply_delta(-amount)`. This is a small additional design step but produces a
cleaner result.

#### Decision 2: Per-account ledger as a follow-on issue

The per-account transaction ledger (Pattern C) is highly valuable for a simulation library and requires no sign
convention changes — it is orthogonal. It should be filed as a separate issue targeting a later milestone, not bundled
into #31. It would be fitinera's most impactful enhancement for metric developer experience.

### Proposed resolution path

| Step | Action                                                                     | Issue     |
| ---- | -------------------------------------------------------------------------- | --------- |
| 1    | Implement positive liability convention with `apply_delta` method override | #31       |
| 2    | Write ADR-0015 documenting the balance sign convention decision            | #31       |
| 3    | File new issue: per-account ledger for time-series metric queries          | New issue |

______________________________________________________________________

## 8. Architectural Observations on fitinera's Typed Hierarchy

ADR-0014 introduced `AssetAccount`/`LiabilityAccount` typed ABCs specifically to enable structural dispatch. The
liability sign convention is the first use case that exercises this fully. There are several architectural notes:

### The `apply_delta` pattern aligns with ADR-0014's design intent

ADR-0014 states: "Built-in flows that previously dispatched on a `get_label('Type')` equality check now use
`isinstance(account, AssetAccountState)` instead." The same principle applies here — but rather than `isinstance` checks
in the engine, the type hierarchy itself should carry the behavioral differentiation via method override.

### LiabilitySolvencyGuardFlow is a natural companion to this change

The existing `AssetSolvencyGuardFlow` (`flows/risk.py`) guards against asset balances going negative (i.e., spending
more than you have). After issue #31, liability balances become positive. An overpaid liability would go negative —
which would be worth detecting. A `LiabilitySolvencyGuardFlow` that flags `liability.balance < 0` (overpayment,
indicating a flow error or an overly generous debt payoff schedule) would be a natural companion to this change.

### Mortgage payment mechanics under apply_delta

A concrete mortgage payment illustrates how `apply_delta` dispatches correctly without any flow-level sign awareness.
Consider a $1,500/month mortgage payment split into $300 principal and $1,200 interest.

**How `apply_delta` is defined on each type:**

- `AssetAccountState.apply_delta(delta)` → `self.balance += delta`
- `LiabilityAccountState.apply_delta(delta)` → `self.balance -= delta` ← the inversion lives here

**Transaction 1 — Principal reduction:** `Transfer(from_account="checking", to_account="mortgage", amount=300)`

| Step                         | Call                         | Account type            | Effect                                         |
| ---------------------------- | ---------------------------- | ----------------------- | ---------------------------------------------- |
| Engine subtracts from source | `checking.apply_delta(-300)` | `AssetAccountState`     | `balance += -300` → checking shrinks by $300 ✓ |
| Engine adds to destination   | `mortgage.apply_delta(+300)` | `LiabilityAccountState` | `balance -= 300` → debt shrinks by $300 ✓      |

**Transaction 2 — Interest payment:** `Expense(from_account="checking", amount=1_200)`

Debt interest is an **expense against the financial system** — money flows from the checking account to the lender
(external). It does **not** touch the liability account, because paying interest does not reduce the outstanding
principal.

| Step                         | Call                           | Account type        | Effect                                                              |
| ---------------------------- | ------------------------------ | ------------------- | ------------------------------------------------------------------- |
| Engine subtracts from source | `checking.apply_delta(-1_200)` | `AssetAccountState` | `balance += -1_200` → checking shrinks by $1,200 ✓                  |
| Liability untouched          | —                              | —                   | Interest leaves the simulation (no in-system account receives it) ✓ |

**Net result:** Checking decreases by $1,500. Mortgage balance decreases by $300. Correct.

**Edge case — Accrued interest that grows the debt (negative amortization):** If a flow needed to add unpaid interest to
the outstanding principal (e.g., a deferred interest product), this would be modelled as
`Expense(from_account="mortgage", amount=monthly_interest)`:

| Step                         | Call                                      | Account type            | Effect                                                                              |
| ---------------------------- | ----------------------------------------- | ----------------------- | ----------------------------------------------------------------------------------- |
| Engine subtracts from source | `mortgage.apply_delta(-monthly_interest)` | `LiabilityAccountState` | `balance -= (-monthly_interest)` = `balance += monthly_interest` → debt **grows** ✓ |

This confirms the user's point: an `Expense` targeting a `LiabilityAccountState` correctly **increases** the liability
balance, because the engine sends a negative delta and `LiabilityAccountState` inverts it. The sign logic lives entirely
in `apply_delta` — the flow itself expresses intent (`Expense` = money leaves this account) with no awareness of the
account's type or sign convention.

### Validation opportunity: `LiabilityAccount.__post_init__`

Under the positive convention, the invariant "liability balances are non-negative" is a valid constraint. A
`__post_init__` validator on `LiabilityAccount` that raises `ValueError` for `balance < 0` would catch user
misconfiguration at scenario construction time — consistent with ADR-0014's philosophy of "hard errors early."

______________________________________________________________________

## 9. Gaps in the Current Issue #31 Proposal

The following items are not mentioned in issue #31 but are affected by or related to the sign flip:

### Gap 1: User-written condition checks on liability balances (medium risk)

If any user-written flow contains a `Condition` that compares a liability account balance to a threshold (e.g., "trigger
when mortgage balance drops below $50,000"), the semantics invert after #31:

- **Before**: threshold would be `< -50_000` (balance is negative, decreasing toward zero)
- **After**: threshold would be `< 50_000` (balance is positive, decreasing toward zero)

This is a **breaking change for user-written code** that relies on specific liability balance values. A migration note
in the changelog and README is needed.

### Gap 2: No validation that liability balances are non-negative (low risk)

There is currently no runtime check that `LiabilityAccount.balance >= 0`. A user who writes
`LiabilityAccount(id="mortgage", balance=-300_000)` after #31 would silently produce an asset-like account (negative
liability = adds to net worth instead of subtracting). A `__post_init__` validator in `LiabilityAccount` would catch
this at construction time.

### Gap 3: Potential `LiabilitySolvencyGuardFlow` gap (low risk)

After #31, a liability balance going negative (overpayment scenario) would be arithmetically valid but semantically
wrong. `AssetSolvencyGuardFlow` only guards assets. There is no built-in guard for this condition. Worth documenting as
a known limitation, with a recommendation to add `LiabilitySolvencyGuardFlow` as a follow-on.

### Gap 4: The `AssetSolvencyGuardFlow` name is now subtly misleading (cosmetic)

`AssetSolvencyGuardFlow` was renamed from `AccountSolvencyGuardFlow` in PR #30 to reflect that it only guards asset
accounts. This is correct. However, a user might reasonably ask "what guards my liability accounts?" — the answer is
"nothing, by design." This should be noted in the guide documentation.

### Gap 5: ADR-0003 claims a "double-entry transaction model" but fitinera's model is not true double-entry (documentation gap)

ADR-0003 is titled "Double-Entry Transaction Model" but the actual model is **single-entry-with-typed-flows**: `Income`,
`Expense`, and `Transfer` are single-journal-entry concepts, not double-entry journal entries. This is a documentation
imprecision (not a bug), but the ADR title may mislead contributors who know accounting. The ADR could be clarified to
say "typed single-entry transaction model inspired by double-entry principles."

______________________________________________________________________

## Research Methodology

This report synthesizes findings from three parallel research streams:

1. **Codebase analysis** — deep read of all affected source files, test suites, and documentation to characterize the
   full scope of issue #31 and identify gaps
1. **Accounting standards research** — GAAP, IFRS, classical double-entry theory, industry software conventions
   (Quicken, YNAB, QuickBooks, Xero)
1. **Software design pattern research** — beancount, hledger, ledger-cli, per-account ledger/event sourcing patterns,
   debit/credit journal entry models

Note: live web searches were unavailable in this environment. Industry and library references are based on established
knowledge of these systems.
