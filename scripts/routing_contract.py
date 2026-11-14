"""Compatibility entry for iqs_scan.questions.routing_contract."""
import sys

from iqs_scan.questions import routing_contract as _implementation

sys.modules[__name__] = _implementation
