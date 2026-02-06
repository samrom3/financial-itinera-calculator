import copy
from collections import defaultdict
from dataclasses import dataclass, field, replace

from fitinera.assets import Asset
from fitinera.core import Age

from .cashflows import Expense, Income, IncomeKind
from .planning import FinancialScenario
from .results import (
    GrowthApplication,
    IncomeBreakdown,
    SimulationTurn,
)


@dataclass()
class TurnState:
    """Holds the mutable state of a simulation turn."""

    current_age: Age
    assets: dict[str, Asset] = field(default_factory=dict)
    incomes: dict[str, Income] = field(default_factory=dict)
    expenses: dict[str, Expense] = field(default_factory=dict)

    def __init__(self, scenario: FinancialScenario):
        self.current_age = copy.deepcopy(scenario.time_horizon.current_age)
        self.assets = {a.name: copy.deepcopy(a) for a in scenario.assets.values()}
        self.incomes = {i.name: copy.deepcopy(i) for i in scenario.incomes.values()}
        self.expenses = {e.name: copy.deepcopy(e) for e in scenario.expenses.values()}


class TurnHandler:
    """Represents a single turn in a financial simulation."""

    def __init__(self):
        pass

    def run(
        self,
        scenario: FinancialScenario,
        turn_state: TurnState,
    ) -> SimulationTurn:
        """
        Runs the logic for a single turn of the simulation.
        """
        # Store current state for the turn
        current_asset_breakdown = {
            asset.name: asset.initial_value for asset in turn_state.assets.values()
        }
        current_income_breakdown = IncomeBreakdown()
        for income in turn_state.incomes.values():
            if income.time_bounds.is_active(turn_state.current_age):
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
        for tax_rate in scenario.tax_rates:
            if tax_rate.time_bounds.is_active(turn_state.current_age):
                active_tax_rate = tax_rate
                tax_amount = gross_income * tax_rate.rate
                tax_breakdown[f"Income Tax ({tax_rate.rate:.2%})"] = tax_amount
                net_income -= tax_amount
                break  # Assume only one tax rate is active at a time

        # Aggregate Expenses
        expense_breakdown = defaultdict(float)
        for expense in turn_state.expenses.values():
            if expense.time_bounds.is_active(turn_state.current_age):
                expense_breakdown[expense.name] = expense.monthly_amount
        total_expenses = sum(expense_breakdown.values())

        # Calculate Net Cash Flow
        net_cash_flow = net_income - total_expenses

        # Apply Asset Flows
        total_contributions = 0
        withdrawal_breakdown = defaultdict(float)
        total_penalties = 0
        needed_cash = 0

        if net_cash_flow > 0:
            # Contribute to assets
            sorted_assets = sorted(
                turn_state.assets.values(),
                key=lambda a: a.contribution_priority,
                reverse=True,
            )
            remaining_cash = net_cash_flow
            for asset in sorted_assets:
                if remaining_cash <= 0:
                    break
                contribution = min(
                    remaining_cash, asset.get_max_contribution(turn_state.current_age)
                )
                turn_state.assets[asset.name] = replace(
                    asset, initial_value=asset.initial_value + contribution
                )
                total_contributions += contribution
                remaining_cash -= contribution
        elif net_cash_flow < 0:
            # Withdraw from assets
            sorted_assets = sorted(
                turn_state.assets.values(),
                key=lambda a: a.withdrawal_priority,
                reverse=True,
            )
            needed_cash = abs(net_cash_flow)
            for i, asset in enumerate(sorted_assets):
                if needed_cash <= 0:
                    break
                if asset.initial_value <= 0 and i < len(sorted_assets) - 1:
                    continue  # Skip assets with no value unless it's the last one.

                new_asset = copy.deepcopy(asset)
                # Compute how much we can withdraw from this asset
                net_withdrawal = (
                    min(needed_cash, asset.initial_value)
                    if i < len(sorted_assets) - 1
                    else needed_cash  # Withdraw whatever is needed from the last asset
                )
                gross_withdrawal = net_withdrawal

                # Apply penalties and taxes on withdrawal. Assume penalties apply before taxes.
                penalty = new_asset.get_penalty(turn_state.current_age)
                if penalty:
                    penalty_amount = net_withdrawal * penalty.rate
                    gross_withdrawal += penalty_amount
                    needed_cash += penalty_amount  # Need to cover the penalty too!
                    net_cash_flow -= (
                        penalty_amount  # This reduces our net cash flow for the turn.
                    )
                    total_penalties += penalty_amount

                tax_rate = (
                    new_asset.get_override_tax_rate(turn_state.current_age)
                    or active_tax_rate
                )
                if tax_rate:
                    tax_amount = net_withdrawal * tax_rate.rate
                    gross_withdrawal += tax_amount
                    needed_cash += tax_amount  # Need to cover the tax too!
                    net_cash_flow -= (
                        tax_amount  # This reduces our net cash flow for the turn.
                    )
                    tax_breakdown[
                        f"Withdrawal Tax ({tax_rate.rate:.2%}) on {asset.name}"
                    ] += tax_amount

                # Apply withdrawal
                actual_withdrawal = (
                    gross_withdrawal
                    if i == len(sorted_assets) - 1
                    else min(gross_withdrawal, asset.initial_value)
                )
                new_asset = replace(
                    asset, initial_value=asset.initial_value - actual_withdrawal
                )
                turn_state.assets[asset.name] = new_asset
                withdrawal_breakdown[asset.name] += actual_withdrawal
                needed_cash -= (
                    actual_withdrawal  # This reduces the cash we still need to cover
                )

        # Compound Values
        asset_growth_breakdown = []
        for asset in turn_state.assets.values():
            rate = asset.growth_strategy.get_monthly_growth_rate(
                turn_state.current_age.month
            )
            growth = asset.initial_value * rate
            turn_state.assets[asset.name] = replace(
                asset, initial_value=asset.initial_value + growth
            )
            asset_growth_breakdown.append(
                GrowthApplication(
                    name=asset.name,
                    rate=rate,
                    amount=growth,
                )
            )

        income_growth_breakdown = []
        for income in turn_state.incomes.values():
            rate = income.growth_strategy.get_monthly_growth_rate(
                turn_state.current_age.month
            )
            growth = income.monthly_amount * rate
            turn_state.incomes[income.name] = replace(
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
        for expense in turn_state.expenses.values():
            rate = expense.growth_strategy.get_monthly_growth_rate(
                turn_state.current_age.month
            )
            growth = expense.monthly_amount * rate
            turn_state.expenses[expense.name] = replace(
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
            asset.name: asset.initial_value for asset in turn_state.assets.values()
        }
        next_income_breakdown = IncomeBreakdown()
        for income in turn_state.incomes.values():
            if income.time_bounds.is_active(turn_state.current_age.next_month()):
                if income.kind == IncomeKind.ACTIVE:
                    next_income_breakdown.active[income.name] = income.monthly_amount
                else:
                    next_income_breakdown.passive[income.name] = income.monthly_amount

        return SimulationTurn(
            current_age=turn_state.current_age,
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
