"""Compatibility module for the workbench clock policy."""
import sys

from iqs_scan.workbench.iqs_temporal_vendor import errors as _implementation

sys.modules[__name__] = _implementation
