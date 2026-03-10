"""Tests for _SimulationLoggerImpl dispatch behaviour.

Verifies:
- _SimulationLoggerImpl accepts a list of LogListener instances.
- Each log method dispatches to every listener in registration order.
- An empty listeners list makes each call a no-op.
- If any listener raises during dispatch, the exception propagates immediately.
- _SimulationLoggerImpl does not accumulate messages itself (no .messages property).
- _SimulationLoggerImpl does not set an error flag (no .has_error property).
"""

import pytest

from fitinera import ListLogListener
from fitinera.engine.state import _SimulationLoggerImpl


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _RaisingListener:
    """A LogListener stub that raises RuntimeError on every call."""

    def debug(self, msg: str) -> None:
        raise RuntimeError(f"debug raised: {msg}")

    def info(self, msg: str) -> None:
        raise RuntimeError(f"info raised: {msg}")

    def warning(self, msg: str) -> None:
        raise RuntimeError(f"warning raised: {msg}")

    def error(self, msg: str) -> None:
        raise RuntimeError(f"error raised: {msg}")


class _RecordingListener:
    """A LogListener stub that records all calls in order."""

    def __init__(self, name: str):
        self.name = name
        self.calls: list[tuple[str, str]] = []

    def debug(self, msg: str) -> None:
        self.calls.append(("debug", msg))

    def info(self, msg: str) -> None:
        self.calls.append(("info", msg))

    def warning(self, msg: str) -> None:
        self.calls.append(("warning", msg))

    def error(self, msg: str) -> None:
        self.calls.append(("error", msg))


# ---------------------------------------------------------------------------
# TestSimulationLoggerImplConstruction
# ---------------------------------------------------------------------------


class TestSimulationLoggerImplConstruction:
    """Verifies _SimulationLoggerImpl construction with a listeners list."""

    def test_accepts_empty_listeners_list(self):
        """_SimulationLoggerImpl constructs without error when given an empty list."""
        logger = _SimulationLoggerImpl(listeners=[])
        assert logger is not None

    def test_accepts_single_listener(self):
        """_SimulationLoggerImpl constructs with a single ListLogListener."""
        listener = ListLogListener()
        logger = _SimulationLoggerImpl(listeners=[listener])
        assert logger is not None

    def test_accepts_multiple_listeners(self):
        """_SimulationLoggerImpl constructs with multiple listeners."""
        a = ListLogListener()
        b = ListLogListener()
        logger = _SimulationLoggerImpl(listeners=[a, b])
        assert logger is not None

    def test_has_no_has_error_attribute(self):
        """_SimulationLoggerImpl does not expose a has_error property."""
        logger = _SimulationLoggerImpl(listeners=[])
        assert not hasattr(logger, "has_error")

    def test_has_no_error_message_attribute(self):
        """_SimulationLoggerImpl does not expose an error_message property."""
        logger = _SimulationLoggerImpl(listeners=[])
        assert not hasattr(logger, "error_message")

    def test_has_no_messages_attribute(self):
        """_SimulationLoggerImpl does not expose a messages property."""
        logger = _SimulationLoggerImpl(listeners=[])
        assert not hasattr(logger, "messages")


# ---------------------------------------------------------------------------
# TestSimulationLoggerImplEmptyListeners
# ---------------------------------------------------------------------------


class TestSimulationLoggerImplEmptyListeners:
    """Verifies that calling log methods with an empty listeners list is a no-op."""

    def test_debug_with_no_listeners_does_not_raise(self):
        """debug() with an empty listeners list completes without raising."""
        logger = _SimulationLoggerImpl(listeners=[])
        logger.debug("test")  # should not raise

    def test_info_with_no_listeners_does_not_raise(self):
        """info() with an empty listeners list completes without raising."""
        logger = _SimulationLoggerImpl(listeners=[])
        logger.info("test")

    def test_warning_with_no_listeners_does_not_raise(self):
        """warning() with an empty listeners list completes without raising."""
        logger = _SimulationLoggerImpl(listeners=[])
        logger.warning("test")

    def test_error_with_no_listeners_does_not_raise(self):
        """error() with an empty listeners list completes without raising."""
        logger = _SimulationLoggerImpl(listeners=[])
        logger.error("test")


# ---------------------------------------------------------------------------
# TestSimulationLoggerImplDispatch
# ---------------------------------------------------------------------------


