"""Compatibility entry for iqs_scan.workbench.dashboard_locks."""
import sys

from iqs_scan.workbench import dashboard_locks as _implementation

sys.modules[__name__] = _implementation
