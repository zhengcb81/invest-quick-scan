"""Compatibility entry for iqs_scan.query.query_pool_scope_contract."""
import sys

from iqs_scan.query import query_pool_scope_contract as _implementation

sys.modules[__name__] = _implementation
