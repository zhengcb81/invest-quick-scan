"""Compatibility imports for the workbench's shared native file lock."""

from ..foundation.file_lock import ControlBusyError, control_lock

__all__ = ["ControlBusyError", "control_lock"]
