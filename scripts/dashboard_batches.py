"""Compatibility entry for iqs_scan.workbench.dashboard_batches."""
import sys

from iqs_scan.workbench import dashboard_batches as _implementation

sys.modules[__name__] = _implementation
