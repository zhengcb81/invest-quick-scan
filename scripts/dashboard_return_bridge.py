"""Compatibility entry for iqs_scan.workbench.dashboard_return_bridge."""
import sys

from iqs_scan.workbench import dashboard_return_bridge as _implementation

sys.modules[__name__] = _implementation
