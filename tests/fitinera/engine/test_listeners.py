"""Tests for LogListener protocol and built-in listener implementations.

Verifies:
- ListLogListener.messages is initially empty on construction.
- ListLogListener appends ``[LEVEL] msg`` strings in chronological order.
- Separate ListLogListener instances maintain independent messages lists.
- PythonLoggingListener can be instantiated without error.
- PythonLoggingListener delegates each call to ``logging.getLogger("fitinera.engine")``
  at the correct Python logging level.
"""

import logging


from fitinera import ListLogListener, PythonLoggingListener
from fitinera.engine import LogListener


class TestLogListenerProtocol:
    """Verifies that LogListener protocol exposes required method signatures."""

    def test_all_log_methods_are_defined_on_protocol(self):
        """LogListener exposes debug, info, warning, and error methods."""
        for method in ("debug", "info", "warning", "error"):
            assert hasattr(LogListener, method)


class TestListLogListenerConstruction:
    """Verifies ListLogListener initialisation behaviour."""

    def test_messages_list_is_empty_on_construction(self):
        """ListLogListener.messages is an empty list immediately after construction."""
        listener = ListLogListener()
        assert listener.messages == []

    def test_messages_is_a_list_type(self):
        """ListLogListener.messages is a list (not None, not another collection)."""
        listener = ListLogListener()
        assert isinstance(listener.messages, list)

    def test_two_instances_have_independent_messages_lists(self):
        """Separate ListLogListener instances do not share the same messages list."""
        a = ListLogListener()
        b = ListLogListener()
        assert a.messages is not b.messages


class TestListLogListenerDebug:
    """Verifies ListLogListener.debug appends the correct prefixed message."""

    def test_debug_appends_prefixed_message(self):
        """debug(msg) appends '[DEBUG] msg' to self.messages."""
        listener = ListLogListener()
        listener.debug("hello debug")
        assert listener.messages == ["[DEBUG] hello debug"]

    def test_debug_multiple_calls_are_in_order(self):
        """Multiple debug calls append in chronological order."""
        listener = ListLogListener()
        listener.debug("first")
        listener.debug("second")
        assert listener.messages == ["[DEBUG] first", "[DEBUG] second"]


class TestListLogListenerInfo:
    """Verifies ListLogListener.info appends the correct prefixed message."""

    def test_info_appends_prefixed_message(self):
        """info(msg) appends '[INFO] msg' to self.messages."""
        listener = ListLogListener()
        listener.info("hello info")
        assert listener.messages == ["[INFO] hello info"]


class TestListLogListenerWarning:
    """Verifies ListLogListener.warning appends the correct prefixed message."""

    def test_warning_appends_prefixed_message(self):
        """warning(msg) appends '[WARNING] msg' to self.messages."""
        listener = ListLogListener()
        listener.warning("hello warning")
        assert listener.messages == ["[WARNING] hello warning"]


class TestListLogListenerError:
    """Verifies ListLogListener.error appends the correct prefixed message."""

    def test_error_appends_prefixed_message(self):
        """error(msg) appends '[ERROR] msg' to self.messages."""
        listener = ListLogListener()
        listener.error("hello error")
        assert listener.messages == ["[ERROR] hello error"]


class TestListLogListenerChronologicalOrder:
    """Verifies ListLogListener accumulates mixed-level messages in order."""

    def test_mixed_level_messages_are_in_chronological_order(self):
        """debug, info, warning, error calls are appended in call order."""
        listener = ListLogListener()
        listener.debug("d")
        listener.info("i")
        listener.warning("w")
        listener.error("e")
        assert listener.messages == [
            "[DEBUG] d",
            "[INFO] i",
            "[WARNING] w",
            "[ERROR] e",
        ]

    def test_independent_instances_do_not_share_state(self):
        """Messages logged to one ListLogListener do not appear in another."""
        a = ListLogListener()
        b = ListLogListener()
        a.info("only in a")
        b.warning("only in b")
        assert a.messages == ["[INFO] only in a"]
        assert b.messages == ["[WARNING] only in b"]


class TestPythonLoggingListenerConstruction:
    """Verifies PythonLoggingListener can be instantiated."""

    def test_python_logging_listener_can_be_instantiated(self):
        """PythonLoggingListener constructs without raising an exception."""
        listener = PythonLoggingListener()
        assert listener is not None


class TestPythonLoggingListenerDelegation:
    """Verifies PythonLoggingListener delegates to the correct logger at the correct level."""

    def test_debug_delegates_to_python_logger(self, caplog):
        """debug(msg) calls logging.getLogger('fitinera.engine').debug(msg)."""
        listener = PythonLoggingListener()
        with caplog.at_level(logging.DEBUG, logger="fitinera.engine"):
            listener.debug("debug message")
        assert any(
            r.levelno == logging.DEBUG and r.message == "debug message"
            for r in caplog.records
        )

    def test_info_delegates_to_python_logger(self, caplog):
        """info(msg) calls logging.getLogger('fitinera.engine').info(msg)."""
        listener = PythonLoggingListener()
        with caplog.at_level(logging.INFO, logger="fitinera.engine"):
            listener.info("info message")
        assert any(
            r.levelno == logging.INFO and r.message == "info message"
            for r in caplog.records
        )

    def test_warning_delegates_to_python_logger(self, caplog):
        """warning(msg) calls logging.getLogger('fitinera.engine').warning(msg)."""
        listener = PythonLoggingListener()
        with caplog.at_level(logging.WARNING, logger="fitinera.engine"):
            listener.warning("warning message")
        assert any(
            r.levelno == logging.WARNING and r.message == "warning message"
            for r in caplog.records
        )

    def test_error_delegates_to_python_logger(self, caplog):
        """error(msg) calls logging.getLogger('fitinera.engine').error(msg)."""
        listener = PythonLoggingListener()
        with caplog.at_level(logging.ERROR, logger="fitinera.engine"):
            listener.error("error message")
        assert any(
            r.levelno == logging.ERROR and r.message == "error message"
            for r in caplog.records
        )

    def test_debug_uses_fitinera_engine_logger(self, caplog):
        """PythonLoggingListener routes to the 'fitinera.engine' logger specifically."""
        listener = PythonLoggingListener()
        with caplog.at_level(logging.DEBUG, logger="fitinera.engine"):
            listener.debug("check logger name")
        assert any(r.name == "fitinera.engine" for r in caplog.records)
