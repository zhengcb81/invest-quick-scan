"""Compatibility entry for iqs_scan.questions.question_bank."""
import sys

from iqs_scan.questions import question_bank as _implementation

sys.modules[__name__] = _implementation
