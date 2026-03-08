from .interfaces import Flow
from ..engine.interfaces import (
    SimulationStateView,
    SimulationStateUpdater,
    SimulationLogger,
)
from ..models.transaction import Income


class JobIncomeFlow(Flow):
    """Injects regular employment income for a person each turn they are actively working."""

    def __init__(self, person_id: str, amount: float, to_account: str):
        self.person_id = person_id
        self.amount = amount
        self.to_account = to_account

    def executeFlow(
        self,
        view: SimulationStateView,
        updater: SimulationStateUpdater,
        logger: SimulationLogger,
    ) -> None:
        """Emit income if person is living and has Status == 'Working'; log otherwise."""
        person = view.get_person(self.person_id)
        if (
            person is not None
            and person.living()
            and person.get_label("Status") == "Working"
        ):
            updater.emit_transaction(
                Income(amount=self.amount, to_account=self.to_account)
            )
        else:
            logger.info(
                f"JobIncomeFlow: skipping income for person '{self.person_id}' "
                "(not living or not working)"
            )
