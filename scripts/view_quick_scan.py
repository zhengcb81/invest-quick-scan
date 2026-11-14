"""Compatibility entry for iqs_scan.workbench.view_quick_scan."""
import sys

from iqs_scan.workbench import view_quick_scan as _implementation

if __name__ == '__main__':
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
