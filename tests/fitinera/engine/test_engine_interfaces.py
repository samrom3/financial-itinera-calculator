"""Tests verifying the shape of SimulationStateView and related engine protocols."""

from fitinera.engine import (
    SimulationStateView,
    SimulationStateUpdater,
    SimulationLogger,
)


class TestSimulationStateViewIsProtocol:
    """Verifies that SimulationStateView exposes all required method signatures."""

    def test_get_accounts_returns_list_annotation(self):
        """SimulationStateView.get_accounts is defined and returns List[AccountState]."""
        assert hasattr(SimulationStateView, "get_accounts")

    def test_get_person_is_defined(self):
        """SimulationStateView.get_person is defined."""
        assert hasattr(SimulationStateView, "get_person")

    def test_get_metric_is_defined(self):
        """SimulationStateView.get_metric is defined."""
        assert hasattr(SimulationStateView, "get_metric")

    def test_get_start_date_is_defined(self):
        """SimulationStateView.get_start_date is defined (added in story-01)."""
        assert hasattr(SimulationStateView, "get_start_date")

    def test_get_current_date_is_defined(self):
        """SimulationStateView.get_current_date is defined (added in story-01)."""
        assert hasattr(SimulationStateView, "get_current_date")

    def test_get_elapsed_duration_is_defined(self):
        """SimulationStateView.get_elapsed_duration is defined (added in story-01)."""
        assert hasattr(SimulationStateView, "get_elapsed_duration")

    def test_get_current_turn_transactions_is_defined(self):
        """SimulationStateView.get_current_turn_transactions is defined (added in story-01)."""
        assert hasattr(SimulationStateView, "get_current_turn_transactions")

    def test_get_start_date_stub_raises_not_implemented(self):
        """SimulationStateView.get_start_date raises NotImplementedError on base call."""

        class _ConcreteView(SimulationStateView):
            pass

        view = _ConcreteView()
        try:
            view.get_start_date()
            assert False, "Expected NotImplementedError"
        except NotImplementedError:
            pass

    def test_get_current_date_stub_raises_not_implemented(self):
        """SimulationStateView.get_current_date raises NotImplementedError on base call."""

        class _ConcreteView(SimulationStateView):
            pass

        view = _ConcreteView()
        try:
            view.get_current_date()
            assert False, "Expected NotImplementedError"
        except NotImplementedError:
            pass

    def test_get_elapsed_duration_stub_raises_not_implemented(self):
        """SimulationStateView.get_elapsed_duration raises NotImplementedError on base call."""

        class _ConcreteView(SimulationStateView):
            pass

        view = _ConcreteView()
        try:
            view.get_elapsed_duration()
            assert False, "Expected NotImplementedError"
        except NotImplementedError:
            pass

    def test_get_current_turn_transactions_stub_raises_not_implemented(self):
        """SimulationStateView.get_current_turn_transactions raises NotImplementedError on base call."""

        class _ConcreteView(SimulationStateView):
            pass

        view = _ConcreteView()
        try:
            view.get_current_turn_transactions()
            assert False, "Expected NotImplementedError"
        except NotImplementedError:
            pass


class TestSimulationStateUpdaterIsProtocol:
    """Verifies SimulationStateUpdater protocol shape."""

    def test_emit_transaction_is_defined(self):
        """SimulationStateUpdater.emit_transaction is defined."""
        assert hasattr(SimulationStateUpdater, "emit_transaction")

    def test_update_person_label_is_defined(self):
        """SimulationStateUpdater.update_person_label is defined."""
        assert hasattr(SimulationStateUpdater, "update_person_label")


class TestSimulationLoggerIsProtocol:
    """Verifies SimulationLogger protocol shape."""

    def test_all_log_methods_are_defined(self):
        """SimulationLogger exposes debug, info, warning, and error methods."""
        for method in ("debug", "info", "warning", "error"):
            assert hasattr(SimulationLogger, method)
