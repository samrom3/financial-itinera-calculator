from collections import defaultdict
from dataclasses import replace

from .cashflows import IncomeKind
from .planning import FinancialScenario
from .results import (
    GrowthApplication,
    IncomeBreakdown,
    SimulationTurn,
)


class Turn:
    """Represents a single turn in a financial simulation."""

    def __init__(
        self,
        scenario: FinancialScenario,
        current_age,
        assets,
        incomes,
        expenses,
        tax_rates,
    ):
        self.scenario = scenario
        self.current_age = current_age
        self.assets = assets
        self.incomes = incomes
        self.expenses = expenses
        self.tax_rates = tax_rates

    def run(self) -> SimulationTurn:
        """
        Runs the logic for a single turn of the simulation.
        """
        # Store current state for the turn
        current_asset_breakdown = {
            asset.name: asset.initial_value for asset in self.assets
        }
        current_income_breakdown = IncomeBreakdown()
        for income in self.incomes:
            if income.time_bounds.is_active(self.current_age):
                if income.kind == IncomeKind.ACTIVE:
                    current_income_breakdown.active[income.name] = income.monthly_amount
                else:
                    current_income_breakdown.passive[income.name] = (
                        income.monthly_amount
                    )
        gross_income = current_income_breakdown.total

        # Apply Taxes
        tax_breakdown = defaultdict(float)
        net_income = gross_income
        active_tax_rate = None
        for tax_rate in self.tax_rates:
            if tax_rate.time_bounds.is_active(self.current_age):
                active_tax_rate = tax_rate
                tax_amount = gross_income * tax_rate.rate
                tax_breakdown[f"Income Tax ({tax_rate.rate:.2%})"] = tax_amount
                net_income -= tax_amount
                break  # Assume only one tax rate is active at a time

        # Aggregate Expenses
        expense_breakdown = defaultdict(float)
        for expense in self.expenses:
            if expense.time_bounds.is_active(self.current_age):
                expense_breakdown[expense.name] = expense.monthly_amount
        total_expenses = sum(expense_breakdown.values())

        # Calculate Net Cash Flow
        net_cash_flow = net_income - total_expenses

        # Apply Asset Flows
        total_contributions = 0
        withdrawal_breakdown = defaultdict(float)
        total_penalties = 0

        if net_cash_flow > 0:
            # Contribute to assets
            sorted_assets = sorted(
                self.assets, key=lambda a: a.contribution_priority, reverse=True
            )
            new_assets = {asset.name: asset for asset in self.assets}
            remaining_cash = net_cash_flow
            for asset in sorted_assets:
                if remaining_cash <= 0:
                    break
                contribution = min(
                    remaining_cash, asset.get_max_contribution(self.current_age)
                )
                new_assets[asset.name] = replace(
                    asset, initial_value=asset.initial_value + contribution
                )
                total_contributions += contribution
                remaining_cash -= contribution
            self.assets = list(new_assets.values())
        elif net_cash_flow < 0:
            # Withdraw from assets
            sorted_assets = sorted(
                self.assets, key=lambda a: a.withdrawal_priority, reverse=True
            )
            needed_cash = abs(net_cash_flow)
            new_assets = {asset.name: asset for asset in self.assets}
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
                penalty = new_asset.get_penalty(self.current_age)
                if penalty:
                    penalty_amount = withdrawal * penalty.rate
                    new_asset = replace(
                        new_asset,
                        initial_value=new_asset.initial_value - penalty_amount,
                    )
                    total_penalties += penalty_amount

                tax_rate = (
                    new_asset.get_override_tax_rate(self.current_age) or active_tax_rate
                )
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
            self.assets = list(new_assets.values())

        # Compound Values
        asset_growth_breakdown = []
        for i, asset in enumerate(self.assets):
            rate = asset.growth_strategy.get_monthly_growth_rate(self.current_age.month)
            growth = asset.initial_value * rate
            self.assets[i] = replace(asset, initial_value=asset.initial_value + growth)
            asset_growth_breakdown.append(
                GrowthApplication(
                    name=asset.name,
                    rate=rate,
                    amount=growth,
                )
            )

        income_growth_breakdown = []
        for i, income in enumerate(self.incomes):
            rate = income.growth_strategy.get_monthly_growth_rate(
                self.current_age.month
            )
            growth = income.monthly_amount * rate
            self.incomes[i] = replace(
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
        for i, expense in enumerate(self.expenses):
            rate = expense.growth_strategy.get_monthly_growth_rate(
                self.current_age.month
            )
            growth = expense.monthly_amount * rate
            self.expenses[i] = replace(
                expense, monthly_amount=expense.monthly_amount + growth
            )
            expense_growth_breakdown.append(
                GrowthApplication(
                    name=expense.name,
                    rate=rate,
                    amount=growth,
                )
            )

        # Check State and Record Turn
        next_asset_breakdown = {
            asset.name: asset.initial_value for asset in self.assets
        }
        next_income_breakdown = IncomeBreakdown()
        for income in self.incomes:
            if income.time_bounds.is_active(self.current_age.next_month()):
                if income.kind == IncomeKind.ACTIVE:
                    next_income_breakdown.active[income.name] = income.monthly_amount
                else:
                    next_income_breakdown.passive[income.name] = income.monthly_amount

        return SimulationTurn(
            current_age=self.current_age,
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
