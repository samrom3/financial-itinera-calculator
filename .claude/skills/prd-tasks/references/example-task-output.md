# Example TaskCreate Output

**Task 1:**

- **Subject:** `FEAT-account-rollover-01: Scaffold RolloverParams and RolloverFlow API`
- **Description:**
  ```
  As a developer, I want typed stubs for RolloverParams and RolloverFlow so that I can validate the
  API surface and write tests before implementing real logic.

  Acceptance Criteria:
  - RolloverParams frozen dataclass in src/fitinera/models/ with fields: from_period_id, to_period_id, amount, account_id
  - RolloverFlow subclass in src/fitinera/flows/ with run() stub raising NotImplementedError
  - Tests exist covering the expected API shape (will fail on NotImplementedError)
  - Pre-commit passes (uv run pre-commit run)
  - Tests written in DAMP style with Google-style docstrings
  - TDD cycle followed: test first → implement → refactor
  ```

**Task 2:**

- **Subject:** `FEAT-account-rollover-02: Implement RolloverFlow logic`
- **Description:**
  ```
  As a developer, I want RolloverFlow.run() to produce a rollover transaction so that the pipeline
  correctly carries balances across periods.

  Acceptance Criteria:
  - RolloverFlow.run() emits a Transaction carrying the rollover amount
  - All scaffold-story tests now pass
  - Zero-amount rollover is skipped (FR-3)
  - Pre-commit passes (uv run pre-commit run)
  - Tests written in DAMP style with Google-style docstrings
  - TDD cycle followed: test first → implement → refactor
  ```
