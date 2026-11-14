"""Compatibility entry for iqs_scan.workbench.dashboard_jobs."""
import sys

from iqs_scan.workbench import dashboard_jobs as _implementation

sys.modules[__name__] = _implementation
