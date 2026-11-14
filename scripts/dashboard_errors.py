"""Compatibility entry for iqs_scan.workbench.dashboard_errors."""
import sys

from iqs_scan.workbench import dashboard_errors as _implementation

sys.modules[__name__] = _implementation
