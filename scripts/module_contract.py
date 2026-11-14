"""Compatibility entry for iqs_scan.foundation.module_contract."""
import sys

from iqs_scan.foundation import module_contract as _implementation

sys.modules[__name__] = _implementation
