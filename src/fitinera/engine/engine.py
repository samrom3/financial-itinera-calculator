from typing import Dict, List

from ..models import (
    Account,
    AccountState,
    Date,
    Metric,
    SimulationScenario,
    Transaction,
)
from ..models.person import Person
from ..models.scenario import Turn
from .configuration import EngineConfiguration
from .result import SimulationResult
from .state import (
    _LivePersonState,
    _SimulationLoggerImpl,
    _SimulationStateUpdaterImpl,
    _SimulationStateViewImpl,
)


def _increment_date(date: Date) -> Date:
    """Return a new Date one calendar month ahead.

    December (month 12) rolls forward to January of the following year.
    """
    if date.month == 12:
        return Date(year=date.year + 1, month=1)
    return Date(year=date.year, month=date.month + 1)


class SimulationEngine:
    """The main controller for running a financial simulation pipeline."""

    def __init__(self, configuration: EngineConfiguration):
        self.configuration = configuration

    def run(self, scenario: SimulationScenario) -> SimulationResult:
        """Execute the simulation and return an immutable SimulationResult.

        Initialises live state from the scenario, then executes turns until
        one of the halt conditions is triggered (FR-023):
          1. A flow emits a logger error -> success=False.
          2. All persons are no longer living -> success=True.
          3. max_turns months have been completed -> success=True.

        Within each turn the engine:
          1. Increments the current Date by one calendar month.
          2. Increments all persons' Age by one month.
          3. Runs all Flows in configuration order.
          4. Checks for logger error (halts without snapshot if set).
          5. Evaluates all MetricGenerators.
          6. Snapshots the turn as a frozen Turn.
          7. Clears the transaction buffer.
          8. Checks remaining halt conditions.
        """
        cfg = self.configuration

        # --- Initialise live account state ---
        account_states: List[AccountState] = [
            AccountState(id=acct.id, balance=acct.balance, labels=dict(acct.labels))
            for acct in scenario.initial_accounts
        ]

        # --- Initialise live person state ---
        person_states: Dict[str, _LivePersonState] = {
            p.id: _LivePersonState(p) for p in scenario.initial_persons
        }

        # --- Mutable references shared with view impl ---
        current_date_ref: List[Date] = [cfg.start_date]
        turns_completed_ref: List[int] = [0]
        tx_buffer: List[Transaction] = []

        # --- Logger ref: placeholder replaced at start of each turn ---
        logger_ref: List[_SimulationLoggerImpl] = [_SimulationLoggerImpl()]

        # --- Build the view/updater; logger is recreated per turn ---
        view = _SimulationStateViewImpl(
            account_states=account_states,
            person_states=person_states,
            metric_generators=cfg.metrics,
            start_date=cfg.start_date,
            current_date_ref=current_date_ref,
            turns_completed_ref=turns_completed_ref,
            tx_buffer=tx_buffer,
            logger_ref=logger_ref,
        )
        updater = _SimulationStateUpdaterImpl(
            account_states=account_states,
            person_states=person_states,
            tx_buffer=tx_buffer,
        )

        max_months = cfg.max_turns.months
        history: List[Turn] = []
        all_log_messages: List[str] = []

        while turns_completed_ref[0] < max_months:
            logger = _SimulationLoggerImpl()
            logger_ref[0] = logger

            # Step 1: Increment date by one calendar month.
            current_date_ref[0] = _increment_date(current_date_ref[0])

            # Step 2: Increment all persons' age by one month.
            for state in person_states.values():
                state.increment_age()

            # Steps 3+4: Run flows; halt immediately after the offending flow if an error is logged.
            for flow in cfg.flows:
                flow.executeFlow(view, updater, logger)
                if logger.has_error:
                    all_log_messages.extend(logger.messages)
                    return SimulationResult(
                        turns=history,
                        success=False,
                        error_message=logger.error_message,
                        log_messages=all_log_messages,
                    )

            # Step 5: Evaluate all MetricGenerators.
            metrics: List[Metric] = [
                Metric(name=name, value=gen.evaluate(view, logger))
                for name, gen in cfg.metrics.items()
            ]

            # Step 6: Snapshot the turn — accounts and persons reflect post-flow state.
            snapshot_accounts = [
                Account(id=s.id, balance=s.balance, labels=dict(s.labels))
                for s in account_states
            ]
            snapshot_persons = [
                Person(
                    id=s.person.id,
                    age=s.age,
                    expectancy=s.person.expectancy,
                    labels=dict(s.labels),
                )
                for s in person_states.values()
            ]

            turn = Turn(
                date=current_date_ref[0],
                accounts=snapshot_accounts,
                persons=snapshot_persons,
                transactions=list(tx_buffer),
                metrics=metrics,
            )
            history.append(turn)

            # Accumulate log messages from this turn.
            all_log_messages.extend(logger.messages)

            # Step 7: Clear transaction buffer.
            tx_buffer.clear()

            # Step 8: Advance turns_completed counter.
            turns_completed_ref[0] += 1

            # Step 8a: Check all-persons-deceased halt condition.
            if person_states and all(not s.is_living() for s in person_states.values()):
                return SimulationResult(
                    turns=history, success=True, log_messages=all_log_messages
                )

        # Step 8b: max_turns exhausted.
        return SimulationResult(
            turns=history, success=True, log_messages=all_log_messages
        )
