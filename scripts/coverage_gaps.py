"""Compatibility entry for iqs_scan.tools.coverage_gaps."""
import sys

from iqs_scan.tools import coverage_gaps as _implementation

if __name__ == '__main__':
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
