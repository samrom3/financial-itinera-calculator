import pytest
from fitinera.models import (
    SimulationScenario,
    Person,
    Age,
    Account,
    Date,
    TurnDuration,
)
from fitinera.engine import SimulationEngine, EngineConfiguration
from fitinera.flows import (
    MetricGenerator,
    JobIncomeFlow,
    MortgagePaymentFlow,
    LivingExpenseFlow,
    RetirementCheckFlow,
)


class NetWorthGenerator(MetricGenerator):
    def evaluate(self, view):
        assets = sum(
            a.balance for a in view.get_accounts() if a.get_label("Type") == "ASSET"
        )
        liabilities = sum(
            a.balance for a in view.get_accounts() if a.get_label("Type") == "LIABILITY"
        )
        return assets - liabilities


def test_e2e_scaffolding_runs_without_import_or_type_errors():
    scenario = SimulationScenario(
        initial_persons=[
            Person(
                id="Sam",
                age=Age(years=34, months=2),
                expectancy=Age(years=99),
                labels={"Status": "Working"},
            ),
            Person(
                id="Alex",
                age=Age(years=33, months=8),
                expectancy=Age(years=99),
                labels={"Status": "Working"},
            ),
        ],
        initial_accounts=[
            Account(
                id="Joint Checking",
                initial_balance=10000,
                labels={"Type": "ASSET", "Liquidity": "LIQUID"},
            ),
            Account(
                id="Mortgage", initial_balance=300000, labels={"Type": "LIABILITY"}
            ),
        ],
    )

    pipeline = EngineConfiguration(
        start_date=Date(year=2026, month=2),
        max_turns=TurnDuration(years=60, months=8),
        metrics={"Net_Worth": NetWorthGenerator()},
        flows=[
            JobIncomeFlow(person_id="Sam", amount=3000, to_account="Joint Checking"),
            MortgagePaymentFlow(
                from_account="Joint Checking", to_account="Mortgage", amount=1500
            ),
            LivingExpenseFlow(from_account="Joint Checking", amount=2500),
            RetirementCheckFlow(
                person_ids=["Sam", "Alex"], metric_name="Net_Worth", threshold=1000000
            ),
        ],
    )

    engine = SimulationEngine(configuration=pipeline)
    with pytest.raises(NotImplementedError):
        engine.run(scenario)
