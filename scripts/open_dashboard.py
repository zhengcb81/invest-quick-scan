"""Compatibility entry for iqs_scan.workbench.open_dashboard."""
import sys

from iqs_scan.workbench import open_dashboard as _implementation

if __name__ == '__main__':
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
