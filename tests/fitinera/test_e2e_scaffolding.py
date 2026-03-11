from fitinera.models import (
    SimulationScenario,
    Person,
    Age,
    AssetAccount,
    LiabilityAccount,
    Date,
    TurnDuration,
)
from fitinera.engine import SimulationEngine, EngineConfiguration
from fitinera.flows import (
    MetricGenerator,
    JobIncomeFlow,
    MortgagePaymentFlow,
    LivingExpenseFlow,
    PersonRetirementLabelFlow,
    MetricCondition,
    ComparisonOperator,
)


class NetWorthGenerator(MetricGenerator):
    def evaluate(self, view, logger):
        return sum(
            a.balance
            for a in view.get_accounts()
            if a.get_label("Type") in ("ASSET", "LIABILITY")
        )


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
            AssetAccount(
                id="Joint Checking",
                balance=10000,
                labels={"Type": "ASSET", "Liquidity": "LIQUID"},
            ),
            LiabilityAccount(
                id="Mortgage", balance=-300000, labels={"Type": "LIABILITY"}
            ),
        ],
    )

    pipeline = EngineConfiguration(
        start_date=Date(year=2026, month=2),
        max_turns=TurnDuration.of(years=60, months=8),
        metrics={"Net_Worth": NetWorthGenerator()},
        flows=[
            JobIncomeFlow(person_id="Sam", amount=3000, to_account="Joint Checking"),
            MortgagePaymentFlow(
                from_account="Joint Checking", to_account="Mortgage", amount=1500
            ),
            LivingExpenseFlow(from_account="Joint Checking", amount=2500),
            PersonRetirementLabelFlow(
                person_ids=["Sam", "Alex"],
                condition=MetricCondition(
                    "Net_Worth", ComparisonOperator.GE, 1_000_000
                ),
            ),
        ],
    )

    engine = SimulationEngine(configuration=pipeline)
    result = engine.run(scenario)
    assert result is not None
