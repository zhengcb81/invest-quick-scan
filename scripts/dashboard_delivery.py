"""Compatibility entry for iqs_scan.workbench.dashboard_delivery."""
import sys

from iqs_scan.workbench import dashboard_delivery as _implementation

sys.modules[__name__] = _implementation
