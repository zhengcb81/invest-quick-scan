"""Compatibility entry for iqs_scan.workbench.dashboard_company_projection."""
import sys

from iqs_scan.workbench import dashboard_company_projection as _implementation

sys.modules[__name__] = _implementation
