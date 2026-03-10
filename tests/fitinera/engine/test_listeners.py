"""Tests for LogListener protocol and built-in listener stubs.

Verifies:
- ListLogListener.messages is initially empty on construction.
- PythonLoggingListener can be instantiated without error.
- All four stub methods (debug, info, warning, error) raise NotImplementedError,
  confirming stubs-only status before implementation story-02.
"""

import pytest

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


class TestListLogListenerStubs:
    """Verifies ListLogListener stub methods raise NotImplementedError.

    These tests are EXPECTED TO FAIL after story-02 (implementation). Until then
    they confirm the scaffold is stubs-only.
    """

    def test_debug_raises_not_implemented(self):
        """ListLogListener.debug raises NotImplementedError (stub)."""
        listener = ListLogListener()
        with pytest.raises(NotImplementedError):
            listener.debug("test message")

    def test_info_raises_not_implemented(self):
        """ListLogListener.info raises NotImplementedError (stub)."""
        listener = ListLogListener()
        with pytest.raises(NotImplementedError):
            listener.info("test message")

    def test_warning_raises_not_implemented(self):
        """ListLogListener.warning raises NotImplementedError (stub)."""
        listener = ListLogListener()
        with pytest.raises(NotImplementedError):
            listener.warning("test message")

    def test_error_raises_not_implemented(self):
        """ListLogListener.error raises NotImplementedError (stub)."""
        listener = ListLogListener()
        with pytest.raises(NotImplementedError):
            listener.error("test message")


class TestPythonLoggingListenerConstruction:
    """Verifies PythonLoggingListener can be instantiated."""

    def test_python_logging_listener_can_be_instantiated(self):
        """PythonLoggingListener constructs without raising an exception."""
        listener = PythonLoggingListener()
        assert listener is not None


class TestPythonLoggingListenerStubs:
    """Verifies PythonLoggingListener stub methods raise NotImplementedError.

    These tests are EXPECTED TO FAIL after story-02 (implementation). Until then
    they confirm the scaffold is stubs-only.
    """

    def test_debug_raises_not_implemented(self):
        """PythonLoggingListener.debug raises NotImplementedError (stub)."""
        listener = PythonLoggingListener()
        with pytest.raises(NotImplementedError):
            listener.debug("test message")

    def test_info_raises_not_implemented(self):
        """PythonLoggingListener.info raises NotImplementedError (stub)."""
        listener = PythonLoggingListener()
        with pytest.raises(NotImplementedError):
            listener.info("test message")

    def test_warning_raises_not_implemented(self):
        """PythonLoggingListener.warning raises NotImplementedError (stub)."""
        listener = PythonLoggingListener()
        with pytest.raises(NotImplementedError):
            listener.warning("test message")

    def test_error_raises_not_implemented(self):
        """PythonLoggingListener.error raises NotImplementedError (stub)."""
        listener = PythonLoggingListener()
        with pytest.raises(NotImplementedError):
            listener.error("test message")
