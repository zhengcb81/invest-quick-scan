"""Compatibility entry for iqs_scan.tools.roster_status."""
import sys

from iqs_scan.tools import roster_status as _implementation

if __name__ == '__main__':
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
