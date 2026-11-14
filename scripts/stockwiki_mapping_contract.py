"""Compatibility entry for iqs_scan.acceptance.stockwiki_mapping_contract."""
import sys

from iqs_scan.acceptance import stockwiki_mapping_contract as _implementation

sys.modules[__name__] = _implementation
