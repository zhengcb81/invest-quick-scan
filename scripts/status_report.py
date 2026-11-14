"""Compatibility entry for iqs_scan.tools.status_report."""
import sys

from iqs_scan.tools import status_report as _implementation

if __name__ == '__main__':
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
