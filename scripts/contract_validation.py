"""Compatibility entry for iqs_scan.foundation.contract_validation."""
import sys

from iqs_scan.foundation import contract_validation as _implementation

sys.modules[__name__] = _implementation
