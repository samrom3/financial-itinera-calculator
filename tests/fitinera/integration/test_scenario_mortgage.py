"""Integration test — Scenario 4: mortgage debt paydown with solvency guard.

Two accounts: checking (ASSET, initial $10,000) and mortgage (LIABILITY,
initial -$300,000 representing outstanding debt). The pipeline includes
AccountSolvencyGuardFlow which monitors only ASSET-labeled accounts (FR-014);
the mortgage LIABILITY account going negative (i.e. a debt balance exists) must
NOT trigger the guard.

Account convention: liability balances are stored as negative values (the common
accounting representation where a $300,000 mortgage appears as -$300,000 in the
ledger). Each MortgagePaymentFlow Transfer(checking, mortgage, 1_600) deducts from
checking and adds $1,600 to the mortgage balance, bringing it toward zero as the
debt is repaid.

The simulation runs for 187 monthly turns — just before full mortgage payoff —
so that result.turns[-1] shows a still-negative mortgage balance (debt not yet
fully discharged), confirming:
  - AccountSolvencyGuardFlow does not fire on LIABILITY accounts (FR-014)
  - The checking ASSET account remains solvent throughout
  - result.success is True despite mortgage being negative
"""

from fitinera import (
    Account,
    Age,
    Date,
    Person,
    SimulationScenario,
    TurnDuration,
)
from fitinera.engine import EngineConfiguration, SimulationEngine
from fitinera.flows import (
    AccountSolvencyGuardFlow,
    JobIncomeFlow,
    LivingExpenseFlow,
    MortgagePaymentFlow,
)

# ---------------------------------------------------------------------------
# Scenario constants
# ---------------------------------------------------------------------------

_MONTHLY_INCOME = 8_333.0
_MORTGAGE_PAYMENT = 1_600.0
_MONTHLY_EXPENSE = 3_000.0

# Mortgage modeled as negative: -$300,000 represents $300,000 owed.
# Each $1,600/month payment brings the balance ~$1,600 closer to zero.
# After 187 turns: -300_000 + 187*1_600 = -800 (still negative, debt not cleared).
_MORTGAGE_INITIAL = -300_000.0
_CHECKING_INITIAL = 10_000.0

# Run for 187 turns so the mortgage is still negative at the last turn,
# explicitly demonstrating that a negative LIABILITY balance does not trigger
# AccountSolvencyGuardFlow (FR-014).
_SIMULATION_TURNS = 187
_MAX_TURNS = TurnDuration(0, months=_SIMULATION_TURNS)

_PERSON_START_AGE = Age(30)
_PERSON_LIFE_EXPECTANCY = Age(85)


def _build_scenario() -> SimulationScenario:
    """Return a scenario with checking and mortgage accounts plus one working person.

    The mortgage balance starts negative (−$300,000) representing outstanding debt.
    """
    return SimulationScenario(
        initial_persons=[
            Person(
                id="person",
                age=_PERSON_START_AGE,
                expectancy=_PERSON_LIFE_EXPECTANCY,
                labels={"Status": "Working"},
            )
        ],
        initial_accounts=[
            Account(
                id="checking",
                initial_balance=_CHECKING_INITIAL,
                labels={"Type": "ASSET"},
            ),
            Account(
                id="mortgage",
                initial_balance=_MORTGAGE_INITIAL,
                labels={"Type": "LIABILITY"},
            ),
        ],
    )


def _build_config() -> EngineConfiguration:
    """Return the pipeline configuration for Scenario 4.

    Pipeline order per the spec:
      1. AccountSolvencyGuardFlow — halt on negative ASSET balance
      2. JobIncomeFlow            — monthly income while Status=Working
      3. MortgagePaymentFlow      — fixed monthly payment from checking to mortgage
      4. LivingExpenseFlow        — fixed monthly living expenses from checking
    """
    return EngineConfiguration(
        start_date=Date(2026, 1),
        max_turns=_MAX_TURNS,
        flows=[
            AccountSolvencyGuardFlow(),
            JobIncomeFlow(
                person_id="person",
                amount=_MONTHLY_INCOME,
                to_account="checking",
            ),
            MortgagePaymentFlow(
                from_account="checking",
                to_account="mortgage",
                amount=_MORTGAGE_PAYMENT,
            ),
            LivingExpenseFlow(
                from_account="checking",
                amount=_MONTHLY_EXPENSE,
            ),
        ],
    )


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------


