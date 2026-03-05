# ADR-0009: Domain-Grouped Standard Flow Modules

## Status

Accepted

## Context

The `fitinera_v1` library ships a set of common, reusable `Flow` and `MetricGenerator` implementations (e.g. income
injection, mortgage payment, living expenses, retirement detection, net-worth calculation). These are first-class
library components — not illustrative snippets — and are intended to be imported and used directly in user pipelines.

The initial scaffolding placed all of these in a single file named `examples.py`. This name was misleading: it implied
the code was illustrative or disposable, when it is in fact part of the library's public API. It also placed
`MetricGenerator` subclasses alongside `Flow` subclasses with no domain separation, and it did not establish a scalable
pattern for adding future components (e.g. tax flows, rental income, investment rebalancing).

## Decision

Replace `flows/examples.py` with a set of domain-grouped modules, each covering one financial concern:

| Module               | Domain                       | Contents              |
| -------------------- | ---------------------------- | --------------------- |
| `flows/income.py`    | Employment & revenue         | `JobIncomeFlow`       |
| `flows/debt.py`      | Debt servicing               | `MortgagePaymentFlow` |
| `flows/spending.py`  | Recurring expenditure        | `LivingExpenseFlow`   |
| `flows/lifecycle.py` | Life-event state transitions | `RetirementCheckFlow` |
| `flows/metrics.py`   | Metric observers             | `NetWorthGenerator`   |

`flows/interfaces.py` continues to hold the abstract `Flow` and `MetricGenerator` protocols, unchanged.

`flows/__init__.py` re-exports everything so the public import path (`from fitinera_v1 import JobIncomeFlow`) is fully
backward-compatible.

New standard flows are added to the module that matches their financial domain. If no existing module fits, a new domain
module is created rather than appending to an unrelated one.

## Consequences

**Positive:**

- File names reflect financial intent, not code role. A contributor looking for mortgage logic goes to `debt.py`; one
  adding rental income goes to `income.py`.
- `MetricGenerator` subclasses (`metrics.py`) are cleanly separated from `Flow` subclasses, matching the conceptual
  split in the engine architecture.
- The pattern scales: each domain module grows independently without creating an ever-longer "grab-bag" file.
- New contributors have clear guidance on where to place a new built-in flow.

**Negative / Tradeoffs:**

- More files than a single flat file, which can feel like premature structure when the domain modules each contain only
  one or two classes. This is an accepted tradeoff given the library's stated roadmap (tax, rental income, investment
  modeling, etc.).
