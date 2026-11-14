"""Compatibility entry for iqs_scan.workbench.dashboard_membership_request."""
import sys

from iqs_scan.workbench import dashboard_membership_request as _implementation

sys.modules[__name__] = _implementation
