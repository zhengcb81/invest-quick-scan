"""Compatibility entry for iqs_scan.workbench.dashboard_iqs_link."""
import sys

from iqs_scan.workbench import dashboard_iqs_link as _implementation

sys.modules[__name__] = _implementation
