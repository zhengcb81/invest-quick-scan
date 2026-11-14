"""Compatibility entry for iqs_scan.providers.model_config."""
import sys

from iqs_scan.providers import model_config as _implementation

sys.modules[__name__] = _implementation
