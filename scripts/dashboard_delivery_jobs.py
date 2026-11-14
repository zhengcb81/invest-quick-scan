"""Compatibility entry for iqs_scan.workbench.dashboard_delivery_jobs."""
import sys

from iqs_scan.workbench import dashboard_delivery_jobs as _implementation

sys.modules[__name__] = _implementation
