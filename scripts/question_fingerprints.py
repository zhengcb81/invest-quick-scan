"""Compatibility entry for iqs_scan.questions.question_fingerprints."""
import sys

from iqs_scan.questions import question_fingerprints as _implementation

sys.modules[__name__] = _implementation
