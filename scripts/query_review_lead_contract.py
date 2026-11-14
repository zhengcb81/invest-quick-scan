"""Compatibility entry for iqs_scan.query.query_review_lead_contract."""
import sys

from iqs_scan.query import query_review_lead_contract as _implementation

sys.modules[__name__] = _implementation
