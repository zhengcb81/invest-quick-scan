"""Compatibility entry for iqs_scan.query.query_field_assessment."""
import sys

from iqs_scan.query import query_field_assessment as _implementation

sys.modules[__name__] = _implementation
