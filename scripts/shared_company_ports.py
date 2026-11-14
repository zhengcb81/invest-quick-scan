"""Compatibility entry for iqs_scan.execution.shared_company_ports."""
import sys

from iqs_scan.execution import shared_company_ports as _implementation

sys.modules[__name__] = _implementation
