"""Compatibility entry for iqs_scan.foundation.exchange_contract."""
import sys

from iqs_scan.foundation import exchange_contract as _implementation

sys.modules[__name__] = _implementation
