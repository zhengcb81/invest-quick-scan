"""Compatibility entry for iqs_scan.workbench.dashboard_json."""
import sys

from iqs_scan.workbench import dashboard_json as _implementation

sys.modules[__name__] = _implementation
