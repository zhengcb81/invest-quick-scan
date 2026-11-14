"""Compatibility entry for iqs_scan.workbench.dashboard_service."""
import sys

from iqs_scan.workbench import dashboard_service as _implementation

sys.modules[__name__] = _implementation
