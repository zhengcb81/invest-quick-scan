"""Compatibility entry for iqs_scan.tools.company_result_feedback."""
import sys

from iqs_scan.tools import company_result_feedback as _implementation

if __name__ == '__main__':
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
