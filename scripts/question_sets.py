"""Compatibility entry for iqs_scan.questions.question_sets."""
import sys

from iqs_scan.questions import question_sets as _implementation

if __name__ == '__main__':
    _implementation.main()
else:
    sys.modules[__name__] = _implementation
