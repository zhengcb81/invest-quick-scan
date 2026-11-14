"""Compatibility entry for iqs_scan.query.query_contract."""
import sys

from iqs_scan.query import query_contract as _implementation

sys.modules[__name__] = _implementation
