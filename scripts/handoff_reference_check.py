"""Compatibility entry for iqs_scan.acceptance.handoff_reference_check."""
import sys

from iqs_scan.acceptance import handoff_reference_check as _implementation

sys.modules[__name__] = _implementation
