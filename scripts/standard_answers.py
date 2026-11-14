"""Compatibility entry for iqs_scan.answers.standard_answers."""
import sys

from iqs_scan.answers import standard_answers as _implementation

if __name__ == '__main__':
    _implementation.main()
else:
    sys.modules[__name__] = _implementation
