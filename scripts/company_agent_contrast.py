"""Compatibility entry for iqs_scan.experiments.company_agent_contrast."""
import sys

from iqs_scan.experiments import company_agent_contrast as _implementation

sys.modules[__name__] = _implementation
