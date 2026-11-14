"""Compatibility entry for iqs_scan.foundation.work_contract."""
import sys

from iqs_scan.foundation import work_contract as _implementation

sys.modules[__name__] = _implementation