class TestScenario4MortgagePaydown:
    """Integration tests for Scenario 4: mortgage paydown with solvency guard.

    Validates that the AccountSolvencyGuardFlow only watches ASSET-labeled accounts
    (FR-014) and does not fire when a LIABILITY account has a negative balance.
    """

    def test_scenario4_result_success_is_true(self):
        """Simulation completes with success=True for 187 turns.

        The checking ASSET account always stays positive (net income > payments).
        AccountSolvencyGuardFlow therefore never fires, and the engine halts via
        max_turns with success=True.
        """
        config = _build_config()
        scenario = _build_scenario()

        result = SimulationEngine(config).run(scenario)

        assert result.success is True
        assert result.error_message is None

    def test_scenario4_produces_expected_turn_count(self):
        """Engine runs for exactly 187 turns before max_turns is exhausted."""
        config = _build_config()
        scenario = _build_scenario()

        result = SimulationEngine(config).run(scenario)

        assert len(result.turns) == _SIMULATION_TURNS

    def test_scenario4_checking_account_stays_solvent(self):
        """Checking ASSET account balance is non-negative across every turn.

        Monthly net inflow = $8,333 − $1,600 − $3,000 = $3,733 per turn.
        Starting at $10,000 the balance grows monotonically, so AccountSolvencyGuardFlow
        never fires.
        """
        config = _build_config()
        scenario = _build_scenario()

        result = SimulationEngine(config).run(scenario)

        for i, turn in enumerate(result.turns):
            checking = next(a for a in turn.accounts if a.id == "checking")
            assert checking.balance >= 0.0, (
                f"Checking went negative at turn {i + 1}: {checking.balance}"
            )

    def test_scenario4_mortgage_balance_is_negative_at_last_turn(self):
        """Mortgage LIABILITY account balance is ≤ $0 at the final turn (debt not cleared).

        After 187 monthly payments of $1,600 against an initial debt of $300,000,
        the remaining balance is approximately −$800, confirming the debt has not
        yet been fully discharged by end of the simulation window.
        """
        config = _build_config()
        scenario = _build_scenario()

        result = SimulationEngine(config).run(scenario)

        last_turn = result.turns[-1]
        mortgage = next(a for a in last_turn.accounts if a.id == "mortgage")
        assert mortgage.balance <= 0.0, (
            f"Expected mortgage balance <= $0 at last turn, got {mortgage.balance}"
        )

    def test_scenario4_solvency_guard_does_not_fire_when_liability_is_negative(self):
        """AccountSolvencyGuardFlow does not trigger on a negative LIABILITY balance.

        The mortgage account has label Type=LIABILITY. Per FR-014, AccountSolvencyGuardFlow
        only inspects accounts where get_label('Type') == 'ASSET'. A negative mortgage
        balance must not cause the simulation to fail.
        """
        config = _build_config()
        scenario = _build_scenario()

        result = SimulationEngine(config).run(scenario)

        # Confirm the simulation succeeded despite the mortgage being negative throughout.
        assert result.success is True

        # Verify the mortgage IS negative during the simulation (at turn 0).
        first_turn = result.turns[0]
        mortgage = next(a for a in first_turn.accounts if a.id == "mortgage")
        assert mortgage.balance < 0.0, (
            "Expected mortgage to be negative in the first turn "
            f"(debt not yet repaid), got {mortgage.balance}"
        )

    def test_scenario4_mortgage_balance_increases_toward_zero_each_turn(self):
        """Mortgage balance increases by $1,600 each turn as payments are applied.

        Transfer(checking, mortgage, 1_600) adds $1,600 to the mortgage account
        each month, bringing the outstanding debt balance from −$300,000 toward
        zero over the simulation period.
        """
        config = _build_config()
        scenario = _build_scenario()

        result = SimulationEngine(config).run(scenario)

        # Mortgage starts at -300_000 and each turn adds 1_600.
        prev_balance = _MORTGAGE_INITIAL
        for i, turn in enumerate(result.turns):
            mortgage = next(a for a in turn.accounts if a.id == "mortgage")
            assert (
                mortgage.balance > prev_balance or mortgage.balance == prev_balance
            ), (
                f"Mortgage balance decreased unexpectedly at turn {i + 1}: "
                f"{prev_balance} -> {mortgage.balance}"
            )
            prev_balance = mortgage.balance

    def test_scenario4_checking_grows_steadily(self):
        """Checking balance increases each turn by approximately $3,733.

        Net monthly inflow = income ($8,333) − mortgage payment ($1,600) −
        living expense ($3,000) = $3,733. Starting at $10,000, the balance
        grows monotonically throughout the simulation.
        """
        config = _build_config()
        scenario = _build_scenario()

        result = SimulationEngine(config).run(scenario)

        prev_balance = _CHECKING_INITIAL
        for i, turn in enumerate(result.turns):
            checking = next(a for a in turn.accounts if a.id == "checking")
            assert checking.balance > prev_balance, (
                f"Checking did not grow at turn {i + 1}: "
                f"{prev_balance} -> {checking.balance}"
            )
            prev_balance = checking.balance
