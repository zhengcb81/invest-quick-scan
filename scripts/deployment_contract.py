"""Compatibility entry for iqs_scan.tools.deployment_contract."""
import sys

from iqs_scan.tools import deployment_contract as _implementation

sys.modules[__name__] = _implementation
