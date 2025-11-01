import copy
from collections import defaultdict
from dataclasses import replace

from .assets import Asset
from .cashflows import Expense, Income, IncomeKind, TaxRate
from .planning import FinancialScenario
from .results import (
    GrowthApplication,
    IncomeBreakdown,
    SimulationResult,
    SimulationStatus,
    SimulationTurn,
)


class Simulator:
    """Runs a financial simulation based on a given scenario."""

    def run(self, scenario: FinancialScenario) -> SimulationResult:
        """
        Runs the simulation and returns the results.

        :param scenario: The financial scenario to simulate.
        :return: A SimulationResult object containing the outcome of the simulation.
        """
        history = []
        assets = copy.deepcopy(scenario.assets)
        incomes = copy.deepcopy(scenario.incomes)
        expenses = copy.deepcopy(scenario.expenses)
        tax_rates = scenario.tax_rates[:]
        current_age = scenario.time_horizon.current_age

        while current_age < scenario.time_horizon.life_expectancy:
            # 1. Check Retirement Status
            is_retired = current_age >= scenario.retirement_goal.retirement_age

            # 2. Store current state for the turn
            current_asset_breakdown = {asset.name: asset.initial_value for asset in assets}
            current_income_breakdown = IncomeBreakdown()
            for income in incomes:
                if income.time_bounds.is_active(current_age):
                    if income.kind == IncomeKind.ACTIVE:
                        current_income_breakdown.active[
                            income.name
                        ] = income.monthly_amount
                    else:
                        current_income_breakdown.passive[
                            income.name
                        ] = income.monthly_amount
            gross_income = current_income_breakdown.total

            # 3. Apply Taxes
            tax_breakdown = defaultdict(float)
            net_income = gross_income
            active_tax_rate = None
            for tax_rate in tax_rates:
                if tax_rate.time_bounds.is_active(current_age):
                    active_tax_rate = tax_rate
                    tax_amount = gross_income * tax_rate.rate
                    tax_breakdown[f"Income Tax ({tax_rate.rate:.2%})"] = tax_amount
                    net_income -= tax_amount
                    break  # Assume only one tax rate is active at a time

            # 4. Aggregate Expenses
            expense_breakdown = defaultdict(float)
            for expense in expenses:
                if expense.time_bounds.is_active(current_age):
                    expense_breakdown[expense.name] = expense.monthly_amount
            total_expenses = sum(expense_breakdown.values())

            # 5. Calculate Net Cash Flow
            net_cash_flow = net_income - total_expenses

            # 6. Apply Asset Flows
            total_contributions = 0
            withdrawal_breakdown = defaultdict(float)
            total_penalties = 0

            if net_cash_flow > 0:
                # Contribute to assets
                sorted_assets = sorted(
                    assets, key=lambda a: a.contribution_priority, reverse=True
                )
                new_assets = {asset.name: asset for asset in assets}
                remaining_cash = net_cash_flow
                for asset in sorted_assets:
                    if remaining_cash <= 0:
                        break
                    contribution = min(
                        remaining_cash, asset.get_max_contribution(current_age)
                    )
                    new_assets[asset.name] = replace(
                        asset, initial_value=asset.initial_value + contribution
                    )
                    total_contributions += contribution
                    remaining_cash -= contribution
                assets = list(new_assets.values())
            elif net_cash_flow < 0:
                # Withdraw from assets
                sorted_assets = sorted(
                    assets, key=lambda a: a.withdrawal_priority, reverse=True
                )
                needed_cash = abs(net_cash_flow)
                new_assets = {asset.name: asset for asset in assets}
                for asset in sorted_assets:
                    if needed_cash <= 0:
                        break
                    withdrawal = min(needed_cash, asset.initial_value)
                    new_asset = replace(
                        asset, initial_value=asset.initial_value - withdrawal
                    )
                    withdrawal_breakdown[asset.name] += withdrawal
                    needed_cash -= withdrawal

                    # Apply penalties and taxes on withdrawal
                    penalty = new_asset.get_penalty(current_age)
                    if penalty:
                        penalty_amount = withdrawal * penalty.rate
                        new_asset = replace(
                            new_asset,
                            initial_value=new_asset.initial_value - penalty_amount,
                        )
                        total_penalties += penalty_amount

                    tax_rate = new_asset.get_override_tax_rate(
                        current_age
                    ) or active_tax_rate
                    if tax_rate:
                        tax_amount = withdrawal * tax_rate.rate
                        new_asset = replace(
                            new_asset,
                            initial_value=new_asset.initial_value - tax_amount,
                        )
                        tax_breakdown[
                            f"Withdrawal Tax ({tax_rate.rate:.2%}) on {asset.name}"
                        ] += tax_amount
                    new_assets[asset.name] = new_asset
                assets = list(new_assets.values())

            # 7. Compound Values
            asset_growth_breakdown = []
            for i, asset in enumerate(assets):
                rate = asset.growth_strategy.get_monthly_growth_rate(current_age.month)
                growth = asset.initial_value * rate
                assets[i] = replace(asset, initial_value=asset.initial_value + growth)
                asset_growth_breakdown.append(
                    GrowthApplication(
                        name=asset.name,
                        rate=rate,
                        amount=growth,
                    )
                )

            income_growth_breakdown = []
            for i, income in enumerate(incomes):
                rate = income.growth_strategy.get_monthly_growth_rate(current_age.month)
                growth = income.monthly_amount * rate
                incomes[i] = replace(
                    income, monthly_amount=income.monthly_amount + growth
                )
                income_growth_breakdown.append(
                    GrowthApplication(
                        name=income.name,
                        rate=rate,
                        amount=growth,
                    )
                )

            expense_growth_breakdown = []
            for i, expense in enumerate(expenses):
                rate = expense.growth_strategy.get_monthly_growth_rate(
                    current_age.month
                )
                growth = expense.monthly_amount * rate
                expenses[i] = replace(
                    expense, monthly_amount=expense.monthly_amount + growth
                )
                expense_growth_breakdown.append(
                    GrowthApplication(
                        name=expense.name,
                        rate=rate,
                        amount=growth,
                    )
                )

            # 8. Check State and Record Turn
            next_asset_breakdown = {asset.name: asset.initial_value for asset in assets}
            next_income_breakdown = IncomeBreakdown()
            for income in incomes:
                if income.time_bounds.is_active(current_age.next_month()):
                    if income.kind == IncomeKind.ACTIVE:
                        next_income_breakdown.active[
                            income.name
                        ] = income.monthly_amount
                    else:
                        next_income_breakdown.passive[
                            income.name
                        ] = income.monthly_amount

            if sum(next_asset_breakdown.values()) <= 0:
                status = (
                    SimulationStatus.PRE_RETIREMENT_BANKRUPTCY
                    if not is_retired
                    else SimulationStatus.POST_RETIREMENT_BANKRUPTCY
                )
                return SimulationResult(status=status, history=history, scenario=scenario)

            turn = SimulationTurn(
                current_age=current_age,
                current_asset_breakdown=current_asset_breakdown,
                next_asset_breakdown=next_asset_breakdown,
                current_income_breakdown=current_income_breakdown,
                next_income_breakdown=next_income_breakdown,
                expense_breakdown=expense_breakdown,
                tax_breakdown=tax_breakdown,
                asset_growth_breakdown=asset_growth_breakdown,
                income_growth_breakdown=income_growth_breakdown,
                expense_growth_breakdown=expense_growth_breakdown,
                net_cash_flow=net_cash_flow,
                total_contributions=total_contributions,
                withdrawal_breakdown=withdrawal_breakdown,
                total_penalties=total_penalties,
            )
            history.append(turn)
            current_age = current_age.next_month()

        # Final check for estate goal
        final_assets = sum(a.initial_value for a in assets)
        if final_assets < scenario.retirement_goal.desired_estate_value:
            status = SimulationStatus.INSUFFICIENT_ESTATE
        else:
            status = SimulationStatus.SUCCESS

        return SimulationResult(status=status, history=history, scenario=scenario)
