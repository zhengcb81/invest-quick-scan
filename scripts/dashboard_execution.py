"""Compatibility entry for iqs_scan.workbench.dashboard_execution."""
import sys

from iqs_scan.workbench import dashboard_execution as _implementation

sys.modules[__name__] = _implementation
