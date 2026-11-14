"""Compatibility entry for iqs_scan.foundation.observation_profiles."""
import sys

from iqs_scan.foundation import observation_profiles as _implementation

sys.modules[__name__] = _implementation
