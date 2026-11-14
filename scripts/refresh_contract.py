"""Compatibility entry for iqs_scan.query.refresh_contract."""
import sys

from iqs_scan.query import refresh_contract as _implementation

sys.modules[__name__] = _implementation
