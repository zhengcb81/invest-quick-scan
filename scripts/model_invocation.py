"""Compatibility entry for iqs_scan.providers.model_invocation."""
import sys

from iqs_scan.providers import model_invocation as _implementation

sys.modules[__name__] = _implementation
