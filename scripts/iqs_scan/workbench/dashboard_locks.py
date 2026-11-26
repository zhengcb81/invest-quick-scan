"""Compatibility imports for the workbench's shared native file lock."""

from ..foundation.api import ControlBusyError, control_lock

__all__ = ["ControlBusyError", "control_lock"]
