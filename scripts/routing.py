"""Compatibility entry for iqs_scan.questions.routing."""
import sys

from iqs_scan.questions import routing as _implementation

sys.modules[__name__] = _implementation
