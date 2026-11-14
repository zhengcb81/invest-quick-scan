"""Compatibility entry for iqs_scan.workbench.dashboard_temporal."""
import sys

from iqs_scan.workbench import dashboard_temporal as _implementation

sys.modules[__name__] = _implementation
