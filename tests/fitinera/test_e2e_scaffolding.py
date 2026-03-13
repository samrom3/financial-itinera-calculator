from fitinera.models import (
    AssetAccountState,
    LiabilityAccountState,
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
    SimpleMortgagePaymentFlow,
    LivingExpenseFlow,
    PersonRetirementLabelFlow,
    MetricCondition,
    ComparisonOperator,
)


class NetWorthGenerator(MetricGenerator):
    def evaluate(self, view, logger):
        accounts = view.get_accounts()
        assets = sum(a.balance for a in accounts if isinstance(a, AssetAccountState))
        liabilities = sum(
            a.balance for a in accounts if isinstance(a, LiabilityAccountState)
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
            AssetAccount(
                id="Joint Checking",
                balance=10000,
                labels={"Liquidity": "LIQUID"},
            ),
            LiabilityAccount(id="Mortgage", balance=1_200_000),
        ],
    )

    pipeline = EngineConfiguration(
        start_date=Date(year=2026, month=2),
        max_turns=TurnDuration.of(years=60, months=8),
        metrics={"Net_Worth": NetWorthGenerator()},
        flows=[
            JobIncomeFlow(person_id="Sam", amount=3000, to_account="Joint Checking"),
            SimpleMortgagePaymentFlow(
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
