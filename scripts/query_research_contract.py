"""Compatibility entry for iqs_scan.query.query_research_contract."""
import sys

from iqs_scan.query import query_research_contract as _implementation

sys.modules[__name__] = _implementation
