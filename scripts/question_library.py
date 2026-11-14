"""Compatibility entry for iqs_scan.questions.question_library."""
import sys

from iqs_scan.questions import question_library as _implementation

sys.modules[__name__] = _implementation
