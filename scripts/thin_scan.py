"""Compatibility entry for iqs_scan.execution.thin_scan."""
import sys

from iqs_scan.execution import thin_scan as _implementation

if __name__ == '__main__':
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
