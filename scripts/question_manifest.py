"""Compatibility entry for iqs_scan.questions.question_manifest."""
import sys

from iqs_scan.questions import question_manifest as _implementation

sys.modules[__name__] = _implementation
