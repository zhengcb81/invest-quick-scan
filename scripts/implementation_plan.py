"""Compatibility entry for iqs_scan.tools.implementation_plan."""
import sys

from iqs_scan.tools import implementation_plan as _implementation

if __name__ == '__main__':
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
