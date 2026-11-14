"""Compatibility entry for iqs_scan.query.subject_dispatch_contract."""
import sys

from iqs_scan.query import subject_dispatch_contract as _implementation

sys.modules[__name__] = _implementation
