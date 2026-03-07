> **[Guidance]** Brief description of the feature and the problem it solves. One paragraph max.

# Account Rollover

## 1. Introduction/Overview

> **[Guidance]** Describe the problem being solved and why it matters to the project. Keep it concise.

The fitinera pipeline currently lacks the ability to roll over balances between financial periods. When a period closes,
any remaining balance must carry forward to the next period's opening position. Without this, downstream flows produce
incorrect totals.

## 2. Goals

> **[Guidance]** Bullet-list what this feature accomplishes. Keep goals measurable.

- Enable period-close flows to emit a rollover transaction that seeds the subsequent period.
- Ensure rollover amounts are immutable once emitted (frozen dataclass).
- Provide a builder so callers can construct rollover parameters without long argument lists.

## 3. Developer Stories

> **[Guidance]** One story = one autonomous agent iteration. Each must fit in a single context window. Use the
> scaffold-first / implement-second pattern (see `/prd-tasks` for the authoritative definition) for any new or changed
> API surface. Story IDs follow format `FEAT-<slug>-NN` (two-digit zero-padded).

### FEAT-account-rollover-01: Scaffold RolloverParams and RolloverFlow API

**As a** developer, **I want** typed stubs for `RolloverParams` and `RolloverFlow` **so that** I can validate the API
surface and write tests before implementing real logic.

**Acceptance Criteria:**

- [ ] `RolloverParams` frozen dataclass exists in `src/fitinera/models/` with fields: `from_period_id`, `to_period_id`,
  `amount`, `account_id`
- [ ] `RolloverFlow` subclass exists in `src/fitinera/flows/` with `run()` stub raising `NotImplementedError`
- [ ] `RolloverParamsBuilder` exists and allows chained construction
- [ ] Tests exist in `tests/fitinera/` covering the expected API shape (tests will fail on `NotImplementedError`)
- [ ] Stub tests created for all new public API surfaces
- [ ] Pre-commit passes (`uv run pre-commit run`)
- [ ] Tests written in DAMP style with Google-style docstrings

### FEAT-account-rollover-02: Implement RolloverFlow logic

**As a** developer, **I want** `RolloverFlow.run()` to produce a rollover transaction **so that** the pipeline correctly
carries balances across periods.

**Acceptance Criteria:**

- [ ] `RolloverFlow.run()` emits a `Transaction` carrying the rollover amount from `from_period_id` to `to_period_id`
- [ ] All scaffold-story tests now pass
- [ ] Edge cases covered: zero-amount skip, negative balance guard
- [ ] Pre-commit passes (`uv run pre-commit run`)
- [ ] TDD cycle followed: test first → implement → refactor

## 4. Functional Requirements

> **[Guidance]** Number every requirement. Each must be concrete, testable, and unmistakably in or out of scope.

- FR-1: `RolloverParams` must be immutable (`frozen=True`).
- FR-2: `RolloverFlow.run()` must return a `Transaction` object, not a raw dict.
- FR-3: A zero-amount rollover must be skipped (no transaction emitted).
- FR-4: `RolloverParamsBuilder` must provide a fluent interface (method chaining).

## 5. Non-Goals (Out of Scope)

> **[Guidance]** Be explicit about what this feature does NOT do. Prevents scope creep.

- No UI or API endpoint changes.
- No multi-currency conversion (out of scope for V1).
- No database migrations (fitinera uses in-memory computation only).

## 6. Design Considerations

> **[Guidance]** Architecture notes, relevant ADRs, known constraints.

- The scaffold-first / implement-second pattern is required per `CONTRIBUTING.md`.
- An ADR should be written if the rollover emission model differs from existing flow patterns.
- See ADR index in `docs/adrs/README.md` for existing decisions that may constrain this design.

## 7. Technical Considerations

> **[Guidance]** Environment, language, tooling constraints.

- Python ≥ 3.13
- Immutable dataclasses (`frozen=True`) for all value objects
- Parameter encapsulation via Builder pattern (per `CONTRIBUTING.md`)
- `uv run pre-commit run` must pass (lint + format + test)
- `uv run pytest tests/fitinera/ -v` must pass

## 8. Success Metrics

> **[Guidance]** How do we know this feature is done and correct?

- All acceptance criteria checked off.
- `uv run pre-commit run` exits 0 on all new/modified files.
- `uv run pytest tests/fitinera/ -v` exits 0 with no skipped rollover tests.

## 9. Open Questions

> **[Guidance]** Unresolved items that need answers before or during implementation. Phase 2 and Phase 3 will resolve
> these.

- OQ-1: Should zero-amount rollovers log a warning or fail silently?
- OQ-2: Is there an existing `Period` model, or should `from_period_id`/`to_period_id` be plain strings for now?
