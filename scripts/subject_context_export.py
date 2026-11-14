"""Compatibility entry for iqs_scan.query.subject_context_export."""
import sys

from iqs_scan.query import subject_context_export as _implementation

sys.modules[__name__] = _implementation
