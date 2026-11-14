"""Compatibility entry for iqs_scan.workbench.dashboard_job_facade."""
import sys

from iqs_scan.workbench import dashboard_job_facade as _implementation

sys.modules[__name__] = _implementation
