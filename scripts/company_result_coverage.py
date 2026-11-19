"""Compatibility entry for iqs_scan.workbench.company_result_coverage."""
import sys

from iqs_scan.workbench import company_result_coverage as _implementation

sys.modules[__name__] = _implementation
