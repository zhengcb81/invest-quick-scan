"""Compatibility entry for iqs_scan.experiments.accuracy_assessment."""
import sys

from iqs_scan.experiments import accuracy_assessment as _implementation

sys.modules[__name__] = _implementation
