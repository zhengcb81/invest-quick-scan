"""Compatibility entry for iqs_scan.questions.question_prompts."""
import sys

from iqs_scan.questions import question_prompts as _implementation

sys.modules[__name__] = _implementation
