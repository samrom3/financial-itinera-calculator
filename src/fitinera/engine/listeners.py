"""Built-in LogListener implementations for fitinera.

This module provides two standard listeners that satisfy the LogListener
protocol:

- ``ListLogListener``: accumulates ``[LEVEL] msg`` strings in ``self.messages``
  for in-process inspection and testing.
- ``PythonLoggingListener``: delegates each call to
  ``logging.getLogger("fitinera.engine")`` at the corresponding level.
"""

import logging
from typing import List

_ENGINE_LOGGER = logging.getLogger("fitinera.engine")


class ListLogListener:
    """Accumulates log messages in-memory for inspection and testing.

    Each call to a log method appends a ``[LEVEL] msg`` string to
    ``self.messages`` in chronological order.

    Attributes:
        messages: Ordered list of log message strings in ``[LEVEL] msg`` format.

    Note:
        This implementation is not thread-safe.
    """

    def __init__(self) -> None:
        """Initialises the listener with an empty messages list."""
        self.messages: List[str] = []

    def debug(self, msg: str) -> None:
        """Appends a DEBUG-level message to self.messages.

        Args:
            msg: The message string to record.
        """
        self.messages.append(f"[DEBUG] {msg}")

    def info(self, msg: str) -> None:
        """Appends an INFO-level message to self.messages.

        Args:
            msg: The message string to record.
        """
        self.messages.append(f"[INFO] {msg}")

    def warning(self, msg: str) -> None:
        """Appends a WARNING-level message to self.messages.

        Args:
            msg: The message string to record.
        """
        self.messages.append(f"[WARNING] {msg}")

    def error(self, msg: str) -> None:
        """Appends an ERROR-level message to self.messages.

        Args:
            msg: The message string to record.
        """
        self.messages.append(f"[ERROR] {msg}")


class PythonLoggingListener:
    """Delegates log messages to the Python standard ``logging`` module.

    All messages are routed to ``logging.getLogger("fitinera.engine")`` at
    the level corresponding to the method called (DEBUG, INFO, WARNING, ERROR).

    Note:
        This implementation is not thread-safe beyond what ``logging`` itself
        guarantees.
    """

    def debug(self, msg: str) -> None:
        """Delegates to logging.getLogger("fitinera.engine").debug(msg).

        Args:
            msg: The message string to log.
        """
        _ENGINE_LOGGER.debug(msg)

    def info(self, msg: str) -> None:
        """Delegates to logging.getLogger("fitinera.engine").info(msg).

        Args:
            msg: The message string to log.
        """
        _ENGINE_LOGGER.info(msg)

    def warning(self, msg: str) -> None:
        """Delegates to logging.getLogger("fitinera.engine").warning(msg).

        Args:
            msg: The message string to log.
        """
        _ENGINE_LOGGER.warning(msg)

    def error(self, msg: str) -> None:
        """Delegates to logging.getLogger("fitinera.engine").error(msg).

        Args:
            msg: The message string to log.
        """
        _ENGINE_LOGGER.error(msg)