class TestSimulationLoggerImplDispatch:
    """Verifies that log calls are dispatched to each registered listener."""

    def test_debug_dispatches_to_single_listener(self):
        """debug(msg) calls listener.debug(msg) on the single registered listener."""
        listener = ListLogListener()
        logger = _SimulationLoggerImpl(listeners=[listener])
        logger.debug("hello debug")
        assert listener.messages == ["[DEBUG] hello debug"]

    def test_info_dispatches_to_single_listener(self):
        """info(msg) calls listener.info(msg) on the single registered listener."""
        listener = ListLogListener()
        logger = _SimulationLoggerImpl(listeners=[listener])
        logger.info("hello info")
        assert listener.messages == ["[INFO] hello info"]

    def test_warning_dispatches_to_single_listener(self):
        """warning(msg) calls listener.warning(msg) on the single registered listener."""
        listener = ListLogListener()
        logger = _SimulationLoggerImpl(listeners=[listener])
        logger.warning("hello warning")
        assert listener.messages == ["[WARNING] hello warning"]

    def test_error_dispatches_to_single_listener(self):
        """error(msg) calls listener.error(msg) on the single registered listener."""
        listener = ListLogListener()
        logger = _SimulationLoggerImpl(listeners=[listener])
        logger.error("hello error")
        assert listener.messages == ["[ERROR] hello error"]

    def test_debug_dispatches_to_all_listeners(self):
        """debug(msg) is dispatched to every listener in the list."""
        a = ListLogListener()
        b = ListLogListener()
        logger = _SimulationLoggerImpl(listeners=[a, b])
        logger.debug("broadcast")
        assert a.messages == ["[DEBUG] broadcast"]
        assert b.messages == ["[DEBUG] broadcast"]

    def test_info_dispatches_to_all_listeners(self):
        """info(msg) is dispatched to every listener in the list."""
        a = ListLogListener()
        b = ListLogListener()
        logger = _SimulationLoggerImpl(listeners=[a, b])
        logger.info("broadcast")
        assert a.messages == ["[INFO] broadcast"]
        assert b.messages == ["[INFO] broadcast"]

    def test_warning_dispatches_to_all_listeners(self):
        """warning(msg) is dispatched to every listener in the list."""
        a = ListLogListener()
        b = ListLogListener()
        logger = _SimulationLoggerImpl(listeners=[a, b])
        logger.warning("broadcast")
        assert a.messages == ["[WARNING] broadcast"]
        assert b.messages == ["[WARNING] broadcast"]

    def test_error_dispatches_to_all_listeners(self):
        """error(msg) is dispatched to every listener in the list."""
        a = ListLogListener()
        b = ListLogListener()
        logger = _SimulationLoggerImpl(listeners=[a, b])
        logger.error("broadcast")
        assert a.messages == ["[ERROR] broadcast"]
        assert b.messages == ["[ERROR] broadcast"]


# ---------------------------------------------------------------------------
# TestSimulationLoggerImplDispatchOrder
# ---------------------------------------------------------------------------


class TestSimulationLoggerImplDispatchOrder:
    """Verifies that listeners are called in registration order."""

    def test_listeners_called_in_registration_order_for_debug(self):
        """Listeners receive debug calls in the order they were registered."""
        call_order: list[str] = []

        class _OrderedListener:
            def __init__(self, name: str) -> None:
                self.name = name

            def debug(self, msg: str) -> None:
                call_order.append(self.name)

            def info(self, msg: str) -> None:
                call_order.append(self.name)

            def warning(self, msg: str) -> None:
                call_order.append(self.name)

            def error(self, msg: str) -> None:
                call_order.append(self.name)

        first = _OrderedListener("first")
        second = _OrderedListener("second")
        third = _OrderedListener("third")
        logger = _SimulationLoggerImpl(listeners=[first, second, third])
        logger.debug("ordering test")
        assert call_order == ["first", "second", "third"]

    def test_listeners_called_in_registration_order_for_error(self):
        """Listeners receive error calls in the order they were registered."""
        a = _RecordingListener("a")
        b = _RecordingListener("b")
        logger = _SimulationLoggerImpl(listeners=[a, b])
        logger.error("ordering test")
        assert a.calls == [("error", "ordering test")]
        assert b.calls == [("error", "ordering test")]
        # a should be called before b; verify both received the call
        assert len(a.calls) == 1
        assert len(b.calls) == 1

    def test_multiple_calls_accumulate_in_listener_order(self):
        """Mixed level calls accumulate correctly across multiple listeners."""
        a = ListLogListener()
        b = ListLogListener()
        logger = _SimulationLoggerImpl(listeners=[a, b])
        logger.info("first")
        logger.warning("second")
        logger.error("third")
        assert a.messages == ["[INFO] first", "[WARNING] second", "[ERROR] third"]
        assert b.messages == ["[INFO] first", "[WARNING] second", "[ERROR] third"]


# ---------------------------------------------------------------------------
# TestSimulationLoggerImplListenerFailurePropagation
# ---------------------------------------------------------------------------


class TestSimulationLoggerImplListenerFailurePropagation:
    """Verifies that a listener exception propagates immediately from _SimulationLoggerImpl."""

    def test_debug_propagates_listener_exception(self):
        """RuntimeError raised by listener.debug() propagates out of logger.debug()."""
        logger = _SimulationLoggerImpl(listeners=[_RaisingListener()])
        with pytest.raises(RuntimeError, match="debug raised"):
            logger.debug("trigger")

    def test_info_propagates_listener_exception(self):
        """RuntimeError raised by listener.info() propagates out of logger.info()."""
        logger = _SimulationLoggerImpl(listeners=[_RaisingListener()])
        with pytest.raises(RuntimeError, match="info raised"):
            logger.info("trigger")

    def test_warning_propagates_listener_exception(self):
        """RuntimeError raised by listener.warning() propagates out of logger.warning()."""
        logger = _SimulationLoggerImpl(listeners=[_RaisingListener()])
        with pytest.raises(RuntimeError, match="warning raised"):
            logger.warning("trigger")

    def test_error_propagates_listener_exception(self):
        """RuntimeError raised by listener.error() propagates out of logger.error()."""
        logger = _SimulationLoggerImpl(listeners=[_RaisingListener()])
        with pytest.raises(RuntimeError, match="error raised"):
            logger.error("trigger")

    def test_first_listener_exception_stops_dispatch(self):
        """When the first listener raises, the second listener is NOT called."""
        second = ListLogListener()
        logger = _SimulationLoggerImpl(listeners=[_RaisingListener(), second])
        with pytest.raises(RuntimeError):
            logger.info("stop here")
        # Second listener should not have been called
        assert second.messages == []
