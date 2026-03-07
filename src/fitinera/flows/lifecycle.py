from typing import List

from .interfaces import Flow
from .conditions import Condition
from ..engine.interfaces import (
    SimulationStateView,
    SimulationStateUpdater,
    SimulationLogger,
)


class PersonRetirementLabelFlow(Flow):
    """Transitions persons to a retired label when a condition is satisfied.

    Args:
        person_ids: Identifiers of the persons to monitor.
        condition: Predicate evaluated each turn to determine retirement.
        status_facet: Label facet to update when retiring. Defaults to 'Status'.
        retired_value: Label value to apply when retiring. Defaults to 'Retired'.
    """

    def __init__(
        self,
        person_ids: List[str],
        condition: Condition,
        status_facet: str = "Status",
        retired_value: str = "Retired",
    ):
        self.person_ids = person_ids
        self.condition = condition
        self.status_facet = status_facet
        self.retired_value = retired_value

    def executeFlow(
        self,
        view: SimulationStateView,
        updater: SimulationStateUpdater,
        logger: SimulationLogger,
    ) -> None:
        """Update retirement labels for all monitored persons when condition is satisfied."""
        if self.condition.evaluate(view):
            for pid in self.person_ids:
                updater.update_person_label(pid, self.status_facet, self.retired_value)
                logger.info(
                    f"PersonRetirementLabelFlow: applied '{self.retired_value}' "
                    f"to person '{pid}' on facet '{self.status_facet}'"
                )


class ConditionalLabelFlow(Flow):
    """Applies a label to a person when a condition is satisfied.

    Args:
        condition: Predicate evaluated each turn to determine if the label applies.
        person_id: Identifier of the person to label.
        facet: Label facet to update when the condition is satisfied.
        value: Label value to apply when the condition is satisfied.
    """

    def __init__(
        self,
        condition: Condition,
        person_id: str,
        facet: str,
        value: str,
    ):
        self.condition = condition
        self.person_id = person_id
        self.facet = facet
        self.value = value

    def executeFlow(
        self,
        view: SimulationStateView,
        updater: SimulationStateUpdater,
        logger: SimulationLogger,
    ) -> None:
        """Apply label to person when condition is satisfied."""
        if self.condition.evaluate(view):
            updater.update_person_label(self.person_id, self.facet, self.value)
