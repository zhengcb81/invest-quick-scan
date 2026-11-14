"""Compatibility entry for iqs_scan.questions.question_selection."""
import sys

from iqs_scan.questions import question_selection as _implementation

sys.modules[__name__] = _implementation
