"""Compatibility entry for iqs_scan.questions.stockqa_adapter."""
import sys

from iqs_scan.questions import stockqa_adapter as _implementation

sys.modules[__name__] = _implementation
