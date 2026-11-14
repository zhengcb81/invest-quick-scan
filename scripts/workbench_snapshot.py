"""Compatibility entry for iqs_scan.workbench.workbench_snapshot."""
import sys

from iqs_scan.workbench import workbench_snapshot as _implementation

sys.modules[__name__] = _implementation
