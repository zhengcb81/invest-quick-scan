"""Compatibility entry for iqs_scan.execution.shared_company_task."""
import sys

from iqs_scan.execution import shared_company_task as _implementation

sys.modules[__name__] = _implementation
